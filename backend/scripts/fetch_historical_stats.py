
import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging
from services.sentinelhub_service import sentinelhub_service
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

# Regions configuration (Approximate BBoxes)
REGIONS = {
    "Bratislava": [17.05, 48.10, 17.20, 48.20],
    "Kosice": [21.20, 48.65, 21.35, 48.75],
    "Zilina": [18.70, 49.18, 18.80, 49.25],
    "Banska Bystrica": [19.10, 48.70, 19.20, 48.78],
    "Presov": [21.20, 48.95, 21.30, 49.05]
}

async def fetch_and_save_stats(region_name: str, bbox: List[float]):
    logger.info(f"Processing region: {region_name}")
    
    # Time interval: Last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    time_interval = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    try:
        # Clear existing stats for this region to avoid duplicates
        logger.info(f"Cleaning up old stats for {region_name}...")
        supabase_service.client.table('region_statistics').delete().eq('region_name', region_name).execute()

        # Fetch stats from Sentinel Hub
        logger.info(f"Fetching stats for {region_name} from {time_interval[0]} to {time_interval[1]}")
        stats = sentinelhub_service.fetch_statistics(
            bbox_coords=bbox,
            time_interval=time_interval,
            resolution=100  # 100m resolution is enough for regional stats
        )
        
        # Save NDVI
        ndvi_data = stats.get("ndvi", [])
        logger.info(f"Found {len(ndvi_data)} NDVI records for {region_name}")
        
        for record in ndvi_data:
            supabase_service.insert_region_statistics({
                "region_name": region_name,
                "date": record["date"],
                "index_type": "NDVI",
                "mean": record["mean"],
                "min": record["min"],
                "max": record["max"],
                "std": record["stDev"],
                "sample_count": record["sample_count"],
                # "bbox": f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            })
            
        # Save NDWI
        ndwi_data = stats.get("ndwi", [])
        logger.info(f"Found {len(ndwi_data)} NDWI records for {region_name}")
        
        for record in ndvi_data: # TYPO DETECTED in previous thought process? No, using ndvi_data variable name by mistake? 
            # Using correct variable here:
            pass 

        for record in ndwi_data:
            supabase_service.insert_region_statistics({
                "region_name": region_name,
                "date": record["date"],
                "index_type": "NDWI",
                "mean": record["mean"],
                "min": record["min"],
                "max": record["max"],
                "std": record["stDev"],
                "sample_count": record["sample_count"]
            })
            
        logger.info(f"✅ Completed {region_name}")
        
    except Exception as e:
        logger.error(f"Failed to process {region_name}: {e}")

def main():
    setup_logging()
    
    logger.info("Starting historical statistics import...")
    
    # Check credentials
    if not os.getenv("SH_CLIENT_ID") or not os.getenv("SH_CLIENT_SECRET"):
        logger.error("Missing Sentinel Hub credentials!")
        return

    # Run loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for region, bbox in REGIONS.items():
        loop.run_until_complete(fetch_and_save_stats(region, bbox))
        
    logger.info("All regions processed.")

if __name__ == "__main__":
    main()
