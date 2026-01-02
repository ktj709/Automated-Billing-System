import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress logging
import logging
logging.disable(logging.CRITICAL)

from services.database_service import DatabaseService
from collections import Counter

db = DatabaseService()

try:
    bills = db.get_all_bills()
    print(f"\nTotal bills found: {len(bills)}")
    
    statuses = [b.get('status') for b in bills]
    print(f"Status counts: {Counter(statuses)}")
    
    print("\nAmounts per status:")
    for status in set(statuses):
        amount = sum(float(b.get('amount', 0) or 0) for b in bills if b.get('status') == status)
        print(f"Status '{status}': {amount}")

except Exception as e:
    print(f"Error: {e}")
