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
    def _get_region_name_from_bbox(bbox: List[float]) -> str:
        """
        Determine region name based on bbox coordinates
        Can be extended to support multiple regions
        """
        # For now the scheduler serves a single configured region.
        # Could later query a regions table or use reverse geocoding.
        return settings.DEFAULT_REGION_NAME
    
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

            self._save_statistics_to_db(stats, bbox)
            
            self.successful_runs += 1
            logger.info("✅ Scheduler job completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Scheduler job failed: {str(e)}", exc_info=True)
            self.failed_runs += 1
            
    def _save_statistics_to_db(self, stats: dict, bbox: List[float]):
        """
        Save statistical data to Supabase 'region_statistics' table
        (long format: one row per region + date + index_type).
        """
        # bbox = [min_lon, min_lat, max_lon, max_lat]
        polygon_ewkt = (
            f"SRID=4326;POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, "
            f"{bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
        )
        region_name = self._get_region_name_from_bbox(bbox)

        rows = []
        for index_type in ('NDVI', 'NDWI'):
            for stat in stats.get(index_type.lower(), []):
                rows.append({
                    "region_name": region_name,
                    "date": stat['date'].split('T')[0],
                    "index_type": index_type,
                    "bbox": polygon_ewkt,
                    "mean": stat.get('mean'),
                    "min": stat.get('min'),
                    "max": stat.get('max'),
                    "std": stat.get('stDev'),
                    "sample_count": stat.get('sample_count'),
                    "provider": "Sentinel Hub Statistical API"
                })

        try:
            count = supabase_service.upsert_region_statistics(rows)
            logger.info(f"Total rows saved: {count}")
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")

    async def cleanup_tile_cache(self, keep_days: int = 30):
        """Evict tiles that have not been accessed for keep_days"""
        try:
            response = supabase_service.client.rpc(
                'cleanup_tile_cache', {'p_keep_days': keep_days}
            ).execute()
            logger.info(f"Tile cache cleanup: removed {response.data} stale tiles")
        except Exception as e:
            logger.error(f"Tile cache cleanup failed: {e}")

    def get_status(self) -> dict:
        """Get scheduler status and statistics"""
        return {
            "enabled": settings.SCHEDULER_ENABLED,
            "running": self.is_running,
            "interval_hours": settings.SCHEDULER_INTERVAL_HOURS,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs
        }

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

            self.scheduler.add_job(
                self.cleanup_tile_cache,
                trigger=IntervalTrigger(hours=24),
                id='cleanup_tile_cache',
                name='Evict stale tiles from cache',
                replace_existing=True,
                max_instances=1
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
