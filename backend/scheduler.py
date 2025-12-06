"""
Automated Scheduler for Sentinel-2 Data Fetching and Processing

This scheduler automatically:
1. Searches for new Sentinel-2 images from Copernicus
2. Calculates NDVI and NDWI indices
3. Saves data to Supabase database

Runs periodically based on SCHEDULER_INTERVAL_HOURS setting.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from config.settings import settings
from services.copernicus_service import copernicus_service
from services.supabase_service import supabase_service
from services.ndvi_calculator import ndvi_calculator
from services.ndwi_calculator import ndwi_calculator

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
    
    async def fetch_and_process_sentinel_data(self):
        """
        Main job: Fetch new Sentinel-2 data and calculate indices
        """
        try:
            logger.info("=" * 80)
            logger.info("🛰️  Starting automated Sentinel-2 data fetch and processing")
            logger.info("=" * 80)
            
            self.total_runs += 1
            self.last_run = datetime.now()
            
            # Check if Copernicus API is available
            if not copernicus_service.is_available():
                logger.warning("Copernicus API not configured - skipping fetch")
                return
            
            # Determine date range for search
            latest_date = supabase_service.get_latest_processed_date()
            
            if latest_date and not settings.PROCESS_HISTORICAL_DATA:
                # Search from latest processed date to now
                date_from = datetime.fromisoformat(latest_date.replace('Z', '+00:00')).date()
                logger.info(f"Searching for new data since: {date_from}")
            else:
                # Search last 7 days
                date_from = (datetime.now() - timedelta(days=7)).date()
                logger.info(f"Searching last 7 days from: {date_from}")
            
            date_to = datetime.now().date()
            
            # Search for Sentinel-2 products
            logger.info(f"Searching Copernicus: {date_from} to {date_to}")
            logger.info(f"Bounds: {settings.DEFAULT_SEARCH_BOUNDS}")
            logger.info(f"Max cloud coverage: {settings.DEFAULT_CLOUD_MAX}%")
            
            products = copernicus_service.search_sentinel2_products(
                area=settings.DEFAULT_SEARCH_BOUNDS,
                date_range=(date_from, date_to),
                cloud_coverage_max=settings.DEFAULT_CLOUD_MAX,
                limit=20
            )
            
            if not products:
                logger.info("No new products found")
                self.successful_runs += 1
                return
            
            logger.info(f"Found {len(products)} new Sentinel-2 products")
            
            # Save products to database
            saved_count = copernicus_service.save_to_supabase(products)
            logger.info(f"Saved {saved_count} products to database")
            
            # Process each saved product
            processed_count = 0
            for product in products:
                try:
                    # Get the saved image from database
                    image_data = supabase_service.client.table('satellite_images')\
                        .select('*')\
                        .eq('product_id', product['product_id'])\
                        .single()\
                        .execute()
                    
                    if not image_data.data:
                        logger.warning(f"Image not found in DB: {product['product_id']}")
                        continue
                    
                    image_id = image_data.data['id']
                    
                    # Check if indices already calculated
                    indices_status = supabase_service.check_image_has_indices(image_id)
                    if indices_status['has_both']:
                        logger.info(f"Indices already calculated for {product['product_id']}")
                        continue
                    
                    # Calculate NDVI
                    if not indices_status['has_ndvi']:
                        logger.info(f"Calculating NDVI for {product['product_id']}")
                        ndvi_data = ndvi_calculator.calculate_ndvi_from_metadata(
                            image_id=image_id,
                            product_id=product['product_id'],
                            cloud_coverage=product['cloud_coverage'],
                            center_point=product.get('center_point')
                        )
                        supabase_service.insert_ndvi_data(ndvi_data)
                    
                    # Calculate NDWI
                    if not indices_status['has_ndwi']:
                        logger.info(f"Calculating NDWI for {product['product_id']}")
                        ndwi_data = ndwi_calculator.calculate_ndwi_from_metadata(
                            image_id=image_id,
                            product_id=product['product_id'],
                            cloud_coverage=product['cloud_coverage'],
                            center_point=product.get('center_point')
                        )
                        supabase_service.insert_ndwi_data(ndwi_data)
                    
                    processed_count += 1
                    logger.info(f"✅ Processed {product['product_id']}")
                    
                except Exception as e:
                    logger.error(f"Error processing product {product.get('product_id')}: {str(e)}")
                    continue
            
            logger.info("=" * 80)
            logger.info(f"✅ Scheduler job completed successfully")
            logger.info(f"   Products found: {len(products)}")
            logger.info(f"   Products saved: {saved_count}")
            logger.info(f"   Products processed: {processed_count}")
            logger.info("=" * 80)
            
            self.successful_runs += 1
            
        except Exception as e:
            logger.error(f"❌ Scheduler job failed: {str(e)}", exc_info=True)
            self.failed_runs += 1
    
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
            logger.info(f"   Search bounds: {settings.DEFAULT_SEARCH_BOUNDS}")
            logger.info(f"   Max cloud coverage: {settings.DEFAULT_CLOUD_MAX}%")
            
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
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        next_run = None
        if self.scheduler and self.is_running:
            job = self.scheduler.get_job('fetch_sentinel_data')
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        
        return {
            "enabled": settings.SCHEDULER_ENABLED,
            "running": self.is_running,
            "interval_hours": settings.SCHEDULER_INTERVAL_HOURS,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": next_run,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "search_bounds": settings.DEFAULT_SEARCH_BOUNDS,
            "max_cloud_coverage": settings.DEFAULT_CLOUD_MAX
        }


# Singleton instance
satellite_scheduler = SatelliteDataScheduler()
