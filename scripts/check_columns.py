import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

db = DatabaseService()

try:
    # Fetch one reading to check columns
    response = db.supabase.table('meter_readings').select('*').limit(1).execute()
    if response.data:
        print("Columns in meter_readings:", response.data[0].keys())
    else:
        print("No readings found to check columns.")
except Exception as e:
    print(f"Error: {e}")
