import pandas as pd
import json
import os

def load_supabase_data():
    data = []
    files = ['supabase_chunk1.json', 'supabase_chunk2.json']
    for f in files:
        if os.path.exists(f):
            with open(f, 'r') as file:
                data.extend(json.load(file))
        else:
            print(f"Warning: {f} not found.")
    return data

def main():
    # Load Excel
    file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
    try:
        # Heuristic to find the header row
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
            print("Excel header not found!")
            return

        # Load Supabase
        supabase_data = load_supabase_data()
        
        # Create dictionaries for comparison
        excel_map = {}
        # Identify columns dynamically
        flat_col = next((c for c in df.columns if "Flat" in str(c) and ("No" in str(c) or "Code" in str(c))), df.columns[0])
        possible_amount_cols = [c for c in df.columns if "Amount" in str(c)]
        # Prefer "Total Amount" if available
        amount_col = next((c for c in possible_amount_cols if "Total" in str(c)), possible_amount_cols[0] if possible_amount_cols else None)

        if not amount_col:
            print("Could not identify Amount column in Excel.")
            return

        for _, row in df.iterrows():
            flat = str(row[flat_col]).strip().upper() # Normalize casing
            try:
                amount = float(row[amount_col])
            except:
                amount = 0.0
            excel_map[flat] = amount

        supabase_map = {}
        for item in supabase_data:
            flat = str(item['code']).strip().upper()
            amount = float(item['total_amount'])
            supabase_map[flat] = amount

        # Comparison Logic
        all_flats = set(excel_map.keys()) | set(supabase_map.keys())
        mismatches = []
        missing_in_supabase = []
        missing_in_excel = []

        for flat in all_flats:
            if flat not in excel_map:
                missing_in_excel.append(flat)
                continue
            if flat not in supabase_map:
                missing_in_supabase.append(flat)
                continue
            
            excel_val = excel_map[flat]
            sb_val = supabase_map[flat]
            
            if abs(excel_val - sb_val) > 1.0: # Tolerance of 1.0
                mismatches.append((flat, excel_val, sb_val))

        # Output Results
        print(f"Total Flats in Excel: {len(excel_map)}")
        print(f"Total Flats in Supabase: {len(supabase_map)}")
        print("-" * 30)
        
        if not mismatches and not missing_in_supabase and not missing_in_excel:
            print("SUCCESS: Excel and Supabase data match primarily!")
        else:
            if mismatches:
                print(f"MISMATCHES: {len(mismatches)}")
                for m in mismatches:
                    print(f"  {m[0]}: Excel={m[1]}, Supabase={m[2]}, Diff={m[1]-m[2]}")
            
            if missing_in_supabase:
                print(f"MISSING IN SUPABASE: {len(missing_in_supabase)}")
                print(f"  {', '.join(missing_in_supabase)}")
                
            if missing_in_excel:
                print(f"MISSING IN EXCEL: {len(missing_in_excel)}")
                # Only show first 5 if too many
                full_list = sorted(missing_in_excel)
                preview = ", ".join(full_list[:5])
                if len(full_list) > 5:
                    preview += "..."
                print(f"  {preview}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
