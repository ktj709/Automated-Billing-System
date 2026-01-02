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
    return {item['code'].strip().upper(): float(item['total_amount']) for item in data}

def main():
    file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
    
    # Try multiple header rows
    best_df = None
    best_flat_col = None
    
    for h in [0, 1, 2, 3, 4]:
        try:
            df = pd.read_excel(file_path, header=h)
            # Find flat column
            flat_col = next((c for c in df.columns if "Flat" in str(c) and ("No" in str(c) or "Code" in str(c))), None)
            if not flat_col and len(df.columns) > 0:
                 # Check if first col looks like Flat Code (e.g. contains "-")
                 first_col_vals = df.iloc[:,0].astype(str)
                 if first_col_vals.str.contains("-").sum() > len(df) * 0.5:
                     flat_col = df.columns[0]
            
            if flat_col:
                best_df = df
                best_flat_col = flat_col
                print(f"Using Header Row: {h}, Flat Column: {flat_col}")
                break
        except:
            pass
            
    if best_df is None:
        print("Could not parse Excel structure.")
        return

    df = best_df
    excel_records = {}
    
    # Heuristic to find Amount column: specific names or correlation
    amount_col = None
    candidates = [c for c in df.columns if "Amount" in str(c) or "Total" in str(c) or "Net" in str(c) or "Payable" in str(c)]
    
    if len(candidates) > 0:
        # Prefer 'Net Payable' or 'Total Amount'
        amount_col = next((c for c in candidates if "Payable" in str(c)), 
                          next((c for c in candidates if "Total" in str(c) and "Amount" in str(c)), candidates[0]))
    
    supabase_map = load_supabase_data()
    
    # Build Excel Map (Flat -> Amount) assuming found col or just trying to find one
    # If no amount col found, try to find one by matching values with Supabase!
    
    if not amount_col:
        print("Searching for Amount column by value matching...")
        # Get a subset of common flats
        common_flats = []
        for i, row in df.iterrows():
            flat = str(row[best_flat_col]).strip().upper()
            if flat in supabase_map:
                common_flats.append((i, flat))
        
        # Check all numeric columns
        best_match_score = 0
        for col in df.columns:
            if col == best_flat_col: continue
            score = 0
            try:
                # Check correlation
                matches = 0
                for i, flat in common_flats:
                    val = df.iloc[i][col]
                    try:
                        val = float(val)
                        if abs(val - supabase_map[flat]) < 5.0:
                            matches += 1
                    except:
                        pass
                
                if matches > best_match_score:
                    best_match_score = matches
                    amount_col = col
            except:
                pass
        
        print(f"Inferred Amount Column: {amount_col} (Matches: {best_match_score}/{len(common_flats)})")

    if not amount_col:
        print("Failed to identify Amount column.")
        return

    # Create Final Map
    for _, row in df.iterrows():
        flat = str(row[best_flat_col]).strip().upper()
        try:
            val = float(row[amount_col])
            excel_records[flat] = val
        except:
            pass # Skip invalid rows

    # Compare
    mismatches = []
    missing_sb = []
    missing_ex = []

    all_flats = set(excel_records.keys()) | set(supabase_map.keys())
    
    for flat in all_flats:
        if flat not in excel_records:
            missing_ex.append(flat)
            continue
        if flat not in supabase_map:
            missing_sb.append(flat)
            continue
        
        ex_val = excel_records[flat]
        sb_val = supabase_map[flat]
        if abs(ex_val - sb_val) > 1.0:
            mismatches.append((flat, ex_val, sb_val))

    with open('comparison_report.txt', 'w') as f:
        f.write(f"Comparison Results:\n")
        f.write(f"Total Matches: {len(all_flats) - len(mismatches) - len(missing_sb) - len(missing_ex)}\n")
        f.write(f"Mismatches: {len(mismatches)}\n")
        for m in mismatches:
            f.write(f"  {m[0]}: Excel={m[1]}, Supabase={m[2]}\n")
            
        if missing_ex:
            f.write(f"Missing in Excel: {len(missing_ex)}\n")
            f.write(f"{', '.join(sorted(missing_ex))}\n")
        if missing_sb:
            f.write(f"Missing in Supabase: {len(missing_sb)}\n")
            f.write(f"{', '.join(sorted(missing_sb))}\n")
            
    print("Report written to comparison_report.txt")

if __name__ == "__main__":
    main()
