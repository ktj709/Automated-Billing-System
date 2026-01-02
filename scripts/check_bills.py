import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

db = DatabaseService()

try:
    bills = db.get_all_bills()
    print(f"Total bills found: {len(bills)}")
    
    if bills:
        print("First bill sample:")
        print(bills[0])
        
        paid_bills = [b for b in bills if b.get('status') == 'paid']
        pending_bills = [b for b in bills if b.get('status') == 'pending']
        
        print(f"Paid bills: {len(paid_bills)}")
        print(f"Pending bills: {len(pending_bills)}")
        
        total_paid = sum(float(b.get('amount', 0)) for b in paid_bills)
        total_outstanding = sum(float(b.get('amount', 0)) for b in pending_bills)
        
        print(f"Total Paid: {total_paid}")
        print(f"Total Outstanding: {total_outstanding}")
    else:
        print("No bills found in the database.")

except Exception as e:
    print(f"Error: {e}")
