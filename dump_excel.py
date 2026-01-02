import pandas as pd

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'
try:
    df = pd.read_excel(file_path, header=None)
    print("Shape:", df.shape)
    for i in range(min(5, len(df))):
        print(f"Row {i}: {df.iloc[i].tolist()}")
except Exception as e:
    print(f"Error: {e}")
