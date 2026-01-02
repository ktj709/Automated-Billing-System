import re

report_path = r"d:\Machine Learning Projects\Billing\scripts\verification_report.txt"

try:
    with open(report_path, 'r', encoding='utf-16') as f:
        lines = f.readlines()
        
    diff_lines = [l for l in lines if "|" in l and "Total Amount" in l]
    
    print(f"Total Discrepancy Lines: {len(diff_lines)}")
    
    rounded_count = 0
    total_diff = 0.0
    
    for line in diff_lines:
        # Format: Flat No | Col | Excel | DB | Diff
        parts = line.split('|')
        if len(parts) >= 5:
            flat = parts[0].strip()
            excel_val = float(parts[2].strip())
            db_val = float(parts[3].strip())
            diff = float(parts[4].strip())
            
            # Check if DB value is essentially an integer
            if db_val.is_integer():
                rounded_count += 1
            
            print(f"{flat}: Ex={excel_val}, DB={db_val}, Diff={diff:.2f}")

    print("-" * 30)
    print(f"Rows where DB value is Integer: {rounded_count}/{len(diff_lines)}")
    
except Exception as e:
    print(f"Error: {e}")
