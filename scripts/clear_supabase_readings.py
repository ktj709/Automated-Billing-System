import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from utils.logger import setup_logger

logger = setup_logger('clear_readings')

def clear_meter_readings():
    """Clear all meter readings from Supabase"""
    logger.info("=" * 60)
    logger.info("CLEARING METER READINGS FROM SUPABASE")
    logger.info("=" * 60)
    
    try:
        db_service = DatabaseService()
        
        if not db_service.use_supabase:
            logger.error("Not using Supabase mode!")
            return False
        
        # Get current count
        logger.info("Getting current readings count...")
        current_readings = db_service.get_all_readings(limit=10000)
        logger.info(f"Current readings: {len(current_readings)}")
        
        if len(current_readings) == 0:
            logger.info("No readings to clear.")
            return True
        
        # Delete all readings
        logger.info(f"\nDeleting {len(current_readings)} readings...")
        deleted_count = 0
        
        for reading in current_readings:
            reading_id = reading.get('id')
            if reading_id:
                try:
                    db_service.delete_reading(reading_id)
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        logger.info(f"  Deleted {deleted_count}/{len(current_readings)}...")
                except Exception as e:
                    logger.error(f"Error deleting reading {reading_id}: {e}")
        
        logger.info(f"\n✓ Successfully deleted {deleted_count} readings")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Error clearing readings: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_meter_readings()
    sys.exit(0 if success else 1)
