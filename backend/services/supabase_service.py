"""
Enhanced Supabase service for database operations
"""
from supabase import create_client, Client
from config.settings import settings
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Production-ready Supabase service"""
    
    def __init__(self):
        try:
            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def get_satellite_images(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        cloud_max: Optional[float] = None,
        platform: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Get satellite images with filters and pagination
        
        Returns: (data, total_count)
        """
        try:
            # Build query
            query = self.client.table('satellite_images').select('*', count='exact')
            
            # Apply filters
            if date_from:
                query = query.gte('acquisition_date', date_from)
            if date_to:
                query = query.lte('acquisition_date', date_to)
            if cloud_max is not None:
                query = query.lte('cloud_coverage', cloud_max)
            if platform:
                query = query.eq('platform', platform)
            
            # Get total count
            count_response = query.execute()
            total = count_response.count if hasattr(count_response, 'count') else 0
            
            # Apply pagination and ordering
            offset = (page - 1) * limit
            query = query.order('acquisition_date', desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            
            logger.info(f"Retrieved {len(response.data)} satellite images (total: {total})")
            return response.data, total
            
        except Exception as e:
            logger.error(f"Error fetching satellite images: {str(e)}")
            raise
    
    def get_satellite_image_by_id(self, image_id: str) -> Optional[Dict]:
        """Get single satellite image by ID"""
        try:
            response = self.client.table('satellite_images')\
                .select('*')\
                .eq('id', image_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching image {image_id}: {str(e)}")
            return None
    
    def insert_satellite_image(self, data: Dict[str, Any]) -> Dict:
        """Insert new satellite image"""
        try:
            response = self.client.table('satellite_images')\
                .insert(data)\
                .execute()
            
            logger.info(f"Inserted satellite image: {data.get('product_id')}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting satellite image: {str(e)}")
            raise
    
    def delete_satellite_image(self, image_id: str) -> bool:
        """Delete satellite image by ID"""
        try:
            response = self.client.table('satellite_images')\
                .delete()\
                .eq('id', image_id)\
                .execute()
            
            success = len(response.data) > 0
            if success:
                logger.info(f"Deleted satellite image: {image_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting image {image_id}: {str(e)}")
            raise
    
    def get_images_in_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        cloud_max: float = 30,
        limit: int = 10
    ) -> List[Dict]:
        """Get images within bounding box using PostGIS"""
        try:
            # For MVP, we'll use simple lat/lon filtering
            # In production, use PostGIS ST_Within for proper spatial queries
            response = self.client.table('satellite_images')\
                .select('*')\
                .lte('cloud_coverage', cloud_max)\
                .limit(limit)\
                .execute()
            
            # TODO: Add proper PostGIS spatial query when location field is properly set
            logger.info(f"Retrieved {len(response.data)} images in bounds")
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching images in bounds: {str(e)}")
            raise
    
    def get_statistics(self, image_id: str) -> Optional[Dict]:
        """Get statistics for an image"""
        try:
            response = self.client.table('statistics')\
                .select('*')\
                .eq('image_id', image_id)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching statistics for {image_id}: {str(e)}")
            return None
    
    def insert_statistics(self, data: Dict[str, Any]) -> Dict:
        """Insert statistics for an image"""
        try:
            response = self.client.table('statistics')\
                .insert(data)\
                .execute()
            
            logger.info(f"Inserted statistics for image: {data.get('image_id')}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting statistics: {str(e)}")
            raise
    
    def get_timeseries_data(
        self,
        area_name: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 30
    ) -> List[Dict]:
        """Get time series data for an area"""
        try:
            query = self.client.table('satellite_images')\
                .select('acquisition_date, cloud_coverage')\
                .order('acquisition_date', desc=False)\
                .limit(limit)
            
            if date_from:
                query = query.gte('acquisition_date', str(date_from))
            if date_to:
                query = query.lte('acquisition_date', str(date_to))
            
            response = query.execute()
            
            logger.info(f"Retrieved {len(response.data)} time series points")
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching time series: {str(e)}")
            raise
    
    def get_area_summary(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict:
        """Get summary statistics for an area"""
        try:
            # For MVP, return basic aggregated data
            query = self.client.table('satellite_images').select('*')
            
            if date_from:
                query = query.gte('acquisition_date', str(date_from))
            if date_to:
                query = query.lte('acquisition_date', str(date_to))
            
            response = query.execute()
            data = response.data
            
            if not data:
                return {
                    "total_images": 0,
                    "average_cloud_coverage": 0,
                    "date_range": None
                }
            
            # Calculate summary
            total = len(data)
            avg_cloud = sum(img.get('cloud_coverage', 0) for img in data) / total if total > 0 else 0
            
            dates = [img['acquisition_date'] for img in data if 'acquisition_date' in img]
            date_range = {
                "start": min(dates) if dates else None,
                "end": max(dates) if dates else None
            }
            
            summary = {
                "total_images": total,
                "average_cloud_coverage": round(avg_cloud, 2),
                "date_range": date_range,
                "vegetation_health": "moderate"  # TODO: Calculate from NDVI
            }
            
            logger.info(f"Generated area summary: {total} images")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating area summary: {str(e)}")
            raise


# Singleton instance
supabase_service = SupabaseService()
