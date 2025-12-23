"""
Automated Scheduler for Sentinel-2 Data Fetching and Processing

This scheduler automatically:
1. Fetches new Sentinel-2 statistics (NDVI, NDWI) from Sentinel Hub
2. Saves data to Supabase database

Runs periodically based on SCHEDULER_INTERVAL_HOURS setting.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
from shapely import wkt

from config.settings import settings
from services.sentinelhub_service import sentinelhub_service
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


class SatelliteDataScheduler:
    """Scheduler for automated satellite data processing"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
    
    @staticmethod
    def _parse_bbox(wkt_polygon: str) -> List[float]:
        """
        Parse WKT Polygon to BBox [min_lon, min_lat, max_lon, max_lat]
        """
        try:
            poly = wkt.loads(wkt_polygon)
            bounds = poly.bounds # (minx, miny, maxx, maxy)
            return list(bounds)
        except Exception as e:
            logger.error(f"Failed to parse search bounds: {e}")
            # Fallback (Central Europe approx) or raise
            raise
    
    async def fetch_and_process_sentinel_data(self, days_back: int = 1):
        """
        Main job: Fetch new Sentinel-2 statistics and save to DB
        """
        try:
            logger.info("=" * 80)
            logger.info("🛰️  Starting automated Sentinel-2 data fetch (Sentinel Hub)")
            logger.info("=" * 80)
            
            self.total_runs += 1
            self.last_run = datetime.now()
            
            # Determine date range
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days_back)
            
            time_interval = (date_from.isoformat(), date_to.isoformat())
            
            # Parse Bounds
            bbox = self._parse_bbox(settings.DEFAULT_SEARCH_BOUNDS)
            
            logger.info(f"Time Interval: {time_interval}")
            logger.info(f"BBox: {bbox}")
            
            # Fetch Statistics
            stats = sentinelhub_service.fetch_statistics(
                bbox_coords=bbox,
                time_interval=time_interval,
                aggregation_period="P1D"
            )
            
            if not stats['ndvi'] and not stats['ndwi']:
                logger.info("No data found for this interval.")
                self.successful_runs += 1
                return

            logger.info(f"Found {len(stats['ndvi'])} NDVI records and {len(stats['ndwi'])} NDWI records.")

            # Save to Supabase
            # Note: We need to adapt the data to the schema.
            # The schema expects 'satellite_images', 'ndvi_data', 'ndwi_data'.
            # 'satellite_images' usually requires a product_id. 
            # Sentinel Hub Statistical API returns aggregated stats, not single 'products'.
            # We might need to synthesize a 'product' or image entry for the day/interval.
            
            self._save_statistics_to_db(stats, bbox)
            
            self.successful_runs += 1
            logger.info("✅ Scheduler job completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Scheduler job failed: {str(e)}", exc_info=True)
            self.failed_runs += 1
            
    @staticmethod
    def _save_statistics_to_db(stats: dict, bbox: List[float]):
        """
        Save statistical data to Supabase 'region_statistics' table.
        """
        # Group by date
        dates = set()
        for item in stats.get('ndvi', []):
            dates.add(item['date'].split('T')[0])
            
        count = 0
        for date_str in dates:
            # Find stats for this date
            ndvi_stat = next((s for s in stats['ndvi'] if s['date'].startswith(date_str)), {})
            ndwi_stat = next((s for s in stats['ndwi'] if s['date'].startswith(date_str)), {})
            
            if not ndvi_stat and not ndwi_stat:
                continue
            
            # Create Polygon WKT for bbox
            #  = [min_lon, min_lat, max_lon, max_lat]
            polygon_wkt = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"

            # Prepare Data Entry
            entry = {
                "region_name": "Trnava", # TODO: Make dynamic if multiple regions
                "date": date_str,
                "bbox": polygon_wkt,
                
                # NDVI
                "ndvi_mean": ndvi_stat.get('mean'),
                "ndvi_min": ndvi_stat.get('min'),
                "ndvi_max": ndvi_stat.get('max'),
                "ndvi_std": ndvi_stat.get('stDev'),
                "ndvi_sample_count": ndvi_stat.get('sample_count'),
                
                # NDWI
                "ndwi_mean": ndwi_stat.get('mean'),
                "ndwi_min": ndwi_stat.get('min'),
                "ndwi_max": ndwi_stat.get('max'),
                "ndwi_std": ndwi_stat.get('stDev'),
                "ndwi_sample_count": ndwi_stat.get('sample_count'),
                
                "provider": "Sentinel Hub Statistical API"
            }
            
            # Insert
            # We use upsert if possible, or just insert. 
            # Sentinel Hub might return multiple entries for same day if orbits overlap? 
            # Usually one per day for aggregated.
            try:
                # Upsert based on region_name + date to avoid duplicates
                supabase_service.client.table('region_statistics').upsert(entry, on_conflict='region_name, date').execute()
                count += 1
                logger.info(f"Saved stats for {date_str}")
            except Exception as e:
                logger.error(f"Failed to save stats for {date_str}: {e}")
                
        logger.info(f"Total days saved: {count}")

    def start(self):
        """Start the scheduler"""
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled in settings")
            return
        
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            logger.info("🚀 Starting Satellite Data Scheduler")
            logger.info(f"   Interval: Every {settings.SCHEDULER_INTERVAL_HOURS} hours")
            
            self.scheduler = AsyncIOScheduler()
            
            # Add job with interval trigger
            self.scheduler.add_job(
                self.fetch_and_process_sentinel_data,
                trigger=IntervalTrigger(hours=settings.SCHEDULER_INTERVAL_HOURS),
                id='fetch_sentinel_data',
                name='Fetch and Process Sentinel-2 Data',
                replace_existing=True,
                max_instances=1  # Prevent concurrent runs
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Scheduler started successfully")
            
            # Run immediately on startup if configured
            if settings.PROCESS_HISTORICAL_DATA:
                logger.info("Running initial data fetch...")
                asyncio.create_task(self.fetch_and_process_sentinel_data())
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            logger.info("Stopping Satellite Data Scheduler...")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
            
            self.is_running = False
            logger.info("✅ Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            raise

# Singleton instance
satellite_scheduler = SatelliteDataScheduler()
