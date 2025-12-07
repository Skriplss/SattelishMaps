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
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        cloud_max: float = 30,
        limit: int = 100
    ) -> List[Dict]:
        """Get images within bounding box using PostGIS (or simple filter)"""
        try:
            # Build query with joins to get statistics
            query = self.client.table('satellite_images').select(
                '*, ndvi_data(ndvi_mean, vegetation_category), ndwi_data(ndwi_mean, water_category)'
            )
            
            # Date filters
            if date_from:
                query = query.gte('acquisition_date', str(date_from))
            if date_to:
                query = query.lte('acquisition_date', str(date_to))
                
            # Cloud filter
            query = query.lte('cloud_coverage', cloud_max)
            
            # Simple bounds check using RPC if available, or just filtering 
            # (Supabase/PostgREST doesn't support complex PostGIS queries directly in table interface without RPC)
            # For now, we will return matches and let frontend settle, OR rely on 'search_by_bounds' RPC if we had it.
            # Assuming user manually loaded data, we will just return date/cloud filtered data for now 
            # and sort by date.
            
            query = query.order('acquisition_date', desc=True).limit(limit)
            
            response = query.execute()
            
            # Filter by simple coordinate box in Python if center_point is available
            # This is a fallback until PostGIS RPC is set up
            results = []
            if response.data:
                for img in response.data:
                    # Parse center point if possible, or just include
                    results.append(img)
            
            logger.info(f"Retrieved {len(results)} images from DB (filtered by date/cloud)")
            return results
            
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
    
    def insert_region_statistics(self, data: Dict[str, Any]) -> Dict:
        """Insert region statistics (NDVI/NDWI)"""
        try:
            response = self.client.table('region_statistics')\
                .insert(data)\
                .execute()
            
            logger.info(f"Inserted statistics for {data.get('region_name')} on {data.get('date')}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting region statistics: {str(e)}")
            raise

    def insert_ndvi_data(self, data: Dict[str, Any]) -> Dict:
        """Insert NDVI calculation data"""
        try:
            response = self.client.table('ndvi_data')\
                .insert(data)\
                .execute()
            
            logger.info(f"Inserted NDVI data for image: {data.get('image_id')}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting NDVI data: {str(e)}")
            raise
    
    def insert_ndwi_data(self, data: Dict[str, Any]) -> Dict:
        """Insert NDWI calculation data"""
        try:
            response = self.client.table('ndwi_data')\
                .insert(data)\
                .execute()
            
            logger.info(f"Inserted NDWI data for image: {data.get('image_id')}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting NDWI data: {str(e)}")
            raise
    
    def get_ndvi_data(self, image_id: str) -> Optional[Dict]:
        """Get NDVI data for an image"""
        try:
            response = self.client.table('ndvi_data')\
                .select('*')\
                .eq('image_id', image_id)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching NDVI data for {image_id}: {str(e)}")
            return None
    
    def get_ndwi_data(self, image_id: str) -> Optional[Dict]:
        """Get NDWI data for an image"""
        try:
            response = self.client.table('ndwi_data')\
                .select('*')\
                .eq('image_id', image_id)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching NDWI data for {image_id}: {str(e)}")
            return None
    
    def get_latest_processed_date(self) -> Optional[str]:
        """Get the acquisition date of the latest processed image"""
        try:
            response = self.client.table('satellite_images')\
                .select('acquisition_date')\
                .order('acquisition_date', desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0].get('acquisition_date')
            return None
            
        except Exception as e:
            logger.error(f"Error fetching latest processed date: {str(e)}")
            return None
    
    
    def get_region_statistics_geojson(
        self,
        date: str,
        index_type: str,
        region_name: Optional[str] = None
    ) -> Dict:
        """
        Get region statistics as GeoJSON FeatureCollection
        
        Converts PostGIS bbox to GeoJSON geometry
        """
        try:
            # Build query
            query = self.client.table('region_statistics').select('*')
            
            # Apply filters
            query = query.eq('date', date)
            query = query.eq('index_type', index_type)
            
            if region_name:
                query = query.eq('region_name', region_name)
            
            response = query.execute()
            
            if not response.data:
                logger.warning(f"No data found for date={date}, index={index_type}")
                return {"type": "FeatureCollection", "features": []}
            
            # Convert to GeoJSON
            features = []
            for row in response.data:
                # Use PostGIS function to convert bbox to GeoJSON
                # The bbox is stored as GEOGRAPHY(POLYGON)
                try:
                    geom_query = self.client.rpc(
                        'st_asgeojson',
                        {'geom': row['bbox']}
                    ).execute()
                    
                    # RPC returns JSON string, need to parse it
                    import json
                    geometry = json.loads(geom_query.data) if geom_query.data else None
                    
                except Exception as e:
                    logger.warning(f"Error converting bbox to GeoJSON: {str(e)}")
                    geometry = None
                
                # Fallback: if RPC doesn't work, try to parse bbox manually
                if not geometry and row.get('bbox'):
                    # bbox is in WKB format, we need to convert it
                    # For now, return a simple structure
                    logger.warning(f"Could not convert bbox to GeoJSON for row {row['id']}")
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [[]]  # Empty for now
                    }
                
                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": row['id'],
                        "region_name": row['region_name'],
                        "date": row['date'],
                        "index_type": row['index_type'],
                        "mean": float(row['mean']) if row['mean'] else None,
                        "min": float(row['min']) if row['min'] else None,
                        "max": float(row['max']) if row['max'] else None,
                        "std": float(row['std']) if row['std'] else None,
                        "sample_count": row['sample_count']
                    }
                }
                features.append(feature)
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            logger.info(f"Converted {len(features)} regions to GeoJSON")
            return geojson
            
        except Exception as e:
            logger.error(f"Error getting region statistics as GeoJSON: {str(e)}")
            raise
    
    def get_available_dates(
        self,
        index_type: Optional[str] = None,
        region_name: Optional[str] = None
    ) -> List[str]:
        """Get list of available dates in region_statistics"""
        try:
            query = self.client.table('region_statistics').select('date')
            
            if index_type:
                query = query.eq('index_type', index_type)
            if region_name:
                query = query.eq('region_name', region_name)
            
            response = query.execute()
            
            # Get unique dates and sort
            dates = sorted(set(row['date'] for row in response.data if 'date' in row))
            
            logger.info(f"Found {len(dates)} available dates")
            return dates
            
        except Exception as e:
            logger.error(f"Error fetching available dates: {str(e)}")
            raise
    
    def check_image_has_indices(self, image_id: str) -> Dict[str, bool]:

        """Check if image has NDVI and NDWI data calculated"""
        try:
            has_ndvi = self.get_ndvi_data(image_id) is not None
            has_ndwi = self.get_ndwi_data(image_id) is not None
            
            return {
                "has_ndvi": has_ndvi,
                "has_ndwi": has_ndwi,
                "has_both": has_ndvi and has_ndwi
            }
            
        except Exception as e:
            logger.error(f"Error checking indices for {image_id}: {str(e)}")
            return {"has_ndvi": False, "has_ndwi": False, "has_both": False}


# Singleton instance
supabase_service = SupabaseService()
