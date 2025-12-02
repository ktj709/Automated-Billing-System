import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

# Import our individual migration scripts
from clear_neo4j import clear_all_neo4j_data
from import_excel_to_neo4j import import_to_neo4j
from sync_readings_to_neo4j import sync_readings
from sync_bills_to_neo4j import sync_bills

logger = setup_logger('migrate_all')

def print_banner(text):
    """Print a nice banner"""
    width = 60
    logger.info("=" * width)
    logger.info(text.center(width))
    logger.info("=" * width)

def display_stats(neo4j_service):
    """Display comprehensive database statistics"""
    try:
        stats = neo4j_service.get_all_stats()
        
        if 'error' in stats:
            logger.error(f"Error getting stats: {stats['error']}")
            return
        
        logger.info("\n" + "=" * 60)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 60)
        
        logger.info("\nNodes:")
        for node_type, count in stats['nodes'].items():
            logger.info(f"  {node_type.capitalize()}: {count}")
        
        total_nodes = sum(stats['nodes'].values())
        logger.info(f"  Total Nodes: {total_nodes}")
        
        logger.info("\nRelationships:")
        for rel_type, count in stats['relationships'].items():
            logger.info(f"  {rel_type.upper()}: {count}")
        
        total_rels = sum(stats['relationships'].values())
        logger.info(f"  Total Relationships: {total_rels}")
        
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Error displaying stats: {e}")

def migrate_all_data():
    """
    Master migration script - orchestrates all migration steps
    """
    start_time = datetime.now()
    
    print_banner("NEO4J DATA MIGRATION")
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get initial stats
    try:
        neo4j_service = Neo4jService()
        if neo4j_service.is_connected():
            logger.info("Initial database state:")
            display_stats(neo4j_service)
            neo4j_service.close()
    except Exception as e:
        logger.warning(f"Could not get initial stats: {e}")
    
    try:
        # Step 1: Clear all existing data
        print_banner("STEP 1: CLEARING ALL DATA")
        logger.info("Clearing all existing Neo4j data...\n")
        
        # Call clear function without confirmation (assume user already confirmed)
        neo4j_service = Neo4jService()
        if neo4j_service.is_connected():
            result = neo4j_service.clear_all_data()
            if result.get('success'):
                logger.info(f"✓ Cleared {result.get('deleted_nodes', 0)} nodes\n")
            else:
                logger.error(f"✗ Failed to clear data: {result.get('error')}\n")
                return
            neo4j_service.close()
        
        # Step 2: Import customers and meters from Excel
        print_banner("STEP 2: IMPORTING EXCEL DATA")
        logger.info("Importing customers and meters from Excel...\n")
        import_to_neo4j()
        
        # Step 3: Sync meter readings from Supabase
        print_banner("STEP 3: SYNCING METER READINGS")
        logger.info("Syncing meter readings from Supabase...\n")
        sync_readings()
        
        # Step 4: Sync bills from Supabase
        print_banner("STEP 4: SYNCING BILLS")
        logger.info("Syncing bills from Supabase...\n")
        sync_bills()
        
        # Step 5: Display final stats
        print_banner("MIGRATION COMPLETE")
        logger.info("Displaying final database statistics...\n")
        
        neo4j_service = Neo4jService()
        if neo4j_service.is_connected():
            display_stats(neo4j_service)
            neo4j_service.close()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"\n✓ Migration completed successfully!")
        logger.info(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Duration: {duration}")
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print_banner("DONE")

if __name__ == "__main__":
    print("\n" + "!" * 60)
    print("WARNING: This will DELETE ALL existing data in your Neo4j database!")
    print("!" * 60)
    
    response = input("\nAre you sure you want to proceed? Type 'YES' to confirm: ")
    if response == "YES":
        migrate_all_data()
    else:
        print("Operation cancelled.")
