"""
Enhanced Copernicus service for satellite data retrieval
"""
from sentinelsat import SentinelAPI
from config.settings import settings
from typing import List, Dict, Any, Tuple
from datetime import date
import logging
import time

logger = logging.getLogger(__name__)


class CopernicusService:
    """Production-ready Copernicus Sentinel API client"""
    
    def __init__(self):
        try:
            if not settings.COPERNICUS_USERNAME or not settings.COPERNICUS_PASSWORD:
                logger.warning("Copernicus credentials not configured")
                self.api = None
                return
            
            self.api = SentinelAPI(
                settings.COPERNICUS_USERNAME,
                settings.COPERNICUS_PASSWORD,
                'https://scihub.copernicus.eu/dhus'
            )
            logger.info("Copernicus API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Copernicus API: {str(e)}")
            self.api = None
    
    def search_products(
        self,
        area: str,
        date_range: Tuple[date, date],
        cloud_coverage_max: float = 30,
        platform: str = 'Sentinel-2'
    ) -> List[Dict[str, Any]]:
        """
        Search for satellite products with retry logic
        
        Args:
            area: WKT polygon string
            date_range: Tuple of (start_date, end_date)
            cloud_coverage_max: Maximum cloud coverage percentage
            platform: Satellite platform name
        
        Returns:
            List of product dictionaries
        """
        if not self.api:
            logger.error("Copernicus API not initialized")
            return []
        
        try:
            logger.info(f"Searching Copernicus: {date_range[0]} to {date_range[1]}, cloud_max={cloud_coverage_max}")
            
            # Query with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    products = self.api.query(
                        area=area,
                        date=date_range,
                        platformname=platform,
                        cloudcoverpercentage=(0, cloud_coverage_max)
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Copernicus API error, retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise
            
            # Convert to list of dicts
            results = []
            for product_id, product_info in products.items():
                results.append({
                    'product_id': product_id,
                    'title': product_info.get('title', ''),
                    'size': product_info.get('size', ''),
                    'acquisition_date': product_info.get('beginposition'),
                    'cloud_coverage': product_info.get('cloudcoverpercentage', 0),
                    'footprint': product_info.get('footprint', ''),
                    'download_url': f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{product_id}')/$value",
                    'thumbnail_url': f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{product_id}')/Products('Quicklook')/$value"
                })
            
            logger.info(f"Found {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"Error searching Copernicus: {str(e)}")
            raise
    
    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """Get detailed product information"""
        if not self.api:
            raise Exception("Copernicus API not initialized")
        
        try:
            product_info = self.api.get_product_odata(product_id)
            logger.info(f"Retrieved info for product: {product_id}")
            return product_info
        except Exception as e:
            logger.error(f"Error getting product info for {product_id}: {str(e)}")
            raise
    
    def download_product(
        self,
        product_id: str,
        directory_path: str = './downloads'
    ) -> Dict[str, Any]:
        """Download satellite product"""
        if not self.api:
            raise Exception("Copernicus API not initialized")
        
        try:
            logger.info(f"Downloading product: {product_id}")
            result = self.api.download(product_id, directory_path=directory_path)
            logger.info(f"Download completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error downloading product {product_id}: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if Copernicus API is available"""
        return self.api is not None


# Singleton instance
copernicus_service = CopernicusService()
