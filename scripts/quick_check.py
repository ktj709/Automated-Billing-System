import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService

n = Neo4jService()
session = n.driver.session()

# Check current customer data
result = session.run("MATCH (c:Customer) RETURN c.name as name, c.flat_no as flat, c.floor as floor LIMIT 10")

print("\nCurrent Customer Data in Neo4j:")
print("=" * 60)
count = 0
for record in result:
    count += 1
    name = record['name']
    flat = record['flat']
    floor = record['floor']
    print(f"{count}. Name: {name}, Flat: {flat}, Floor: {floor}")

if count == 0:
    print("No customers found!")

session.close()
n.close()
