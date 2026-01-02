import pandas as pd
import os

file_path = "d:\\Machine Learning Projects\\Billing\\data\\Bills_Summary_November2025.xlsx"

if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
else:
    try:
        df = pd.read_excel(file_path, header=None)
        print("File read successfully.")
        print("-" * 30)
        
        for i in range(20):
            row_values = df.iloc[i].tolist()
            # Filter out NaNs for cleaner view
            clean_row = [str(x) for x in row_values if pd.notna(x)]
            print(f"Row {i}: {clean_row}")

        import sys
        sys.exit()
            
    except Exception as e:
        print(f"Error reading excel: {e}")
