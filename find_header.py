import pandas as pd

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
try:
    df = pd.read_excel(file_path, header=None)
    for i, row in df.iterrows():
        # Check if row has 'Flat' and 'Total' or 'Amount'
        row_values = [str(x) for x in row if pd.notna(x)]
        if any('Flat' in x for x in row_values) and any('Amount' in x for x in row_values):
            print(f"FOUND HEADER AT INDEX {i}")
            print(row_values)
            break
except Exception as e:
    print(e)
