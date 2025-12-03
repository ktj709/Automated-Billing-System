import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from services.database_service import DatabaseService

def import_readings():
    print("Starting import from Blessings_City_Master_Data.xlsx...")
    
    file_path = 'data/Blessings_City_Master_Data.xlsx'
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return

    try:
        # Read Excel
        df = pd.read_excel(file_path)
        print(f"Found {len(df)} rows in Excel file.")
        
        # Initialize DB Service
        db = DatabaseService()
        
        # Step 1: Clear existing readings
        print("Clearing existing meter_readings...")
        if db.use_supabase:
            # Delete all rows (using a not-null filter on a required column usually works to select all)
            db.supabase.table('meter_readings').delete().neq('id', -1).execute()
        else:
            print("❌ Error: Only Supabase supported for this operation.")
            return
            
        print("✅ Existing readings cleared.")
        
        # Step 2: Insert new data
        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Map columns
                # Excel: ['Unit_ID', 'Flat no', 'Floor', 'Client Name', 'Meter No.', ...]
                
                reading_data = {
                    'unit_id': str(row['Unit_ID']),
                    'flat_no': str(row['Flat no']),
                    'floor': str(row['Floor']),
                    'client_name': str(row['Client Name']),
                    'meter_id': str(row['Meter No.']),
                    'customer_id': f"CUST_{str(row['Unit_ID'])}", # Generate customer_id
                    'reading_value': 0, # Default to 0 as no reading in file
                    'reading_date': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'status': 'initial',
                    'unit': 'kWh'
                }
                
                # Insert
                db.supabase.table('meter_readings').insert(reading_data).execute()
                success_count += 1
                
                if success_count % 10 == 0:
                    print(f"Imported {success_count} readings...")
                    
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
        
        print(f"\n✅ Import Complete!")
        print(f"Successfully imported: {success_count}")
        print(f"Errors: {len(errors)}")
        if errors:
            print("First 5 errors:")
            for e in errors[:5]:
                print(e)

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    import_readings()
