import pandas as pd
import sys
import os
import uuid
from datetime import datetime

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from utils.logger import setup_logger
from import_excel_to_neo4j import import_to_neo4j

logger = setup_logger('sync_neo4j_excel')

INPUT_FILE = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
SHEET_NAME = "Monthly Billing"

def sync_from_excel():
    """
    Sync customers, meters, and readings from Excel to Neo4j
    """
    logger.info("=" * 60)
    logger.info("SYNCING NEO4J FROM EXCEL MASTER DATA")
    logger.info("=" * 60)

    # Step 1: Import Customers and Meters
    logger.info("\nStep 1: Importing Customers and Meters...")
    try:
        import_to_neo4j()
    except Exception as e:
        logger.error(f"Failed to import customers/meters: {e}")
        return

    # Step 2: Import Readings
    logger.info("\nStep 2: Importing Readings from Excel...")
    
    try:
        # Read Excel file
        logger.info(f"Reading {SHEET_NAME} from {INPUT_FILE}...")
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=3)
        
        print("DEBUG: DataFrame Head:")
        print(df.head().to_string())
        sys.stdout.flush()
        
        readings_list = []
        current_date = datetime.now().strftime("%Y-%m-%d")
        created_at = datetime.now().isoformat()
        
        for idx, row in df.iterrows():
            if pd.isna(row.iloc[0]):
                continue
                
            try:
                unit_id = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else None
                meter_id = str(row.iloc[5]).strip().replace('.0', '') if not pd.isna(row.iloc[5]) else None
                units_consumed = float(row.iloc[6]) if not pd.isna(row.iloc[6]) else 0.0
                
                if not unit_id or not meter_id or 'Unit_ID' in str(unit_id):
                    continue
                
                # Debug log
                if idx < 5 or units_consumed > 0:
                    print(f"DEBUG: Row {idx}: Unit={unit_id}, Meter={meter_id}, Value={units_consumed}")

                # Generate a unique ID for the reading since we aren't using Supabase's ID
                reading_id = str(uuid.uuid4())
                
                reading_data = {
                    "id": reading_id,
                    "meter_id": meter_id,
                    "unit_id": unit_id,
                    "reading_value": units_consumed,
                    "reading_date": current_date,
                    "created_at": created_at,
                    "unit": "kWh"
                }
                readings_list.append(reading_data)
                
            except Exception as e:
                logger.warning(f"Skipping row {idx}: {e}")
                continue
                
        logger.info(f"Prepared {len(readings_list)} readings for sync.")
        
        # Sync to Neo4j
        neo4j_service = Neo4jService()
        if not neo4j_service.is_connected():
            logger.error("Could not connect to Neo4j.")
            return

        logger.info("Syncing readings to Neo4j...")
        # We reuse sync_readings_from_supabase as it handles the logic of clearing and creating
        result = neo4j_service.sync_readings_from_supabase(readings_list)
        
        if result.get('success'):
            logger.info("✓ Readings sync completed successfully!")
            logger.info(f"  Synced: {result.get('synced')}")
            logger.info(f"  Deleted old: {result.get('deleted')}")
        else:
            logger.error(f"✗ Readings sync failed: {result.get('error')}")
            
        neo4j_service.close()
        
    except Exception as e:
        logger.error(f"Error processing readings: {e}")
        import traceback
        traceback.print_exc()

    logger.info("\n" + "=" * 60)
    logger.info("SYNC COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    sync_from_excel()
