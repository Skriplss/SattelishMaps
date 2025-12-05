"""
Enhanced Copernicus service for Sentinel-2 satellite data retrieval
"""
from sentinelsat import SentinelAPI
from config.settings import settings
from typing import List, Dict, Any, Tuple
from datetime import date, datetime
import logging
import time

logger = logging.getLogger(__name__)


class CopernicusService:
    """Production-ready Copernicus Sentinel-2 API client"""
    
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
            logger.info("Copernicus API client initialized for Sentinel-2")
        except Exception as e:
            logger.error(f"Failed to initialize Copernicus API: {str(e)}")
            self.api = None
    
    def search_sentinel2_products(
        self,
        area: str,
        date_range: Tuple[date, date],
        cloud_coverage_max: float = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for Sentinel-2 products
        
        Args:
            area: WKT polygon string
            date_range: Tuple of (start_date, end_date)
            cloud_coverage_max: Maximum cloud coverage percentage
            limit: Maximum number of results
        
        Returns:
            List of product dictionaries
        """
        if not self.api:
            logger.error("Copernicus API not initialized")
            return []
        
        try:
            logger.info(f"Searching Sentinel-2: {date_range[0]} to {date_range[1]}, cloud_max={cloud_coverage_max}")
            
            # Query with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    products = self.api.query(
                        area=area,
                        date=date_range,
                        platformname='Sentinel-2',
                        producttype='S2MSI2A',  # Level-2A products (atmospherically corrected)
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
            
            # Convert to list of dicts and limit results
            results = []
            for i, (product_id, product_info) in enumerate(products.items()):
                if i >= limit:
                    break
                    
                # Extract coordinates from footprint
                footprint = product_info.get('footprint', '')
                center_point = self._extract_center_from_footprint(footprint)
                
                results.append({
                    'product_id': product_id,
                    'title': product_info.get('title', ''),
                    'size': product_info.get('size', ''),
                    'acquisition_date': product_info.get('beginposition'),
                    'processing_date': product_info.get('ingestiondate'),
                    'cloud_coverage': float(product_info.get('cloudcoverpercentage', 0)),
                    'footprint': footprint,
                    'center_point': center_point,
                    'thumbnail_url': f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{product_id}')/Products('Quicklook')/$value",
                    'download_url': f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{product_id}')/$value",
                    'platform': product_info.get('platformname', 'Sentinel-2'),
                    'metadata': {
                        'orbitnumber': product_info.get('orbitnumber'),
                        'relativeorbitnumber': product_info.get('relativeorbitnumber'),
                        'processinglevel': product_info.get('processinglevel'),
                        'producttype': product_info.get('producttype')
                    }
                })
            
            logger.info(f"Found {len(results)} Sentinel-2 products")
            return results
            
        except Exception as e:
            logger.error(f"Error searching Copernicus: {str(e)}")
            raise
    
    def _extract_center_from_footprint(self, footprint: str) -> Dict[str, float]:
        """Extract center point from WKT footprint"""
        try:
            # Simple center calculation from POLYGON
            if 'POLYGON' in footprint:
                coords = footprint.replace('POLYGON((', '').replace('))', '').split(',')
                lats = []
                lons = []
                for coord in coords:
                    lon, lat = coord.strip().split()
                    lats.append(float(lat))
                    lons.append(float(lon))
                
                return {
                    'lat': sum(lats) / len(lats),
                    'lon': sum(lons) / len(lons)
                }
        except Exception as e:
            logger.warning(f"Failed to extract center point: {str(e)}")
        
        return {'lat': 0, 'lon': 0}
    
    def save_to_supabase(self, products: List[Dict[str, Any]]) -> int:
        """
        Save Sentinel-2 products to Supabase
        
        Args:
            products: List of product dictionaries
        
        Returns:
            Number of products saved
        """
        from services.supabase_service import supabase_service
        
        saved_count = 0
        for product in products:
            try:
                # Prepare data for Supabase
                data = {
                    'product_id': product['product_id'],
                    'title': product['title'],
                    'acquisition_date': product['acquisition_date'].isoformat() if isinstance(product['acquisition_date'], datetime) else product['acquisition_date'],
                    'processing_date': product.get('processing_date').isoformat() if product.get('processing_date') and isinstance(product.get('processing_date'), datetime) else None,
                    'cloud_coverage': product['cloud_coverage'],
                    'thumbnail_url': product['thumbnail_url'],
                    'download_url': product['download_url'],
                    'metadata': product.get('metadata', {})
                }
                
                # Add center point in PostGIS format
                if product.get('center_point'):
                    cp = product['center_point']
                    data['center_point'] = f"POINT({cp['lon']} {cp['lat']})"
                
                # Save to Supabase
                supabase_service.insert_satellite_image(data)
                saved_count += 1
                logger.info(f"Saved product {product['product_id']} to Supabase")
                
            except Exception as e:
                logger.error(f"Failed to save product {product.get('product_id')}: {str(e)}")
                continue
        
        logger.info(f"Saved {saved_count}/{len(products)} products to Supabase")
        return saved_count
    
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
