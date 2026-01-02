import pandas as pd
import math

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'

def clean_phone(val):
    if pd.isna(val): return None
    s = str(val).strip()
    if s == '' or s.lower() == 'nan': return None
    # Remove .0 if present (excel float)
    if s.endswith('.0'): s = s[:-2]
    # Basic cleanup: remove spaces, dashes
    s = s.replace(' ', '').replace('-', '')
    # Check length (Indian numbers are usually 10 digits)
    if not s.isdigit(): return None 
    if len(s) < 10: return None # suspicious
    return s

def main():
    # Try header 1, 2, 3
    df = None
    flat_col = None
    phone_col = None
    
    for h in [1, 2, 3]:
        temp_df = pd.read_excel(file_path, header=h)
        # Find Flat column
        fc = next((c for c in temp_df.columns if "Flat" in str(c) and ("No" in str(c) or "Code" in str(c))), None)
        # Find Contact column
        pc = next((c for c in temp_df.columns if "Contact" in str(c) or "Mobile" in str(c) or "Phone" in str(c)), None)
        
        if fc and pc:
            df = temp_df
            flat_col = fc
            phone_col = pc
            print(f"Using Header Row: {h}")
            print(f"Flat Column: {flat_col}")
            print(f"Phone Column: {phone_col}")
            break
            
    if not df is not None:
        print("Could not identify columns.")
        return

    updates = []
    
    for i, row in df.iterrows():
        flat = str(row[flat_col]).strip()
        phone_raw = row[phone_col]
        phone = clean_phone(phone_raw)
        
        if flat and phone:
            # Construct SQL
            # Subquery to update owner of this flat
            sql = f"""
UPDATE owners
SET phone = '{phone}'
WHERE id IN (
    SELECT owner_id
    FROM flat_owners fo
    JOIN flats f ON fo.flat_id = f.id
    WHERE f.code = '{flat}'
);
"""
            updates.append(sql.strip())
            
    # Write to file
    with open('update_phones.sql', 'w', encoding='utf-8') as f:
        f.write("\n".join(updates))
        
    print(f"Generated {len(updates)} SQL update statements.")

if __name__ == "__main__":
    main()
