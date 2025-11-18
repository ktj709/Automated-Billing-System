from typing import List, Dict
from config import Config

# Import neo4j only if available (optional dependency)
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False


class Neo4jService:
    """Neo4j service for managing tariff rules and relationships"""
    
    def __init__(self):
        if not HAS_NEO4J:
            self.driver = None
            return
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
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
