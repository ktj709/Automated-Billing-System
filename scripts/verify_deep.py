import pandas as pd
import json
import sys

excel_path = "d:\\Machine Learning Projects\\Billing\\data\\Bills_Summary_November2025.xlsx"
json_path = "d:\\Machine Learning Projects\\Billing\\data\\db_bills_nov.json"

def normalize_float(val):
    try:
        if pd.isna(val): return 0.0
        return float(val)
    except:
        return 0.0

try:
    # 1. Load Excel
    # Confirmed header is at index 2 (Row 3)
    df_excel = pd.read_excel(excel_path, header=2)
    
    # Filter valid rows
    if 'Flat Code' not in df_excel.columns:
        print(f"CRITICAL: 'Flat Code' column not found. Columns: {list(df_excel.columns)}")
        sys.exit(1)
        
    df_excel = df_excel[df_excel['Flat Code'].notna()]
    
    # Identify discrepancies
    issues = []
    
    # 2. Load JSON
    with open(json_path, 'r') as f:
        db_data = json.load(f)
    
    # Create DB lookups
    db_map = {item['flat_no'].strip(): item for item in db_data}
    
    print(f"Loaded {len(df_excel)} Excel records and {len(db_map)} DB records.")

    # 3. Iterate and Compare
    print(f"{'Flat No':<10} | {'Col':<15} | {'Excel':<10} | {'DB':<10} | {'Diff':<10}")
    print("-" * 65)
    
    match_count = 0
    mismatch_count = 0
    
    # Explicit Column Mapping
    col_map = {
        'total_amount': 'Final Bill',
        'flat_units': 'Flat Units',
        'motor_units': 'Motor Share',
        'total_units': 'Total Units' # Also check this
    }

    for index, row in df_excel.iterrows():
        flat_no = str(row['Flat Code']).strip()
        
        # Debug: Print first matched record details
        if match_count == 0 and flat_no in db_map:
             print(f"DEBUG CHECK: Matching {flat_no}")
             print(f"Excel Amt: {row[col_map['total_amount']]}, DB Amt: {db_map[flat_no]['total_amount']}")

        
        if flat_no not in db_map:
            if "total" in flat_no.lower(): continue
            print(f"{flat_no:<10} | {'MISSING IN DB':<15} | {'YES':<10} | {'NO':<10} | {'N/A':<10}")
            mismatch_count += 1
            continue
            
        db_record = db_map[flat_no]
        
        # Check Total Amount
        excel_amt = normalize_float(row[col_map['total_amount']])
        db_amt = normalize_float(db_record['total_amount'])
        
        # Exact comparison or very tight tolerance? 
        # Excel seems to have cents, DB seems rounded to int or 00 cents.
        # User said "mistakes are unaffordable", so I will flag ANY difference > 0.01
        
        if abs(excel_amt - db_amt) > 0.01:
            print(f"{flat_no:<10} | {'Total Amount':<15} | {excel_amt:<10.2f} | {db_amt:<10.2f} | {excel_amt-db_amt:<10.2f}")
            mismatch_count += 1
        
        # Check Flat Units
        excel_units = normalize_float(row[col_map['flat_units']])
        db_units = normalize_float(db_record['flat_units'])
        if abs(excel_units - db_units) > 0.01:
            print(f"{flat_no:<10} | {'Flat Units':<15} | {excel_units:<10.2f} | {db_units:<10.2f} | {excel_units-db_units:<10.2f}")
            mismatch_count += 1
                
        # Check Motor Units
        excel_units = normalize_float(row[col_map['motor_units']])
        db_units = normalize_float(db_record['motor_units'])
        if abs(excel_units - db_units) > 0.01:
            print(f"{flat_no:<10} | {'Motor Units':<15} | {excel_units:<10.2f} | {db_units:<10.2f} | {excel_units-db_units:<10.2f}")
            mismatch_count += 1

        match_count += 1

    print("-" * 65)
    print(f"Verified {match_count} records.")
    print(f"Found {mismatch_count} discrepancies.")
    
    if len(db_map) > len(df_excel):
        print(f"WARNING: DB has {len(db_map)} records, Excel has {len(df_excel)}. {(len(db_map) - len(df_excel))} records in DB are not in Excel.")

except Exception as e:
    print(f"Comparison Error: {e}")
