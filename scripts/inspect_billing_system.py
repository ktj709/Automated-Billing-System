import pandas as pd
import json

# Read the Master Data sheet
print("Reading Electricity_Billing_System.xlsx...")
xl_file = "data/Electricity_Billing_System.xlsx"

# Try to find the correct header row
df_temp = pd.read_excel(xl_file, sheet_name='Master Data', header=None, nrows=10)
print("\nFirst 10 rows (to find header):")
print(df_temp)

# Try reading with header at row 1 (0-indexed)
print("\n" + "="*80)
print("Trying with header at row 1:")
df = pd.read_excel(xl_file, sheet_name='Master Data', header=1)
print("\nColumns:", df.columns.tolist())
print(f"\nTotal rows: {len(df)}")
print("\nFirst 5 rows:")
print(df.head(5).to_string())

# Check for specific columns we need
required_cols = ['Unit_ID', 'Flat_no', 'Floor', 'Type', 'Client_Name']
print("\n" + "="*80)
print("Checking for required columns...")
for col in required_cols:
    # Try to find column (case-insensitive)
    found = [c for c in df.columns if col.lower() in str(c).lower()]
    print(f"{col}: {found if found else 'NOT FOUND'}")
