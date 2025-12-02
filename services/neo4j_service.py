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

    def sync_readings_from_supabase(self, readings: List[Dict]) -> Dict:
        """
        Sync meter readings from Supabase to Neo4j
        1. CLEARS all existing readings
        2. Creates all readings from Supabase fresh
        """
        if not self.driver:
            return {"error": "Neo4j driver not available", "synced": 0}
        
        synced_count = 0
        deleted_count = 0
        errors = []
        
        try:
            with self.driver.session() as session:
                # Step 1: Clear ALL existing readings from Neo4j
                logger.info("Clearing existing readings from Neo4j...")
                delete_result = session.run("""
                    MATCH (r:Reading)
                    DETACH DELETE r
                    RETURN count(r) as deleted
                """)
                
                delete_record = delete_result.single()
                deleted_count = delete_record['deleted'] if delete_record else 0
                logger.info(f"Deleted {deleted_count} existing readings")
                
                # Step 2: Sync all readings from Supabase
                logger.info(f"Syncing {len(readings)} readings to Neo4j...")
                for reading in readings:
                    try:
                        # Determine how to match the Meter node
                        # Priority 1: Match by unit_id (which is the Meter node ID)
                        # Priority 2: Match by meter_id property
                        
                        unit_id = reading.get('unit_id')
                        meter_id = reading.get('meter_id')
                        
                        if unit_id:
                            # Match by ID (unit_id)
                            match_query = "MATCH (m:Meter {id: $unit_id})"
                            match_params = {'unit_id': unit_id}
                        else:
                            # Match by meter_id property
                            match_query = "MATCH (m:Meter) WHERE m.meter_id = $meter_id"
                            match_params = {'meter_id': meter_id}
                            
                        # Create Reading node and relationship
                        session.run(f"""
                            {match_query}
                            MERGE (r:Reading {{id: $reading_id}})
                            SET r.value = $value,
                                r.date = $date,
                                r.created_at = $created_at,
                                r.unit = $unit,
                                r.meter_id = $meter_id_prop,
                                r.unit_id = $unit_id_prop
                            MERGE (m)-[:HAS_READING]->(r)
                        """, 
                            reading_id=str(reading.get('id')),
                            value=float(reading.get('reading_value', 0)),
                            date=reading.get('reading_date'),
                            created_at=reading.get('created_at'),
                            unit=reading.get('unit', 'kWh'),
                            meter_id_prop=meter_id,
                            unit_id_prop=unit_id,
                            **match_params
                        )
                        
                        synced_count += 1
                        
                    except Exception as e:
                        errors.append(f"Reading {reading.get('id')}: {str(e)}")
                        continue
            
            return {
                "success": True,
                "synced": synced_count,
                "deleted": deleted_count,
                "total": len(readings),
                "errors": errors if errors else None
            }
        
        except Exception as e:
            logger.error(f"Error syncing readings: {e}")
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
    
    def clear_all_data(self) -> Dict:
        """Clear ALL data from Neo4j (nodes and relationships)"""
        if not self.driver:
            return {"error": "Neo4j driver not available"}
        
        try:
            with self.driver.session() as session:
                # Delete all nodes and relationships
                result = session.run("""
                    MATCH (n)
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                """)
                record = result.single()
                return {
                    "success": True,
                    "deleted_nodes": record['deleted_count'] if record else 0
                }
        except Exception as e:
            logger.error(f"Error clearing Neo4j data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_customers_and_meters(self, data: List[Dict]) -> Dict:
        """
        Import customers and meters from Excel data
        Creates Customer nodes, Meter nodes, and OWNS_METER relationships
        NEW SCHEMA: Uses unit_id as primary identifier, includes meter_id, excludes fixed_charge
        """
        if not self.driver:
            return {"error": "Neo4j driver not available", "imported": 0}
        
        customers_created = 0
        meters_created = 0
        relationships_created = 0
        errors = []
        
        try:
            with self.driver.session() as session:
                for entry in data:
                    try:
                        unit_id = entry.get('unit_id')
                        meter_id = entry.get('meter_id')
                        client_name = entry.get('client_name')
                        flat_no = entry.get('flat_no')
                        floor = entry.get('floor')
                        flat_type = entry.get('type')
                        
                        # Skip if essential data is missing
                        if not unit_id or not client_name:
                            continue
                        
                        # Create unique customer ID using unit_id + client_name hash
                        # This handles cases where multiple customers share a unit
                        import hashlib
                        customer_id = f"CUST_{unit_id}_{hashlib.md5(client_name.encode()).hexdigest()[:8]}"
                        
                        # Create/Update Customer node (unit_id is now primary, meter_id is just a property)
                        cust_result = session.run("""
                            MERGE (c:Customer {id: $customer_id})
                            ON CREATE SET c.created_at = datetime()
                            SET c.unit_id = $unit_id,
                                c.name = $name,
                                c.flat_no = $flat_no,
                                c.floor = $floor,
                                c.type = $type,
                                c.meter_id = $meter_id,
                                c.updated_at = datetime()
                            RETURN c
                        """, 
                            customer_id=customer_id,
                            unit_id=unit_id,
                            name=client_name,
                            flat_no=flat_no,
                            floor=floor,
                            type=flat_type,
                            meter_id=meter_id
                        )
                        if cust_result.single():
                            customers_created += 1
                        
                        # Create/Update Meter node (using unit_id as primary key)
                        meter_result = session.run("""
                            MERGE (m:Meter {id: $unit_id})
                            ON CREATE SET m.created_at = datetime()
                            SET m.meter_id = $meter_id,
                                m.flat_no = $flat_no,
                                m.floor = $floor,
                                m.type = $type,
                                m.updated_at = datetime()
                            RETURN m
                        """, 
                            unit_id=unit_id,
                            meter_id=meter_id,
                            flat_no=flat_no,
                            floor=floor,
                            type=flat_type
                        )
                        if meter_result.single():
                            meters_created += 1
                        
                        # Create OWNS_METER relationship
                        rel_result = session.run("""
                            MATCH (c:Customer {id: $customer_id})
                            MATCH (m:Meter {id: $unit_id})
                            MERGE (c)-[r:OWNS_METER]->(m)
                            RETURN r
                        """, customer_id=customer_id, unit_id=unit_id)
                        if rel_result.single():
                            relationships_created += 1
                        
                    except Exception as e:
                        errors.append(f"Entry {entry.get('unit_id', 'unknown')}: {str(e)}")
                        continue
            
            return {
                "success": True,
                "customers_created": customers_created,
                "meters_created": meters_created,
                "relationships_created": relationships_created,
                "total_entries": len(data),
                "errors": errors if errors else None
            }
        
        except Exception as e:
            logger.error(f"Error importing customers and meters: {e}")
            return {
                "success": False,
                "error": str(e),
                "customers_created": customers_created,
                "meters_created": meters_created
            }
    
    def get_all_stats(self) -> Dict:
        """Get comprehensive statistics about all nodes and relationships"""
        if not self.driver:
            return {"error": "Neo4j driver not available"}
        
        try:
            with self.driver.session() as session:
                # Get node counts
                result = session.run("""
                    MATCH (c:Customer) WITH count(c) as customers
                    OPTIONAL MATCH (m:Meter) WITH customers, count(m) as meters
                    OPTIONAL MATCH (r:Reading) WITH customers, meters, count(r) as readings
                    OPTIONAL MATCH (b:Bill) WITH customers, meters, readings, count(b) as bills
                    OPTIONAL MATCH (t:Tariff) WITH customers, meters, readings, bills, count(t) as tariffs
                    RETURN customers, meters, readings, bills, tariffs
                """)
                record = result.single()
                
                # Get relationship counts
                rel_result = session.run("""
                    MATCH ()-[r:OWNS_METER]->() WITH count(r) as owns_meter
                    OPTIONAL MATCH ()-[r2:HAS_READING]->() WITH owns_meter, count(r2) as has_reading
                    OPTIONAL MATCH ()-[r3:HAS_BILL]->() WITH owns_meter, has_reading, count(r3) as has_bill
                    OPTIONAL MATCH ()-[r4:GENERATED_BILL]->() WITH owns_meter, has_reading, has_bill, count(r4) as generated_bill
                    RETURN owns_meter, has_reading, has_bill, generated_bill
                """)
                rel_record = rel_result.single()
                
                stats = {
                    "nodes": {
                        "customers": record['customers'] if record else 0,
                        "meters": record['meters'] if record else 0,
                        "readings": record['readings'] if record else 0,
                        "bills": record['bills'] if record else 0,
                        "tariffs": record['tariffs'] if record else 0
                    },
                    "relationships": {
                        "owns_meter": rel_record['owns_meter'] if rel_record else 0,
                        "has_reading": rel_record['has_reading'] if rel_record else 0,
                        "has_bill": rel_record['has_bill'] if rel_record else 0,
                        "generated_bill": rel_record['generated_bill'] if rel_record else 0
                    }
                }
                
                return stats
        except Exception as e:
            logger.error(f"Error getting stats from Neo4j: {e}")
            return {"error": str(e)}