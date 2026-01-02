import pandas as pd
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_FILE = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
OUTPUT_FILE = r"e:\Machine Learning Projects\Billing\data\meter_registry.json"
SHEET_NAME = "Master Data"

def import_billing_system():
    """Import data from Electricity_Billing_System.xlsx to meter_registry.json"""
    print(f"Reading {INPUT_FILE}...")
    print(f"Sheet: {SHEET_NAME}")
    
    try:
        # Read Excel file (skip first row which is title, use second row as header)
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=1)
        
        print(f"\nColumns found: {df.columns.tolist()}")
        print(f"Total rows: {len(df)}")
        
        # Build registry with new structure
        registry = []
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.iloc[0]):  # Check first column
                continue
            
            # Extract data (columns are at indices 0-6 based on inspection)
            # Index 0: Unit_ID
            # Index 1: (skip - just index number)
            # Index 2: Flat_no
            # Index 3: Floor  
            # Index 4: Type
            # Index 5: Client_Name
            # Index 6: Meter_ID
            # Index 7: Fixed_Charge (skip as per user request)
            
            try:
                unit_id = str(row.iloc[0]).strip()
                flat_no = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else ""
                floor = str(row.iloc[3]).strip() if not pd.isna(row.iloc[3]) else ""
                unit_type = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else ""
                client_name = str(row.iloc[5]).strip() if not pd.isna(row.iloc[5]) else ""
                meter_id = str(row.iloc[6]).strip().replace('.0', '') if not pd.isna(row.iloc[6]) else ""
                
                # Skip invalid entries
                if not unit_id or unit_id == 'nan' or 'Unit_ID' in unit_id:
                    continue
                
                entry = {
                    "unit_id": unit_id,
                    "flat_no": flat_no,
                    "floor": floor,
                    "type": unit_type,
                    "client_name": client_name,
                    "meter_id": meter_id
                }
                
                registry.append(entry)
                
            except Exception as e:
                print(f"Warning: Skipping row {idx}: {e}")
                continue
        
        print(f"\nExtracted {len(registry)} valid entries")
        
        # Save to JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved registry to {OUTPUT_FILE}")
        
        # Show sample
        if registry:
            print("\nSample entries:")
            for i, entry in enumerate(registry[:3], 1):
                print(f"\n{i}. Unit ID: {entry['unit_id']}")
                print(f"   Flat: {entry['flat_no']}, Floor: {entry['floor']}, Type: {entry['type']}")
                print(f"   Client: {entry['client_name']}")
                print(f"   Meter ID: {entry['meter_id']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error importing data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_billing_system()
    sys.exit(0 if success else 1)
