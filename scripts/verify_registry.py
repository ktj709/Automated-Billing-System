from services.database_service import DatabaseService
import json
import os

def test_registry_loading():
    print("Testing registry loading...")
    db = DatabaseService()
    
    registry = db.get_meter_registry()
    print(f"Loaded {len(registry)} meters.")
    
    if len(registry) > 0:
        print("First meter:", registry[0])
        print("SUCCESS: Registry loaded.")
    else:
        print("FAILURE: Registry empty.")

    # Check file existence
    registry_path = os.path.join(os.path.dirname(__file__), 'data', 'meter_registry.json')
    print(f"Checking path: {registry_path}")
    print(f"Exists: {os.path.exists(registry_path)}")

if __name__ == "__main__":
    test_registry_loading()
