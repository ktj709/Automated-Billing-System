import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

db = DatabaseService()

# Get all readings
readings = db.get_all_readings(limit=1000)

print(f"\nTotal readings in Supabase: {len(readings)}")
print("\nFirst 5 readings:")
for r in readings[:5]:
    print(f"  - Meter: {r.get('meter_id')}, Date: {r.get('reading_date')}, Value: {r.get('reading_value')}")
