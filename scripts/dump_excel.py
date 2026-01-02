import pandas as pd
import sys

file_path = "d:\\Machine Learning Projects\\Billing\\data\\Bills_Summary_November2025.xlsx"
output_path = "d:\\Machine Learning Projects\\Billing\\scripts\\excel_dump.txt"

try:
    df = pd.read_excel(file_path, header=None)
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(min(20, len(df))):
            row_values = df.iloc[i].tolist()
            # Replace NaNs with empty string
            clean_row = [str(x) if pd.notna(x) else "" for x in row_values]
            f.write(f"Row {i}: {clean_row}\n")
    print(f"Dumped 20 rows to {output_path}")
except Exception as e:
    print(f"Error: {e}")
