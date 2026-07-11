"""
Script to fetch and store pixel data from Sentinel Hub

Usage:
    python -m scripts.fetch_pixel_data --bbox "19.5,48.5,19.7,48.7" --date "2024-12-05"
"""
import asyncio
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tile_cache_service import tile_cache_service
from utils.logger import setup_logging

logger = setup_logging(log_level="INFO")


async def main():
    parser = argparse.ArgumentParser(description='Fetch pixel data from Sentinel Hub')
    parser.add_argument('--bbox', required=True, help='Bounding box: min_lon,min_lat,max_lon,max_lat')
    parser.add_argument('--date', required=True, help='Date in YYYY-MM-DD format')
    parser.add_argument('--resolution', type=int, default=100, help='Grid resolution (default: 100)')
    
    args = parser.parse_args()
    
    # Parse bbox
    try:
        bbox_parts = [float(x.strip()) for x in args.bbox.split(',')]
        if len(bbox_parts) != 4:
            raise ValueError("bbox must have 4 values")
        
        min_lon, min_lat, max_lon, max_lat = bbox_parts
        
    except Exception as e:
        logger.error(f"Invalid bbox format: {e}")
        logger.error("Expected format: min_lon,min_lat,max_lon,max_lat")
        logger.error("Example: 19.5,48.5,19.7,48.7")
        return
    
    logger.info("Fetching pixel data for:")
    logger.info(f"  Area: [{min_lon}, {min_lat}] to [{max_lon}, {max_lat}]")
    logger.info(f"  Date: {args.date}")
    logger.info(f"  Resolution: {args.resolution}x{args.resolution}")
    
    try:
        result = await tile_cache_service.fetch_and_store_pixel_data(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            date=args.date,
            resolution=args.resolution
        )
        
        logger.info("=" * 60)
        logger.info("RESULT:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Pixels stored: {result['pixels_stored']}")
        logger.info(f"  Resolution: {result.get('resolution', 'N/A')}")
        logger.info(f"  Indices: {', '.join(result.get('indices', []))}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
