import pandas as pd
import openpyxl
import sys
import os

# Inspect the Monthly Billing sheet
xl_file = "data/Electricity_Billing_System.xlsx"
wb = openpyxl.load_workbook(xl_file)
ws = wb['Monthly Billing']

print("=" * 80)
print("MONTHLY BILLING SHEET STRUCTURE")
print("=" * 80)

# Get first 10 rows
for i, row in enumerate(ws.iter_rows(max_row=10), 1):
    values = [cell.value for cell in row]
    print(f"\nRow {i}:")
    for j, val in enumerate(values[:12], 1):
        if val is not None:
            print(f"  Col {j}: {val}")
