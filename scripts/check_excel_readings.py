import pandas as pd

file_path = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
sheet_name = "Monthly Billing"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
    
    # Check column 6 (Units_Consumed)
    non_zero = df[df.iloc[:, 6] > 0]
    
    print(f"Total rows: {len(df)}")
    print(f"Non-zero readings: {len(non_zero)}")
    
    if len(non_zero) > 0:
        print("\nSample non-zero readings:")
        print(non_zero.iloc[:5, [0, 5, 6]].to_string())
    else:
        print("\nAll readings are 0.")
        
except Exception as e:
    print(f"Error: {e}")
