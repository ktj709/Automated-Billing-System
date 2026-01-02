import pandas as pd
import os
import sys
import json
import subprocess

# Add current directory to path to allow imports if needed, though we'll use direct subprocess for SQL if needed 
# or use the existing Supabase setup if available.
# Actually, since we don't have direct DB access libraries installed in the env reliably, 
# I will use the 'supabase' library if available, or generate a JSON dump via the mcp tool?
# No, I can't generate a dump via MCP easily for the whole DB in one go if I want to join tables in Python.
# Better approach:
# 1. Fetch relevant data from Supabase via SQL query using the MCP tool (simulated here by outputting a query to run).
#    Wait, I cannot run MCP tools *inside* this python script.
#    I must run the SQL query using the 'execute_sql' tool from the agent, save it to a JSON file, 
#    and THEN run this script to compare.

# So this script will accept a JSON file path as an argument.

def normalize_float(val):
    try:
        if pd.isna(val): return 0.0
        val = str(val).replace(',', '').strip()
        if val == '-': return 0.0
        return float(val)
    except:
        return 0.0

def normalize_name(name):
    if pd.isna(name): return ""
    return str(name).strip().lower()

def verify_data(excel_path, json_path):
    print(f"Loading Excel: {excel_path}")
    # Header is at index 2 (Row 3)
    df_excel = pd.read_excel(excel_path, header=2)
    
    # Filter valid rows
    if 'Flat Code' not in df_excel.columns:
        print(f"CRITICAL: 'Flat Code' column not found. Columns: {list(df_excel.columns)}")
        return

    df_excel = df_excel[df_excel['Flat Code'].notna()]
    
    print(f"Loading DB Data: {json_path}")
    with open(json_path, 'r') as f:
        db_data = json.load(f)

    # Create DB lookup map
    # We expect DB data to have fields: flat_code, tenant_name, total_amount, flat_units, motor_units
    db_map = {}
    for item in db_data:
        code = item.get('flat_code')
        if code:
            db_map[code.strip()] = item

    print(f"Comparison: {len(df_excel)} Excel records vs {len(db_map)} DB records")
    print("-" * 80)
    print(f"{'Flat':<8} | {'Field':<15} | {'Excel':<20} | {'DB':<20} | {'Diff'}")
    print("-" * 80)

    mismatches = 0
    checked = 0

    # Column Mapping (Excel Col Name -> DB Key)
    # Excel Columns based on report and common sense, verified via earlier scripts implicitly
    # 'Final Bill' -> total_amount
    # 'Flat Units' -> flat_units
    # 'Motor Share' -> motor_units
    # 'Tenant Name' -> tenant_name (need to verify exact excel col name)
    
    # Let's check Excel columns for Name
    name_col = None
    for col in df_excel.columns:
        if 'name' in str(col).lower() or 'client' in str(col).lower() or 'occupant' in str(col).lower():
            name_col = col
            break
            
    if not name_col:
        print("WARNING: Could not identify Client Name column in Excel.")
    
    for _, row in df_excel.iterrows():
        flat_code = str(row['Flat Code']).strip()
        
        # Skip totals rows if any
        if 'total' in flat_code.lower(): continue
        
        if flat_code not in db_map:
            print(f"{flat_code:<8} | {'MISSING':<15} | {'-':<20} | {'-':<20} | Full Record Missing")
            mismatches += 1
            continue

        db_rec = db_map[flat_code]
        checked += 1

        # 1. Total Amount
        val_excel = normalize_float(row.get('Final Bill', 0))
        val_db = normalize_float(db_rec.get('total_amount', 0))
        if abs(val_excel - val_db) > 1.0: # Allow small rounding diffs
            print(f"{flat_code:<8} | {'Amount':<15} | {val_excel:<20} | {val_db:<20} | {val_excel - val_db:.2f}")
            mismatches += 1

        # 2. Client Name
        if name_col:
            name_excel = normalize_name(row.get(name_col))
            name_db = normalize_name(db_rec.get('tenant_name'))
            
            # Simple fuzzy match or exact? Start with exact normalized
            if name_excel != name_db:
                # Check for "vacant" or nulls
                if not name_excel and not name_db: continue
                
                # If one is subset of another?
                if name_excel in name_db or name_db in name_excel:
                     pass # Acceptable substring match
                else:
                    print(f"{flat_code:<8} | {'Client Name':<15} | {row.get(name_col):<20} | {db_rec.get('tenant_name'):<20} | Mismatch")
                    mismatches += 1

    print("-" * 80)
    print(f"Checked {checked} records. Found {mismatches} discrepancies.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_live_data.py <excel_file> <json_db_dump>")
        sys.exit(1)
        
    verify_data(sys.argv[1], sys.argv[2])
