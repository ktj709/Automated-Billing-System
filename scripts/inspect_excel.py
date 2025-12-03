import pandas as pd
import os

file_path = 'data/Blessings_City_Master_Data.xlsx'

try:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
    else:
        df = pd.read_excel(file_path)
        print("Columns:", df.columns.tolist())
        print("\nFirst 3 rows:")
        print(df.head(3).to_string())
except Exception as e:
    print(f"Error reading Excel file: {e}")
