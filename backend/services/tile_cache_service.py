"""
Service for tile caching and pixel data management
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import math

from services.supabase_service import supabase_service
from services.sentinel_hub_wms_service import sentinel_hub_wms_service

logger = logging.getLogger(__name__)


class TileCacheService:
    """Service for managing tile cache and pixel data"""
    
    @staticmethod
    def tile_to_bbox(z: int, x: int, y: int) -> list[float]:
        """Convert XYZ tile coordinates to lat/lon bbox"""
        n = 2.0 ** z
        lon_min = x / n * 360.0 - 180.0
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        lon_max = (x + 1) / n * 360.0 - 180.0
        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        return [lon_min, lat_min, lon_max, lat_max]
    
    async def get_cached_tile(
        self,
        z: int,
        x: int,
        y: int,
        date: str,
        index_type: str
    ) -> Optional[bytes]:
        """Get tile from cache if exists"""
        try:
            response = supabase_service.client.table('tile_cache')\
                .select('tile_data')\
                .eq('z', z)\
                .eq('x', x)\
                .eq('y', y)\
                .eq('date', date)\
                .eq('index_type', index_type)\
                .single()\
                .execute()
            
            if response.data:
                # Update access stats
                supabase_service.client.table('tile_cache')\
                    .update({
                        'accessed_at': datetime.now().isoformat(),
                        'access_count': response.data.get('access_count', 0) + 1
                    })\
                    .eq('z', z)\
                    .eq('x', x)\
                    .eq('y', y)\
                    .eq('date', date)\
                    .eq('index_type', index_type)\
                    .execute()
                
                return response.data['tile_data']
            
            return None
            
        except Exception as e:
            logger.warning(f"Tile not in cache: {e}")
            return None
    
    async def cache_tile(
        self,
        z: int,
        x: int,
        y: int,
        date: str,
        index_type: str
    ) -> Dict[str, Any]:
        """Fetch tile from Sentinel Hub and cache it"""
        try:
            # Get bbox for tile
            bbox = self.tile_to_bbox(z, x, y)
            
            # Fetch tile from Sentinel Hub
            tile_data = sentinel_hub_wms_service.get_image(
                bbox=bbox,
                date=date,
                index_type=index_type,
                width=256,
                height=256
            )
            
            # Create bbox polygon WKT
            bbox_wkt = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            
            # Save to database
            supabase_service.client.table('tile_cache').upsert({
                'z': z,
                'x': x,
                'y': y,
                'date': date,
                'index_type': index_type,
                'bbox': bbox_wkt,
                'tile_data': tile_data,
                'created_at': datetime.now().isoformat(),
                'accessed_at': datetime.now().isoformat(),
                'access_count': 1
            }, on_conflict='z,x,y,date,index_type').execute()
            
            logger.info(f"Cached tile: z={z}, x={x}, y={y}, date={date}, index={index_type}")
            
            return {
                "cached": True,
                "z": z,
                "x": x,
                "y": y,
                "date": date,
                "index_type": index_type
            }
            
        except Exception as e:
            logger.error(f"Error caching tile: {str(e)}")
            raise
    
    async def get_area_statistics(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        date: str,
        index_type: str
    ) -> Dict[str, Any]:
        """Get aggregated statistics for an area from pixel data"""
        try:
            # Call PostgreSQL function
            response = supabase_service.client.rpc(
                'get_area_pixel_stats',
                {
                    'p_min_lon': min_lon,
                    'p_min_lat': min_lat,
                    'p_max_lon': max_lon,
                    'p_max_lat': max_lat,
                    'p_date': date,
                    'p_index_type': index_type
                }
            ).execute()
            
            if response.data and len(response.data) > 0:
                stats = response.data[0]
                return {
                    "mean": float(stats['mean_value']) if stats['mean_value'] else None,
                    "min": float(stats['min_value']) if stats['min_value'] else None,
                    "max": float(stats['max_value']) if stats['max_value'] else None,
                    "std": float(stats['std_value']) if stats['std_value'] else None,
                    "pixel_count": int(stats['pixel_count']) if stats['pixel_count'] else 0,
                    "area": {
                        "min_lon": min_lon,
                        "min_lat": min_lat,
                        "max_lon": max_lon,
                        "max_lat": max_lat
                    }
                }
            
            return {
                "mean": None,
                "min": None,
                "max": None,
                "std": None,
                "pixel_count": 0,
                "message": "No pixel data available for this area"
            }
            
        except Exception as e:
            logger.error(f"Error getting area statistics: {str(e)}")
            raise


# Singleton
tile_cache_service = TileCacheService()
