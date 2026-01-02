import os
import sys
import logging
from typing import List, Dict

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

logger = setup_logger('sync_to_neo4j')

def sync_data():
    """Sync customers, meters, and readings from Supabase to Neo4j"""
    logger.info("Starting sync process...")
    
    # Initialize services
    db = DatabaseService()
    neo4j = Neo4jService()
    
    if not neo4j.is_connected():
        logger.error("Failed to connect to Neo4j. Check your configuration.")
        return

    try:
        # 1. Fetch Active Meters (Registry) from Supabase
        logger.info("Fetching active meters (registry) from Supabase...")
        active_meters = db.get_active_meters()
        logger.info(f"Found {len(active_meters)} active meters/customers.")
        
        if not active_meters:
            logger.warning("No active meters found. Aborting sync.")
            return

        # 2. Import Customers and Meters into Neo4j
        logger.info("Importing Customers and Meters into Neo4j...")
        import_stats = neo4j.import_customers_and_meters(active_meters)
        
        if import_stats.get('success'):
            logger.info("Successfully imported customers and meters:")
            logger.info(f"  - Customers Created: {import_stats.get('customers_created')}")
            logger.info(f"  - Meters Created: {import_stats.get('meters_created')}")
            logger.info(f"  - Relationships Created: {import_stats.get('relationships_created')}")
        else:
            logger.error(f"Failed to import customers/meters: {import_stats.get('error')}")
            return

        # 3. Fetch All Readings from Supabase
        logger.info("Fetching all meter readings from Supabase...")
        # Using a large limit to get all readings
        all_readings = db.get_all_readings(limit=10000)
        logger.info(f"Found {len(all_readings)} readings.")

        # 4. Sync Readings to Neo4j
        logger.info("Syncing readings to Neo4j...")
        reading_stats = neo4j.sync_readings_from_supabase(all_readings)
        
        if reading_stats.get('success'):
            logger.info("Successfully synced readings:")
            logger.info(f"  - Synced: {reading_stats.get('synced')}")
            logger.info(f"  - Deleted Old: {reading_stats.get('deleted')}")
            if reading_stats.get('errors'):
                logger.warning(f"  - Errors: {len(reading_stats.get('errors'))}")
        else:
            logger.error(f"Failed to sync readings: {reading_stats.get('error')}")

        # 5. Final Stats
        logger.info("Fetching final graph statistics...")
        final_stats = neo4j.get_all_stats()
        logger.info(f"Final Graph Stats: {final_stats}")

    except Exception as e:
        logger.error(f"An error occurred during sync: {e}")
    finally:
        neo4j.close()
        logger.info("Sync process completed.")

if __name__ == "__main__":
    sync_data()
