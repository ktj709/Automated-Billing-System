import pandas as pd
import json
import os

INPUT_FILE = r"e:\Machine Learning Projects\Billing\data\Electrcity details for Software.xlsx"
OUTPUT_FILE = r"e:\Machine Learning Projects\Billing\data\meter_registry.json"
SHEET_NAME = "Flats "  # Note the space at the end based on previous inspection

def import_registry():
    print(f"Reading {INPUT_FILE}...")
    
    try:
        # Step 1: Find the header row
        # Read first 20 rows to find header
        df_temp = pd.read_csv(INPUT_FILE) if INPUT_FILE.endswith('.csv') else pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=None, nrows=20)
        
        header_row_index = None
        for i, row in df_temp.iterrows():
            row_values = [str(val).strip() for val in row.values]
            if 'Flat no' in row_values:
                header_row_index = i
                break
        
        if header_row_index is None:
            print("Error: Could not find header row with 'Flat no'")
            return
            
        print(f"Found header at row {header_row_index}")
        
        # Step 2: Read the actual data
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=header_row_index)

        # Try to locate the maintenance/fixed charges column in a flexible way
        maint_col = None
        for col in df.columns:
            col_str = str(col).strip().lower().replace("\n", " ")
            if "maintenance" in col_str and "fixed" in col_str and "charge" in col_str:
                maint_col = col
                break
        
        # Step 3: Filter and Clean
        registry = []
        
        for _, row in df.iterrows():
            # Skip empty rows or rows without Flat no
            if pd.isna(row.get('Flat no')):
                continue
                
            flat_no = str(row.get('Flat no')).strip()
            
            # Skip if flat_no is empty or looks like a header repetition
            if not flat_no or flat_no.lower() == 'flat no':
                continue
                
            # Extract fields
            entry = {
                "flat_no": flat_no,
                "floor": str(row.get('Floor', '')).strip(),
                "type": str(row.get('Type', '')).strip(),
                "client_name": str(row.get('Client Name', '')).strip(),
                "meter_id": str(row.get('Meter No.', '')).strip().replace('.0', ''), # Remove decimal if any
                "fixed_charge": row.get(maint_col, 0) if maint_col is not None else 0
            }
            
            # Handle NaN/None
            if pd.isna(entry['fixed_charge']):
                entry['fixed_charge'] = 0
            
            # Basic validation
            if entry['meter_id'] and entry['meter_id'].lower() != 'nan':
                registry.append(entry)
        
        print(f"Extracted {len(registry)} valid entries.")
        
        # Step 4: Save to JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
            
        print(f"Saved registry to {OUTPUT_FILE}")
        
        # Show sample
        if registry:
            print("\nSample entry:")
            print(json.dumps(registry[0], indent=2))
            
    except Exception as e:
        print(f"Error importing registry: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_registry()
