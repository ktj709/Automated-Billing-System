import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

db = DatabaseService()

# Get all readings
readings = db.get_all_readings(limit=1000)

print(f"\nTotal readings in Supabase: {len(readings)}")
print("\nFirst 5 readings with metadata:")
for r in readings[:5]:
    print(f"  - Unit: {r.get('unit_id')}")
    print(f"    Meter: {r.get('meter_id')}")
    print(f"    Client: {r.get('client_name')}")
    print(f"    Reading: {r.get('reading_value')} kWh")
    print(f"    Flat: {r.get('flat_no')} (Floor: {r.get('floor')})")
    print("-" * 40)
