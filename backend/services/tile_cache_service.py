"""
Service for tile caching and pixel data management
"""
import asyncio
import base64
import logging
from typing import Dict, Any, Optional
import math

import numpy as np

from services.supabase_service import supabase_service
from services.sentinel_hub_wms_service import sentinel_hub_wms_service
from services.pixel_tile_renderer import render_grid_to_png

logger = logging.getLogger(__name__)

# Grid side for DB-rendered tiles; 4096 cells max per tile
PIXEL_TILE_GRID = 64
# Minimum populated cells to consider a DB-rendered tile meaningful
PIXEL_TILE_MIN_CELLS = 4


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
        """
        Get tile from cache if it exists (bumps access stats atomically).
        Returns PNG bytes or None on cache miss.
        """
        try:
            response = supabase_service.client.rpc(
                'get_cached_tile',
                {'p_z': z, 'p_x': x, 'p_y': y, 'p_date': date, 'p_index_type': index_type}
            ).execute()

            if response.data:
                return base64.b64decode(response.data)
            return None

        except Exception as e:
            logger.warning(f"Tile cache lookup failed: {e}")
            return None

    async def store_tile(
        self,
        z: int,
        x: int,
        y: int,
        date: str,
        index_type: str,
        tile_data: bytes
    ) -> None:
        """Store already-fetched tile bytes in the cache"""
        supabase_service.client.table('tile_cache').upsert({
            'z': z,
            'x': x,
            'y': y,
            'date': date,
            'index_type': index_type,
            'tile_data': base64.b64encode(tile_data).decode('ascii')
        }, on_conflict='z,x,y,date,index_type').execute()

        logger.info(f"Cached tile: z={z}, x={x}, y={y}, date={date}, index={index_type}")

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
            bbox = self.tile_to_bbox(z, x, y)

            tile_data = sentinel_hub_wms_service.get_image(
                bbox=bbox,
                date=date,
                index_type=index_type,
                width=256,
                height=256
            )

            await self.store_tile(z, x, y, date, index_type, tile_data)

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
                    "mean": float(stats['mean_value']) if stats['mean_value'] is not None else None,
                    "min": float(stats['min_value']) if stats['min_value'] is not None else None,
                    "max": float(stats['max_value']) if stats['max_value'] is not None else None,
                    "std": float(stats['std_value']) if stats['std_value'] is not None else None,
                    "median": float(stats['median_value']) if stats['median_value'] is not None else None,
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
                "median": None,
                "pixel_count": 0,
                "message": "No pixel data available for this area"
            }

        except Exception as e:
            logger.error(f"Error getting area statistics: {str(e)}")
            raise

    async def get_area_timeseries(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        index_type: str,
        date_from: str,
        date_to: str
    ) -> list[Dict[str, Any]]:
        """Get per-date aggregates for an area from pixel data (for charts)"""
        try:
            response = supabase_service.client.rpc(
                'get_area_pixel_timeseries',
                {
                    'p_min_lon': min_lon,
                    'p_min_lat': min_lat,
                    'p_max_lon': max_lon,
                    'p_max_lat': max_lat,
                    'p_index_type': index_type,
                    'p_date_from': date_from,
                    'p_date_to': date_to
                }
            ).execute()

            return [
                {
                    "date": row['date'],
                    "mean": row['mean_value'],
                    "min": row['min_value'],
                    "max": row['max_value'],
                    "pixel_count": row['pixel_count']
                }
                for row in (response.data or [])
            ]

        except Exception as e:
            logger.error(f"Error getting area timeseries: {str(e)}")
            raise

    async def get_area_histogram(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        date: str,
        index_type: str,
        bins: int = 20
    ) -> list[Dict[str, Any]]:
        """Get value distribution for an area on a given date"""
        try:
            response = supabase_service.client.rpc(
                'get_area_pixel_histogram',
                {
                    'p_min_lon': min_lon,
                    'p_min_lat': min_lat,
                    'p_max_lon': max_lon,
                    'p_max_lat': max_lat,
                    'p_date': date,
                    'p_index_type': index_type,
                    'p_bins': bins
                }
            ).execute()

            return [
                {
                    "range_min": row['range_min'],
                    "range_max": row['range_max'],
                    "count": row['count']
                }
                for row in (response.data or [])
            ]

        except Exception as e:
            logger.error(f"Error getting area histogram: {str(e)}")
            raise

    async def get_area_change(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        date_a: str,
        date_b: str,
        index_type: str,
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Compare pixel values between two dates over an area.

        Pixels are matched on exact coordinates, so both dates should be
        fetched with the same bbox and resolution.
        """
        try:
            response = supabase_service.client.rpc(
                'get_area_pixel_change',
                {
                    'p_min_lon': min_lon,
                    'p_min_lat': min_lat,
                    'p_max_lon': max_lon,
                    'p_max_lat': max_lat,
                    'p_date_a': date_a,
                    'p_date_b': date_b,
                    'p_index_type': index_type,
                    'p_threshold': threshold
                }
            ).execute()

            if response.data and len(response.data) > 0:
                row = response.data[0]
                return {
                    "date_a": date_a,
                    "date_b": date_b,
                    "mean_a": float(row['mean_a']) if row['mean_a'] is not None else None,
                    "mean_b": float(row['mean_b']) if row['mean_b'] is not None else None,
                    "mean_diff": float(row['mean_diff']) if row['mean_diff'] is not None else None,
                    "improved_count": int(row['improved_count'] or 0),
                    "declined_count": int(row['declined_count'] or 0),
                    "stable_count": int(row['stable_count'] or 0),
                    "pixel_count": int(row['pixel_count'] or 0),
                    "threshold": threshold
                }

            return {
                "date_a": date_a,
                "date_b": date_b,
                "pixel_count": 0,
                "message": "No matching pixel data for both dates"
            }

        except Exception as e:
            logger.error(f"Error getting area change: {str(e)}")
            raise

    async def render_tile_from_pixels(
        self,
        z: int,
        x: int,
        y: int,
        date: str,
        index_type: str
    ) -> Optional[bytes]:
        """
        Render a map tile directly from stored pixel_data.

        Returns PNG bytes, or None when the tile has too little data
        to be meaningful.
        """
        try:
            bbox = self.tile_to_bbox(z, x, y)

            response = supabase_service.client.rpc(
                'get_pixel_grid',
                {
                    'p_min_lon': bbox[0],
                    'p_min_lat': bbox[1],
                    'p_max_lon': bbox[2],
                    'p_max_lat': bbox[3],
                    'p_date': date,
                    'p_index_type': index_type,
                    'p_grid': PIXEL_TILE_GRID
                }
            ).execute()

            cells = response.data or []
            if len(cells) < PIXEL_TILE_MIN_CELLS:
                return None

            grid = np.full((PIXEL_TILE_GRID, PIXEL_TILE_GRID), np.nan)
            for cell in cells:
                grid[cell['gy'], cell['gx']] = cell['value']

            # gy grows with latitude (south → north); image row 0 is north
            grid = np.flipud(grid)

            return render_grid_to_png(grid, index_type)

        except Exception as e:
            logger.warning(f"Pixel tile render failed for z={z}/{x}/{y}: {e}")
            return None

    async def fetch_and_store_pixel_data(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        date: str,
        index_types: Optional[list[str]] = None,
        resolution: int = 100
    ) -> Dict[str, Any]:
        """
        Получить пиксельные данные из Sentinel Hub и сохранить в БД

        Args:
            min_lon, min_lat, max_lon, max_lat: границы области
            date: дата в формате YYYY-MM-DD
            index_types: список индексов для загрузки (по умолчанию все)
            resolution: размер сетки (100x100 пикселей по умолчанию)

        Returns:
            Статистика сохраненных данных
        """
        try:
            if index_types is None:
                index_types = ['NDVI', 'NDWI', 'NDBI', 'MOISTURE']

            bbox = [min_lon, min_lat, max_lon, max_lat]

            # Прогреваем OAuth-токен до параллельных запросов
            sentinel_hub_wms_service.get_access_token()

            # Индексы тянем параллельно — 4 последовательных запроса
            # к Sentinel Hub превращаются в один раунд
            logger.info(f"Fetching pixel data for {', '.join(index_types)} in parallel...")
            results = await asyncio.gather(*[
                asyncio.to_thread(
                    sentinel_hub_wms_service.get_pixel_values,
                    bbox=bbox,
                    date=date,
                    index_type=index_type,
                    width=resolution,
                    height=resolution
                )
                for index_type in index_types
            ])

            values_by_index = {}
            valid_by_index = {}

            for index_type, result in zip(index_types, results):
                values = np.asarray(result['values'], dtype=np.float64)
                mask = result['mask']
                valid = np.isfinite(values)
                if mask is not None:
                    valid &= np.asarray(mask) > 0

                values_by_index[index_type.lower()] = values
                valid_by_index[index_type.lower()] = valid

            height, width = values_by_index[index_types[0].lower()].shape

            # Координаты центров пикселей (Y идет сверху вниз)
            lon_step = (max_lon - min_lon) / width
            lat_step = (max_lat - min_lat) / height
            lons = min_lon + (np.arange(width) + 0.5) * lon_step
            lats = max_lat - (np.arange(height) + 0.5) * lat_step

            # Пиксель попадает в БД, если хотя бы один индекс валиден
            any_valid = np.logical_or.reduce([valid_by_index[k] for k in valid_by_index])

            pixels_to_insert = []
            for y, x in np.argwhere(any_valid):
                row = {
                    'date': date,
                    'lon': float(lons[x]),
                    'lat': float(lats[y])
                }
                for key in ('ndvi', 'ndwi', 'ndbi', 'moisture'):
                    if key in values_by_index and valid_by_index[key][y, x]:
                        row[key] = float(values_by_index[key][y, x])
                    else:
                        row[key] = None
                pixels_to_insert.append(row)

            # Batch insert в БД
            if pixels_to_insert:
                # Создаём партицию под месяц, если её ещё нет
                supabase_service.client.rpc(
                    'ensure_pixel_data_partition', {'p_date': date}
                ).execute()

                batch_size = 1000
                total_inserted = 0

                for i in range(0, len(pixels_to_insert), batch_size):
                    batch = pixels_to_insert[i:i + batch_size]

                    supabase_service.client.table('pixel_data').upsert(
                        batch,
                        on_conflict='date,lon,lat'
                    ).execute()

                    total_inserted += len(batch)
                    logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} pixels")

                logger.info(f"Successfully stored {total_inserted} pixels for date {date}")

                return {
                    "success": True,
                    "pixels_stored": total_inserted,
                    "date": date,
                    "bbox": bbox,
                    "resolution": f"{width}x{height}",
                    "indices": index_types
                }
            else:
                return {
                    "success": False,
                    "pixels_stored": 0,
                    "message": "No valid pixel data found"
                }

        except Exception as e:
            logger.error(f"Error fetching and storing pixel data: {str(e)}")
            raise


# Singleton
tile_cache_service = TileCacheService()
