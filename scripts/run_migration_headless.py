import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

# Import our individual migration scripts
from scripts.clear_neo4j import clear_all_neo4j_data
from scripts.import_excel_to_neo4j import import_to_neo4j
from scripts.sync_readings_to_neo4j import sync_readings
from scripts.sync_bills_to_neo4j import sync_bills

logger = setup_logger('headless_migration')

def run_headless_migration():
    print("STARTING HEADLESS MIGRATION...")
    
    # Step 1: Clear all existing data
    print("\nSTEP 1: CLEARING ALL DATA")
    # We call the function directly, but clear_all_neo4j_data in the imported module 
    # is the one defined in the file, which doesn't have the prompt inside the function itself,
    # only in the if __name__ == "__main__" block.
    # Wait, let me double check clear_neo4j.py content again.
    # Yes, clear_all_neo4j_data() is the function. The prompt is in the main block.
    # So calling clear_all_neo4j_data() directly is safe.
    clear_all_neo4j_data()
    
    # Step 2: Import customers and meters from Excel
    print("\nSTEP 2: IMPORTING EXCEL DATA")
    import_to_neo4j()
    
    # Step 3: Sync meter readings from Supabase
    print("\nSTEP 3: SYNCING METER READINGS")
    sync_readings()
    
    # Step 4: Sync bills from Supabase
    print("\nSTEP 4: SYNCING BILLS")
    sync_bills()
    
    print("\nMIGRATION COMPLETE!")

if __name__ == "__main__":
    run_headless_migration()
