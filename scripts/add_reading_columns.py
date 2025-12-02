import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from utils.logger import setup_logger

logger = setup_logger('add_columns')

def add_columns_to_meter_readings():
    """Add extra columns to meter_readings table in Supabase"""
    logger.info("=" * 60)
    logger.info("ADDING COLUMNS TO METER_READINGS TABLE")
    logger.info("=" * 60)
    
    try:
        db = DatabaseService()
        
        # SQL to add columns (Supabase uses PostgreSQL)
        # Note: This is a schema change, so we need to use raw SQL
        
        columns_to_add = [
            ("unit_id", "TEXT"),
            ("flat_no", "TEXT"),
            ("floor", "TEXT"),
            ("type", "TEXT"),
            ("client_name", "TEXT")
        ]
        
        logger.info("Adding the following columns to meter_readings table:")
        for col_name, col_type in columns_to_add:
            logger.info(f"  - {col_name} ({col_type})")
        
        logger.info("\n⚠️  Note: Schema changes must be done through Supabase Dashboard")
        logger.info("   Go to: Supabase Dashboard → Table Editor → meter_readings")
        logger.info("   Add these columns manually:")
        logger.info("")
        for col_name, col_type in columns_to_add:
            logger.info(f"   • {col_name} - Type: {col_type} - Nullable: Yes")
        
        logger.info("\n" + "=" * 60)
        logger.info("After adding columns, run import_readings_from_excel.py again")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_columns_to_meter_readings()
    sys.exit(0 if success else 1)
