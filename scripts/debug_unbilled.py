import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

db = DatabaseService()

print("Checking unbilled readings...")
try:
    unbilled = db.get_unbilled_readings(limit=10)
    print(f"Found {len(unbilled)} unbilled readings")
    for r in unbilled:
        print(f"  - Meter: {r.get('meter_id')}, Date: {r.get('reading_date')}, Value: {r.get('reading_value')}")
        print(f"    Metadata in DB: Unit={r.get('unit_id')}, Flat={r.get('flat_no')}")

    if len(unbilled) == 0:
        print("\nChecking raw readings count...")
        all_readings = db.get_all_readings(limit=10)
        print(f"Total raw readings found: {len(all_readings)}")
        if all_readings:
            print("First raw reading:", all_readings[0])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
