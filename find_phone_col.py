import pandas as pd

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
try:
    # We know from previous steps that header is likely around row 2-3
    # Let's search for "Contact" in the first 5 rows
    df = pd.read_excel(file_path, header=None, nrows=5)
    
    found = False
    for i, row in df.iterrows():
        row_str = [str(x) for x in row if pd.notna(x)]
        print(f"Row {i}: {row_str}")
        
        # Check for keywords
        if any("Contact" in x or "Phone" in x or "Mobile" in x for x in row_str):
            print(f"\nPotential Header Found at Row {i}")
            # Identify the specific column index
            for col_idx, val in enumerate(row):
                if pd.notna(val) and ("Contact" in str(val) or "Phone" in str(val) or "Mobile" in str(val)):
                    print(f"Column Index: {col_idx}, Name: {val}")
            found = True
            
    if not found:
        print("Could not find a column with 'Contact', 'Phone', or 'Mobile'.")

except Exception as e:
    print(f"Error: {e}")
