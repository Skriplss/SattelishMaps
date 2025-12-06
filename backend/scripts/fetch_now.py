
import asyncio
import logging
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import satellite_scheduler
from utils.logger import setup_logging

async def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("🛰️  STARTING MANUAL SATELLITE DATA FETCH")
    print("="*80 + "\n")
    
    try:
        # Force Trnava bounds for this run
        from config.settings import settings
        settings.DEFAULT_SEARCH_BOUNDS = "POLYGON((17.50 48.30, 17.70 48.30, 17.70 48.45, 17.50 48.45, 17.50 48.30))"
        
        # Run the fetch job (6 months history)
        await satellite_scheduler.fetch_and_process_sentinel_data(days_back=180)
        
        print("\n" + "="*80)
        print("✅  MANUAL FETCH COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error during manual fetch: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
