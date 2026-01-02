import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService

n = Neo4jService()

if not n.is_connected():
    print("Not connected to Neo4j")
else:
    session = n.driver.session()
    
    # Query sample customers
    print("\n" + "=" * 80)
    print("SAMPLE CUSTOMERS IN NEO4J DATABASE")
    print("=" * 80)
    
    result = session.run('''
        MATCH (c:Customer) 
        RETURN c.name as name, c.flat_no as flat, c.floor as floor, 
               c.type as type, c.fixed_charge as charge 
        LIMIT 10
    ''')
    
    for record in result:
        name = record['name'] or 'N/A'
        flat = record['flat'] or 'N/A'
        floor = record['floor'] or 'N/A'
        ftype = record['type'] or 'N/A'
        charge = record['charge'] if record['charge'] is not None else 0
        print(f"Name: {name:45} | Flat: {flat:5} | Floor: {floor:3} | Type: {ftype:5} | Charge: ₹{charge}")
    
    # Query sample meters
    print("\n" + "=" * 80)
    print("SAMPLE METERS IN NEO4J DATABASE")
    print("=" * 80)
    
    result = session.run('''
        MATCH (m:Meter) 
        RETURN m.id as meter_id, m.flat_no as flat, m.floor as floor, 
               m.type as type, m.fixed_charge as charge 
        LIMIT 10
    ''')
    
    for record in result:
        meter_id = record['meter_id'] or 'N/A'
        flat = record['flat'] or 'N/A'
        floor = record['floor'] or 'N/A'
        ftype = record['type'] or 'N/A'
        charge = record['charge'] if record['charge'] is not None else 0
        print(f"Meter ID: {meter_id:10} | Flat: {flat:5} | Floor: {floor:3} | Type: {ftype:5} | Charge: ₹{charge}")
    
    session.close()
    n.close()
    print("\n" + "=" * 80)
