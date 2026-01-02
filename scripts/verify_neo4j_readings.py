import os
import sys
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService

def verify_readings():
    print("--- Verifying Neo4j Readings ---")
    neo = Neo4jService()
    if not neo.is_connected():
        print("Error: Could not connect to Neo4j")
        return

    stats = neo.get_all_stats()
    nodes = stats.get('nodes', {})
    rels = stats.get('relationships', {})
    
    print(f"Readings Node Count: {nodes.get('readings', 0)}")
    print(f"HAS_READING Relationships: {rels.get('has_reading', 0)}")
    
    if nodes.get('readings', 0) > 0:
        print("✅ SUCCESS: Readings found in Neo4j")
        
        print("\n--- Sample Readings Data ---")
        with neo.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer)-[:OWNS_METER]->(m:Meter)-[:HAS_READING]->(r:Reading)
                RETURN c.name as client, m.id as meter_unit, r.value as reading, r.date as date
                LIMIT 5
            """)
            for record in result:
                print(f"Client: {record['client']} | Unit: {record['meter_unit']} | Reading: {record['reading']} kWh | Date: {record['date']}")
    else:
        print("❌ FAILURE: No readings found")

if __name__ == "__main__":
    verify_readings()
