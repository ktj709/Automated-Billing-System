from typing import List, Dict
from config import Config
import logging

logger = logging.getLogger(__name__)

# Import neo4j only if available (optional dependency)
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False


class Neo4jService:
    """Neo4j service for managing tariff rules and relationships"""
    
    def __init__(self):
        self.connection_error = None
        
        if not HAS_NEO4J:
            self.driver = None
            self.connection_error = "Neo4j driver not installed"
            return
        
        if not Config.NEO4J_PASSWORD:
            self.driver = None
            self.connection_error = "NEO4J_PASSWORD not set in .env file"
            return
        
        try:
            self.driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            # Neo4j not available - set driver to None
            self.driver = None
            self.connection_error = str(e)
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
    def is_connected(self) -> bool:
        """Check if Neo4j is connected"""
        if not self.driver:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False
    
    def get_active_tariffs(self) -> List[Dict]:
        """Retrieve all active tariff rules"""
        if not self.driver:
            return []
        
        query = """
        MATCH (t:Tariff) 
        WHERE t.active = true 
        RETURN t
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            tariffs = []
            for record in result:
                tariff_node = record['t']
                tariffs.append(dict(tariff_node))
            return tariffs
    
    def create_bill_relationship(self, bill_data: Dict) -> Dict:
        """Create bill node and relationships in Neo4j"""
        if not self.driver:
            return {}
        
        query = """
        MATCH (c:Customer {id: $customer_id}), (m:Meter {id: $meter_id})
        CREATE (b:Bill {
            id: $bill_id,
            amount: $amount,
            consumption: $consumption,
            date: $date,
            status: 'pending'
        })
        CREATE (c)-[:HAS_BILL]->(b)
        CREATE (m)-[:GENERATED_BILL]->(b)
        RETURN b
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                customer_id=bill_data['customer_id'],
                meter_id=bill_data['meter_id'],
                bill_id=bill_data['bill_id'],
                amount=bill_data['amount'],
                consumption=bill_data['consumption'],
                date=bill_data['date']
            )
            record = result.single()
            if record:
                return dict(record['b'])
            return {}
    
    def get_customer_billing_history(self, customer_id: str) -> List[Dict]:
        """Get billing history for a customer"""
        if not self.driver:
            return []
        
        query = """
        MATCH (c:Customer {id: $customer_id})-[:HAS_BILL]->(b:Bill)
        RETURN b
        ORDER BY b.date DESC
        LIMIT 12
        """
        
        with self.driver.session() as session:
            result = session.run(query, customer_id=customer_id)
            bills = []
            for record in result:
                bills.append(dict(record['b']))
            return bills
    
    def update_bill_status(self, bill_id: int, status: str) -> Dict:
        """Update bill status in Neo4j"""
        if not self.driver:
            return {}
        
        query = """
        MATCH (b:Bill {id: $bill_id})
        SET b.status = $status, b.updated_at = datetime()
        RETURN b
        """
        
        with self.driver.session() as session:
            result = session.run(query, bill_id=bill_id, status=status)
            record = result.single()
            if record:
                return dict(record['b'])
            return {}
    
    def sync_bills_from_supabase(self, bills: List[Dict]) -> Dict:
        """
        Sync bills from Supabase to Neo4j - EXACT MATCH
        1. CLEARS all existing bills
        2. Creates all bills from Supabase fresh
        Result: Neo4j will have EXACTLY the same bills as Supabase
        """
        if not self.driver:
            return {"error": "Neo4j driver not available", "synced": 0}
        
        synced_count = 0
        deleted_count = 0
        errors = []
        
        try:
            with self.driver.session() as session:
                # Step 1: Clear ALL existing bills from Neo4j
                delete_result = session.run("""
                    MATCH (b:Bill)
                    WITH b, b.id as bill_id
                    DETACH DELETE b
                    RETURN count(bill_id) as deleted
                """)
                
                delete_record = delete_result.single()
                deleted_count = delete_record['deleted'] if delete_record else 0
                
                # Step 3: Sync all bills from Supabase (overwrite existing, add new)
                for bill in bills:
                    try:
                        # Ensure Customer node exists
                        session.run("""
                            MERGE (c:Customer {id: $customer_id})
                            ON CREATE SET c.created_at = datetime()
                            ON MATCH SET c.updated_at = datetime()
                        """, customer_id=bill.get('customer_id'))
                        
                        # Ensure Meter node exists
                        session.run("""
                            MERGE (m:Meter {id: $meter_id})
                            ON CREATE SET m.created_at = datetime()
                            ON MATCH SET m.updated_at = datetime()
                        """, meter_id=bill.get('meter_id'))
                        
                        # MERGE Bill node (overwrites if exists, creates if new)
                        session.run("""
                            MERGE (b:Bill {id: $bill_id})
                            SET b.amount = $amount,
                                b.consumption_kwh = $consumption,
                                b.status = $status,
                                b.billing_period_start = $period_start,
                                b.billing_period_end = $period_end,
                                b.created_at = $created_at,
                                b.updated_at = datetime()
                        """, 
                            bill_id=bill.get('id'),
                            amount=float(bill.get('amount', 0)),
                            consumption=float(bill.get('consumption_kwh', 0)),
                            status=bill.get('status', 'pending'),
                            period_start=bill.get('billing_period_start'),
                            period_end=bill.get('billing_period_end'),
                            created_at=bill.get('created_at')
                        )
                        
                        # Create relationships (MERGE ensures no duplicates)
                        session.run("""
                            MATCH (c:Customer {id: $customer_id})
                            MATCH (b:Bill {id: $bill_id})
                            MERGE (c)-[:HAS_BILL]->(b)
                        """, customer_id=bill.get('customer_id'), bill_id=bill.get('id'))
                        
                        session.run("""
                            MATCH (m:Meter {id: $meter_id})
                            MATCH (b:Bill {id: $bill_id})
                            MERGE (m)-[:GENERATED_BILL]->(b)
                        """, meter_id=bill.get('meter_id'), bill_id=bill.get('id'))
                        
                        synced_count += 1
                        
                    except Exception as e:
                        errors.append(f"Bill {bill.get('id')}: {str(e)}")
                        continue
            
            return {
                "success": True,
                "synced": synced_count,
                "deleted": deleted_count,
                "total": len(bills),
                "errors": errors if errors else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "synced": synced_count,
                "deleted": deleted_count
            }
    
    def clear_all_bills(self) -> Dict:
        """Clear all bill nodes and relationships from Neo4j"""
        if not self.driver:
            return {"error": "Neo4j driver not available"}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (b:Bill)
                    DETACH DELETE b
                    RETURN count(b) as deleted_count
                """)
                record = result.single()
                return {
                    "success": True,
                    "deleted": record['deleted_count'] if record else 0
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the graph"""
        if not self.driver:
            return {"error": "Neo4j driver not available"}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Customer) WITH count(c) as customers
                    MATCH (m:Meter) WITH customers, count(m) as meters
                    MATCH (b:Bill) WITH customers, meters, count(b) as bills
                    MATCH (b2:Bill {status: 'paid'}) WITH customers, meters, bills, count(b2) as paid_bills
                    MATCH (b3:Bill {status: 'pending'}) WITH customers, meters, bills, paid_bills, count(b3) as pending_bills
                    RETURN customers, meters, bills, paid_bills, pending_bills
                """)
                record = result.single()
                if record:
                    return dict(record)
                return {}
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_bills(self) -> List[Dict]:
        """Get all bills from Neo4j"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Customer)-[:HAS_BILL]->(b:Bill)<-[:GENERATED_BILL]-(m:Meter)
                    RETURN b.id as bill_id, 
                           c.id as customer_id,
                           m.id as meter_id,
                           b.amount as amount,
                           b.consumption_kwh as consumption_kwh,
                           b.status as status,
                           b.billing_period_start as billing_period_start,
                           b.billing_period_end as billing_period_end,
                           b.created_at as created_at
                    ORDER BY b.created_at DESC
                """)
                
                bills = []
                for record in result:
                    bills.append(dict(record))
                return bills
        except Exception as e:
            logger.error(f"Error getting bills from Neo4j: {e}")
            return []