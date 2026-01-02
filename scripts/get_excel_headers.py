
import pandas as pd
import json

try:
    file_path = r'd:\\Machine Learning Projects\\Billing\\data\\Bills_Summary_November2025.xlsx'
    # Read first 5 rows to inspect structure
    df = pd.read_excel(file_path, nrows=5, header=None)
    # Convert to list of lists
    data = df.values.tolist()
    
    with open('headers.json', 'w') as f:
        json.dump({"success": True, "data": data}, f)
    print("Done")
except Exception as e:
    with open('headers.json', 'w') as f:
        json.dump({"success": False, "error": str(e)}, f)
    print("Error")
