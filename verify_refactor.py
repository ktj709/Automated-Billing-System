import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from services.database_service import DatabaseService

def verify_refactor():
    print("--- Starting Verification ---")
    db = DatabaseService()
    
    # 1. Verify Active Meters
    print("\n[1] Testing get_active_meters()...")
    meters = db.get_active_meters()
    print(f"Found {len(meters)} active meters.")
    if meters:
        sample = meters[0]
        print(f"Sample Meter: {sample}")
        if 'floor' in sample and sample['floor']:
            print("✅ Floor field populated correctly.")
        else:
            print("⚠️ Floor field missing or empty.")
    else:
        print("❌ No active meters found.")

    # 2. Verify Reading Insert (Dry Run / Test)
    # We will try to insert a reading for the first meter found
    if meters:
        target_meter = meters[0]
        meter_id = target_meter['meter_id']
        print(f"\n[2] Testing insert_meter_reading() for meter_id {meter_id}...")
        
        reading_data = {
            "meter_id": meter_id,
            "reading_value": 1234.5,
            "reading_date": datetime.now().strftime("%Y-%m-%d"),
            "meter_image_path": "test_image.jpg" # Should be ignored
        }
        
        try:
            # Note: This WILL insert data. 
            # If we want to avoid pollution, we should maybe duplicate code or just warn.
            # User said "create a separate for December", so inserting ONE reading for Dec is probably consistent with "testing" 
            # but ideally we delete it.
            # Since Supabase table 'readings' has an ID, we can delete it after.
            
            result = db.insert_meter_reading(reading_data)
            print(f"✅ inserted reading: {result}")
            inserted_id = result.get('id')
            
            # 3. Verify Unbilled Readings
            print("\n[3] Testing get_unbilled_readings()...")
            unbilled = db.get_unbilled_readings()
            found = any(r['id'] == inserted_id for r in unbilled)
            if found:
                print(f"✅ Newly inserted reading {inserted_id} found in unbilled list.")
            else:
                print(f"⚠️ Newly inserted reading {inserted_id} NOT found in unbilled list (might be delay or logic issue).")
            
            # Cleanup (Optional, but good practice for verification script)
            print(f"\n[Cleanup] Deleting test reading {inserted_id}...")
            db.supabase.table('readings').delete().eq('id', inserted_id).execute()
            print("✅ Test reading deleted.")
            
        except Exception as e:
            print(f"❌ Error inserting/verifying reading: {e}")

    else:
        print("Skipping insert test as no meters found.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_refactor()
