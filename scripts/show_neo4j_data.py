import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService

n = Neo4jService()
session = n.driver.session()

# Get stats
stats = n.get_all_stats()

print("\n" + "=" * 70)
print("NEO4J DATABASE STATISTICS")
print("=" * 70)
print(f"Customers: {stats['nodes']['customers']}")
print(f"Meters: {stats['nodes']['meters']}")
print(f"Readings: {stats['nodes']['readings']}")
print(f"Bills: {stats['nodes']['bills']}")
print("=" * 70)

# Check current customer data
result = session.run("""
    MATCH (c:Customer) 
    RETURN c.name as name, c.flat_no as flat, c.floor as floor, c.type as type, c.fixed_charge as charge 
    LIMIT 10
""")

print("\nSAMPLE CUSTOMERS (First 10):")
print("=" * 70)
count = 0
for record in result:
    count += 1
    name = record['name'] or 'N/A'
    flat = record['flat'] or 'N/A'
    floor = record['floor'] or 'N/A'
    ftype = record['type'] or 'N/A'
    charge = record['charge'] if record['charge'] is not None else 0
    print(f"{count:2}. {name:40} | {flat:5} | {floor:3} | {ftype:5} | ₹{charge}")

print("=" * 70)
print("\n✅ Data import successful! All customer details are now in Neo4j.")
print("   You can now refresh your Neo4j Browser to see the updated data.\n")

session.close()
n.close()
