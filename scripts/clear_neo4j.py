import sys
import os
import logging

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neo4j_service import Neo4jService
from utils.logger import setup_logger

logger = setup_logger('clear_neo4j')

def clear_all_neo4j_data():
    """
    Clear ALL data from Neo4j database
    WARNING: This is irreversible!
    """
    logger.info("=" * 60)
    logger.info("CLEARING ALL NEO4J DATA")
    logger.info("=" * 60)
    
    # Initialize Neo4j service
    try:
        neo4j_service = Neo4jService()
        
        if not neo4j_service.is_connected():
            logger.error("Could not connect to Neo4j. Please check your configuration.")
            return
            
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j service: {e}")
        return
    
    # Get stats before clearing
    try:
        logger.info("Getting current database statistics...")
        stats_before = neo4j_service.get_all_stats()
        
        if 'error' not in stats_before:
            logger.info("Current database state:")
            logger.info(f"  Customers: {stats_before['nodes']['customers']}")
            logger.info(f"  Meters: {stats_before['nodes']['meters']}")
            logger.info(f"  Readings: {stats_before['nodes']['readings']}")
            logger.info(f"  Bills: {stats_before['nodes']['bills']}")
            logger.info(f"  Tariffs: {stats_before['nodes']['tariffs']}")
            logger.info(f"  Total nodes: {sum(stats_before['nodes'].values())}")
    except Exception as e:
        logger.warning(f"Could not get stats before clearing: {e}")
    
    # Clear all data
    try:
        logger.info("\nClearing all data from Neo4j...")
        result = neo4j_service.clear_all_data()
        
        if result.get('success'):
            logger.info("✓ Data cleared successfully!")
            logger.info(f"  Deleted nodes: {result.get('deleted_nodes', 0)}")
        else:
            logger.error(f"✗ Failed to clear data: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Unexpected error during clearing: {e}")
    finally:
        neo4j_service.close()
    
    logger.info("=" * 60)
    logger.info("CLEARING COMPLETED")
    logger.info("=" * 60)

if __name__ == "__main__":
    import warnings
    warnings.warn("WARNING: This will delete ALL data from your Neo4j database!")
    
    # Simple confirmation
    response = input("\nAre you sure you want to clear ALL Neo4j data? Type 'YES' to confirm: ")
    if response == "YES":
        clear_all_neo4j_data()
    else:
        print("Operation cancelled.")
