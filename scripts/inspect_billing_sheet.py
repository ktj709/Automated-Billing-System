import pandas as pd
import os

file_path = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
sheet_name = "Monthly Billing"

try:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
    else:
        print(f"Reading {file_path} - Sheet: {sheet_name}")
        # Header is at row 3 (0-indexed) based on previous scripts
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
        with open('columns_debug.txt', 'w') as f:
            for i, col in enumerate(df.columns):
                f.write(f"{i}: {col}\n")
            f.write("\nFIRST ROW:\n")
            f.write(str(df.iloc[0].tolist()))
except Exception as e:
    print(f"Error reading Excel file: {e}")
