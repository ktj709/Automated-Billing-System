import pandas as pd

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
try:
    # Read first few rows without header
    df = pd.read_excel(file_path, header=None, nrows=10)
    print("First 10 rows (raw):")
    print(df.to_string())
    
    # Try logic to find header
    header_idx = -1
    for i, row in df.iterrows():
        row_str = " ".join([str(x) for x in row if pd.notna(x)])
        if "Flat" in row_str and ("Amount" in row_str or "Units" in row_str):
            header_idx = i
            print(f"\nPotential Header Row found at index {i}:")
            print(row.tolist())
            break
except Exception as e:
    print(f"Error: {e}")
