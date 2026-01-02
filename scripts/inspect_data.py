import pandas as pd

file_path = r"e:\Machine Learning Projects\Billing\data\Electrcity details for Software.xlsx"

try:
    # Check sheets
    xl = pd.ExcelFile(file_path)
    print("Sheet names:", xl.sheet_names)
    
    # Read first sheet
    df = pd.read_excel(file_path, header=None, nrows=20)
    header_row_index = None
    for i, row in df.iterrows():
        row_values = [str(val).strip() for val in row.values]
        if 'Flat no' in row_values:
            header_row_index = i
            break
            
    if header_row_index is not None:
        df = pd.read_excel(file_path, header=header_row_index)
        print(f"Using header row index: {header_row_index}")
        
        if 'Type' in df.columns and 'Flat no' in df.columns:
            print("\nSample Flat Nos by Type:")
            for t in df['Type'].unique():
                sample = df[df['Type'] == t]['Flat no'].head(3).tolist()
                print(f"{t}: {sample}")
                
    else:
        print("Header not found")

except Exception as e:
    print(f"Error: {e}")
