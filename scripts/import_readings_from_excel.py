import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from utils.logger import setup_logger

logger = setup_logger('import_readings')

INPUT_FILE = r"e:\Machine Learning Projects\Billing\data\Electricity_Billing_System.xlsx"
SHEET_NAME = "Monthly Billing"

def import_readings_with_metadata():
    """Import meter readings with full metadata (unit_id, flat_no, floor, type, client_name)"""
    logger.info("=" * 60)
    logger.info("IMPORTING READINGS WITH FULL METADATA")
    logger.info("=" * 60)
    
    try:
        # Read Excel file (header is at row 3, 0-indexed)
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=3)
        
        logger.info(f"Total rows to process: {len(df)}")
        
        # Initialize database service
        db = DatabaseService()
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # Use current date for all readings
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.iloc[0]):
                continue
                
            try:
                # Extract all fields (using column indices from inspection)
                unit_id = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else None
                flat_no = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else None
                floor = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else None
                flat_type = str(row.iloc[3]).strip() if not pd.isna(row.iloc[3]) else None
                client_name = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else None
                meter_id = str(row.iloc[5]).strip().replace('.0', '') if not pd.isna(row.iloc[5]) else None
                units_consumed = float(row.iloc[6]) if not pd.isna(row.iloc[6]) else 0.0
                
                # Skip if essential data is missing or if it's a header row
                if not unit_id or not meter_id or 'Unit_ID' in str(unit_id):
                    skipped_count += 1
                    continue
                
                # Create reading data with ALL metadata fields
                reading_data = {
                    "meter_id": meter_id,
                    "customer_id": f"UNIT-{unit_id}",  # Use unit_id as primary identifier
                    "reading_value": units_consumed,
                    "reading_date": current_date,
                    "unit_id": unit_id,
                    "flat_no": flat_no,
                    "floor": floor,
                    "type": flat_type,
                    "client_name": client_name,
                    "created_at": datetime.now().isoformat()
                }
                
                # Insert to Supabase
                try:
                    result = db.insert_meter_reading(reading_data)
                    
                    if result:
                        imported_count += 1
                        if units_consumed > 0:
                            logger.info(f"  ✓ {unit_id} - {client_name[:30]} - {units_consumed} kWh")
                        else:
                            if imported_count <= 5:  # Only log first few zeros
                                logger.info(f"  ✓ {unit_id} - {client_name[:30]} - 0 kWh")
                except Exception as insert_error:
                    errors.append(f"{unit_id}: {str(insert_error)}")
                    logger.warning(f"  ⚠ Skipped {unit_id}: {str(insert_error)}")
                    continue
                    
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                logger.warning(f"  ⚠ Skipped row {idx}: {str(e)}")
                continue
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ Import completed!")
        logger.info(f"  - Total rows processed: {len(df)}")
        logger.info(f"  - Successfully imported: {imported_count}")
        logger.info(f"  - Skipped: {skipped_count}")
        logger.info(f"  - Errors: {len(errors)}")
        
        if errors and len(errors) <= 10:
            logger.warning(f"\nErrors encountered:")
            for error in errors:
                logger.warning(f"  - {error}")
        elif errors:
            logger.warning(f"\n{len(errors)} errors encountered (showing first 5):")
            for error in errors[:5]:
                logger.warning(f"  - {error}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ All readings now include:")
        logger.info(f"   - unit_id (primary identifier)")
        logger.info(f"   - flat_no")
        logger.info(f"   - floor")
        logger.info(f"   - type")
        logger.info(f"   - client_name")
        logger.info(f"   - meter_id")
        logger.info(f"   - reading_value")
        logger.info(f"   - reading_date")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Error importing readings: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_readings_with_metadata()
    sys.exit(0 if success else 1)
