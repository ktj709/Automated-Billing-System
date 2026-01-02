import pandas as pd

file_path = r'd:\Machine Learning Projects\Billing\data\Bills_Summary_November2025.xlsx'

def main():
    # Helper to find C16-SF
    for h in [1, 2, 3]:
        try:
            df = pd.read_excel(file_path, header=h)
            # Find columns
            flat_col = next((c for c in df.columns if "Flat" in str(c) and ("No" in str(c) or "Code" in str(c))), None)
            phone_col = next((c for c in df.columns if "Contact" in str(c) or "Mobile" in str(c) or "Phone" in str(c)), None)
            
            if flat_col and phone_col:
                print(f"Checking header row {h}")
                for i, row in df.iterrows():
                    flat = str(row[flat_col]).strip()
                    if "C16-SF" in flat or "C16 SF" in flat:
                        print(f"Found Flat: {flat}")
                        print(f"Raw Phone Value: {row[phone_col]}")
                        return
        except:
            continue
            
    print("Flat C16-SF not found in Excel search.")

if __name__ == "__main__":
    main()
