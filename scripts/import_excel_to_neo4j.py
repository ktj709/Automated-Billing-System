import sys
import os
import pandas as pd
import json
import logging

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

logger = setup_logger('import_excel')

# File paths
EXCEL_FILE = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
JSON_FILE = r"e:\Machine Learning Projects\Billing\data\meter_registry.json"

def load_data_from_excel():
    """Load data from Master Data sheet in Excel"""
    logger.info("Loading data from Excel file...")
    
    all_data = []
    
    try:
        # Try to use existing JSON file first
        if os.path.exists(JSON_FILE):
            logger.info(f"Found existing JSON registry: {JSON_FILE}")
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            logger.info(f"Loaded {len(all_data)} entries from JSON")
            return all_data
            
        logger.info("JSON file not found, reading from Excel...")
        
        # Read Master Data sheet
        sheet_name = "Master Data"
        try:
            logger.info(f"Reading sheet: {sheet_name}")
            
            # Read actual data
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
            
            # Process rows
            for _, row in df.iterrows():
                unit_id = str(row.get('Unit_ID', '')).strip()
                if not unit_id or unit_id.lower() == 'nan':
                    continue
                
                entry = {
                    "unit_id": unit_id,
                    "flat_no": str(row.get('Flat_no', '')).strip(),
                    "floor": str(row.get('Floor', '')).strip(),
                    "type": str(row.get('Type', '')).strip(),
                    "client_name": str(row.get('Client_Name', '')).strip(),
                    "meter_id": str(row.get('Meter_No', '')).strip().replace('.0', ''),
                    "fixed_charge": 0  # Explicitly 0 as requested
                }
                
                # Validate
                if entry['meter_id'] and entry['meter_id'].lower() != 'nan':
                    all_data.append(entry)
            
            logger.info(f"Loaded {len(all_data)} entries from {sheet_name}")
            
            # Save to JSON for future use
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2)
            logger.info(f"Saved registry to {JSON_FILE}")
            
        except Exception as e:
            logger.error(f"Error reading sheet {sheet_name}: {e}")
    
        logger.info(f"Total entries loaded: {len(all_data)}")
        return all_data
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return []

def import_to_neo4j():
    """Import customers and meters from Excel to Neo4j"""
    logger.info("=" * 60)
    logger.info("IMPORTING EXCEL DATA TO NEO4J")
    logger.info("=" * 60)
    
    # Load data
    data = load_data_from_excel()
    
    if not data:
        logger.error("No data to import!")
        return
    
    # Initialize Neo4j service
    try:
        neo4j_service = Neo4jService()
        
        if not neo4j_service.is_connected():
            logger.error("Could not connect to Neo4j. Please check your configuration.")
            return
            
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j service: {e}")
        return
    
    # Import data
    try:
        logger.info(f"\nImporting {len(data)} entries to Neo4j...")
        result = neo4j_service.import_customers_and_meters(data)
        
        if result.get('success'):
            logger.info("✓ Import completed successfully!")
            logger.info(f"  Customers created: {result.get('customers_created', 0)}")
            logger.info(f"  Meters created: {result.get('meters_created', 0)}")
            logger.info(f"  Relationships created: {result.get('relationships_created', 0)}")
            
            if result.get('errors'):
                logger.warning(f"\nEncountered {len(result.get('errors'))} errors:")
                for error in result.get('errors')[:10]:
                    logger.warning(f"  - {error}")
                if len(result.get('errors')) > 10:
                    logger.warning(f"  ... and {len(result.get('errors')) - 10} more")
        else:
            logger.error(f"✗ Import failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Unexpected error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_service.close()
    
    logger.info("=" * 60)
    logger.info("IMPORT COMPLETED")
    logger.info("=" * 60)

if __name__ == "__main__":
    import_to_neo4j()
