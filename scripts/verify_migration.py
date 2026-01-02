import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def verify_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return False

    print(f"Checking connection to: {url}")

    try:
        supabase: Client = create_client(url, key)
        
        # 1. Test basic connection by fetching meters (or flats if new schema)
        print("\n1. Testing 'meters' table access...")
        try:
            response = supabase.table("meters").select("count", count="exact").execute()
            print(f"✅ Success! Found {response.count} meters.")
        except Exception as e:
            print(f"⚠️ 'meters' table check failed: {e}")
            print("   (This is expected if still on old schema with 'meter_readings' only)")

        # 2. Test 'meter_readings' (Old schema check)
        print("\n2. Testing 'meter_readings' table access (Legacy)...")
        try:
            response = supabase.table("meter_readings").select("count", count="exact").execute()
            print(f"✅ Found {response.count} legacy meter_readings.")
        except Exception as e:
            print(f"ℹ️ 'meter_readings' table not found or inaccessible: {e}")

        # 3. Test 'flats' (New schema check)
        print("\n3. Testing 'flats' table access (New Schema)...")
        try:
            response = supabase.table("flats").select("count", count="exact").execute()
            print(f"✅ Success! Found {response.count} flats.")
        except Exception as e:
            print(f"⚠️ 'flats' table check failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    verify_connection()
