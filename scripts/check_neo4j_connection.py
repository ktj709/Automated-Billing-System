import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from config import Config

def test_connection():
    print("Testing Neo4j Connection...")
    print(f"URI: {Config.NEO4J_URI}")
    print(f"User: {Config.NEO4J_USER}")
    
    service = Neo4jService()
    
    if service.is_connected():
        print("\n✅ SUCCESS: Connected to Neo4j successfully!")
        
        # Get some stats to prove it
        try:
            with service.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"Current node count in database: {count}")
        except Exception as e:
            print(f"⚠️ Connected but failed to run query: {e}")
            
    else:
        print("\n❌ FAILED: Could not connect to Neo4j.")
        if service.connection_error:
            print(f"Error details: {service.connection_error}")
        else:
            print("Unknown error (driver is None)")

    service.close()

if __name__ == "__main__":
    test_connection()
