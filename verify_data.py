import pandas as pd
import json
import os

# Load Excel
file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
df = None
try:
    # Use find_header logic
    temp_df = pd.read_excel(file_path, header=None)
    header_idx = -1
    for i, row in temp_df.iterrows():
        row_str = " ".join([str(x) for x in row if pd.notna(x)])
        if "Flat" in row_str and ("Amount" in row_str or "Units" in row_str):
            header_idx = i
            break
    
    if header_idx != -1:
        df = pd.read_excel(file_path, header=header_idx)
    else:
        print("Header not found! Exiting.")
        exit(1)

    print(f"Loaded Excel with {len(df)} rows.")
    print(f"Columns found: {df.columns.tolist()}")
    
    # Load Supabase Data
    supabase_data = []
    for f in ['batch1.json', 'batch2.json', 'batch3.json']:
        if os.path.exists(f):
            with open(f, 'r') as file:
                supabase_data.extend(json.load(file))
                
    print(f"Loaded Supabase data with {len(supabase_data)} rows.")

    # Create Dictionary for comparison
    flat_col = None
    amount_col = None
    
    for c in df.columns:
        c_str = str(c)
        if "Flat" in c_str and ("No" in c_str or "Code" in c_str):
            flat_col = c
        if "Amount" in c_str and "Total" in c_str:
            amount_col = c
        if "Bill" in c_str and "Amount" in c_str and not amount_col:
             amount_col = c

    if not flat_col or not amount_col:
        print(f"Could not identify columns. Flat col: {flat_col}, Amount col: {amount_col}")
        # Try fallbacks/hardcoded indices if names fail?
        # Assuming col 0 is flat, col 'Total Amount' etc.
        if not flat_col: flat_col = df.columns[0] # assume first column
        if not amount_col: 
             # try to find any column with 'Amount'
             amounts = [c for c in df.columns if "Amount" in str(c)]
             if amounts: amount_col = amounts[0]
        
    print(f"Using columns: '{flat_col}' and '{amount_col}'")

    excel_map = {}
    for i, row in df.iterrows():
        flat = str(row[flat_col]).strip()
        try:
            amount = float(row[amount_col])
        except:
            amount = 0.0
        excel_map[flat] = amount

    supabase_map = {}
    for item in supabase_data:
        flat = str(item['code']).strip()
        amount = float(item['total_amount'])
        supabase_map[flat] = amount

    # Compare
    mismatches = []
    missing_in_supabase = []
    missing_in_excel = []

    all_flats = set(excel_map.keys()) | set(supabase_map.keys())
    
    for flat in all_flats:
        if flat not in excel_map:
            missing_in_excel.append(flat)
            continue
        if flat not in supabase_map:
            missing_in_supabase.append(flat)
            continue
        
        val_excel = excel_map[flat]
        val_supabase = supabase_map[flat]
        
        if abs(val_excel - val_supabase) > 1.0: # allow small diff
            mismatches.append((flat, val_excel, val_supabase))

    # Generate Report
    report_lines = []
    report_lines.append("# Data Verification Report: Nov 2025")
    report_lines.append(f"**Date:** {pd.Timestamp.now()}")
    report_lines.append(f"**Excel Source:** `{file_path}`")
    report_lines.append(f"**Supabase Project:** `blessing_city_electric` (November 2025 Bill Cycle)")
    report_lines.append("\n## Summary")
    
    if not mismatches and not missing_in_supabase and not missing_in_excel:
        report_lines.append("✅ **SUCCESS**: All data matches exactly!")
    else:
        report_lines.append(f"❌ **DISCREPANCIES FOUND**")
        report_lines.append(f"- **Mismatches:** {len(mismatches)}")
        report_lines.append(f"- **Missing in Supabase:** {len(missing_in_supabase)}")
        report_lines.append(f"- **Missing in Excel:** {len(missing_in_excel)}")
        
        if mismatches:
            report_lines.append("\n## Mismatches (Diff > 1.0)")
            report_lines.append("| Flat Code | Excel Amount | Supabase Amount | Difference |")
            report_lines.append("|---|---|---|---|")
            for m in mismatches:
                diff = m[1] - m[2]
                report_lines.append(f"| {m[0]} | {m[1]} | {m[2]} | {diff:.2f} |")
        
        if missing_in_supabase:
            report_lines.append("\n## Missing in Supabase")
            report_lines.append("These flats exist in Excel but not in Supabase query results:")
            report_lines.append(", ".join(sorted(missing_in_supabase)))

        if missing_in_excel:
            report_lines.append("\n## Missing in Excel")
            report_lines.append("These flats exist in Supabase but not in Excel:")
            report_lines.append(", ".join(sorted(missing_in_excel)))

    with open('verification_report.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    
    print("Report generated: verification_report.md")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
