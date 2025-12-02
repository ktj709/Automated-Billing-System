import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress logging
import logging
logging.disable(logging.CRITICAL)

from services.database_service import DatabaseService
import pandas as pd

db = DatabaseService()

try:
    print("Fetching all bills...")
    bills = db.get_all_bills()
    df = pd.DataFrame(bills)
    
    print(f"Total bills: {len(df)}")
    print(f"Status counts:\n{df['status'].value_counts()}")
    
    # Simulate App Logic (Updated)
    total_paid = sum(b.get("amount", 0) for b in bills if b.get("status") == "paid")
    total_outstanding = sum(b.get("amount", 0) for b in bills if b.get("status") in ["pending", "generated", "overdue"])
    invoices = len([b for b in bills if b.get("status") in ["pending", "generated", "overdue"]])
    
    print("\n--- App Logic Simulation ---")
    print(f"Total Paid: {total_paid}")
    print(f"Total Outstanding (Pending + Generated + Overdue): {total_outstanding}")
    print(f"Invoices to Send (Pending + Generated + Overdue): {invoices}")
    
    # Verify Analytics Logic (Updated)
    print("\n--- Analytics Logic Simulation ---")
    collected_revenue = df[df['status'] == 'paid']['amount'].sum()
    pending_revenue = df[df['status'].isin(['pending', 'generated', 'overdue'])]['amount'].sum()
    
    print(f"Collected Revenue: {collected_revenue}")
    print(f"Pending Revenue: {pending_revenue}")
    
    if abs(total_outstanding - pending_revenue) < 0.01:
        print("\n✅ Logic matches between App and Analytics!")
    else:
        print("\n❌ Mismatch between App and Analytics logic!")

except Exception as e:
    print(f"Error: {e}")
