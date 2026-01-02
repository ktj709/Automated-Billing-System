import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.database_service import DatabaseService

def verify_fix():
    print("Verifying get_unbilled_readings fix...")
    db = DatabaseService()
    
    try:
        # Fetch readings using the updated method
        readings = db.get_unbilled_readings(limit=50)
        
        print(f"Fetched {len(readings)} unbilled readings.")
        
        # Check if any reading has value <= 0
        invalid_readings = [r for r in readings if float(r.get('reading_value', 0)) <= 0]
        
        if invalid_readings:
            print(f"❌ FAILED: Found {len(invalid_readings)} readings with value <= 0")
            for r in invalid_readings:
                print(f"  - ID: {r.get('id')}, Value: {r.get('reading_value')}")
        else:
            print("✅ SUCCESS: All fetched readings have value > 0")
            
        # Optional: Print a few valid readings to confirm
        if readings:
            print("\nSample valid readings:")
            for r in readings[:3]:
                print(f"  - ID: {r.get('id')}, Value: {r.get('reading_value')}, Date: {r.get('reading_date')}")
                
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    verify_fix()
