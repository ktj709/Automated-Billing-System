import sys
import os
import logging

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

logger = setup_logger('sync_readings')

def sync_readings():
    """
    Synchronize meter readings from Supabase to Neo4j
    """
    logger.info("Starting meter reading synchronization...")
    
    # Initialize services
    try:
        db_service = DatabaseService()
        neo4j_service = Neo4jService()
        
        if not neo4j_service.is_connected():
            logger.error("Could not connect to Neo4j. Please check your configuration.")
            return
            
        if not db_service.use_supabase:
            logger.warning("Not using Supabase mode. This script is optimized for Supabase.")
            
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return

    # Fetch all readings from Supabase
    try:
        logger.info("Fetching readings from Supabase...")
        readings = db_service.get_all_readings(limit=10000)
        logger.info(f"Retrieved {len(readings)} readings from Supabase")
        
        if not readings:
            logger.warning("No readings found in Supabase. Nothing to sync.")
            return
            
    except Exception as e:
        logger.error(f"Failed to fetch readings from Supabase: {e}")
        return

    # Sync to Neo4j
    try:
        logger.info("Syncing to Neo4j...")
        result = neo4j_service.sync_readings_from_supabase(readings)
        
        if result.get('success'):
            logger.info("Synchronization completed successfully!")
            logger.info(f"Total readings processed: {result.get('total')}")
            logger.info(f"Readings deleted from Neo4j: {result.get('deleted')}")
            logger.info(f"Readings synced to Neo4j: {result.get('synced')}")
            
            if result.get('errors'):
                logger.warning(f"Encountered {len(result.get('errors'))} errors during sync:")
                for error in result.get('errors')[:10]:
                    logger.warning(f"  - {error}")
                if len(result.get('errors')) > 10:
                    logger.warning(f"  ... and {len(result.get('errors')) - 10} more")
        else:
            logger.error(f"Synchronization failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}")
    finally:
        neo4j_service.close()

if __name__ == "__main__":
    sync_readings()
