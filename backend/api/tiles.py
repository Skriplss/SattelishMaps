"""
API endpoints for tile caching and pixel data
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import logging

from services.tile_cache_service import tile_cache_service
from services.pixel_tile_renderer import empty_tile_png
from utils.response_formatter import success_response
from utils.validation import validate_index_type, validate_date, validate_bbox_in_coverage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tiles/area/stats", response_model=dict)
async def get_area_pixel_statistics(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE")
):
    """
    Get pixel-level statistics for a selected area

    Returns aggregated statistics from cached pixel data
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date)

    try:
        logger.info(f"Fetching pixel stats for area: [{min_lon},{min_lat}] to [{max_lon},{max_lat}], date={date}, index={index_type_upper}")

        stats = await tile_cache_service.get_area_statistics(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            date=date,
            index_type=index_type_upper
        )

        return success_response(
            data=stats,
            message="Area statistics retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error fetching area statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch area statistics: {str(e)}"
        )


@router.get("/tiles/area/timeseries", response_model=dict)
async def get_area_pixel_timeseries(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE"),
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get per-date aggregated pixel statistics for a selected area over a date range.

    Powers timeseries charts for arbitrary user-selected areas.
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date_from, "date_from")
    validate_date(date_to, "date_to")

    try:
        data = await tile_cache_service.get_area_timeseries(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            index_type=index_type_upper,
            date_from=date_from,
            date_to=date_to
        )

        return success_response(
            data=data,
            message=f"Area timeseries retrieved ({len(data)} points)",
            meta={"count": len(data)}
        )

    except Exception as e:
        logger.error(f"Error fetching area timeseries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch area timeseries: {str(e)}"
        )


@router.get("/tiles/area/histogram", response_model=dict)
async def get_area_pixel_histogram(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE"),
    bins: int = Query(20, ge=4, le=100, description="Number of histogram buckets")
):
    """
    Get the value distribution (histogram) of an index for a selected area.
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date)

    try:
        data = await tile_cache_service.get_area_histogram(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            date=date,
            index_type=index_type_upper,
            bins=bins
        )

        return success_response(
            data=data,
            message=f"Area histogram retrieved ({len(data)} buckets)",
            meta={"count": len(data)}
        )

    except Exception as e:
        logger.error(f"Error fetching area histogram: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch area histogram: {str(e)}"
        )


@router.get("/tiles/area/change", response_model=dict)
async def get_area_pixel_change(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date_a: str = Query(..., description="Baseline date (YYYY-MM-DD)"),
    date_b: str = Query(..., description="Comparison date (YYYY-MM-DD)"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE"),
    threshold: float = Query(0.05, ge=0, le=1, description="Min |diff| to count a pixel as changed")
):
    """
    Change detection: compare pixel values between two dates over an area.

    Returns mean values for both dates, mean difference, and counts of
    improved / declined / stable pixels.
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date_a, "date_a")
    validate_date(date_b, "date_b")

    try:
        data = await tile_cache_service.get_area_change(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            date_a=date_a,
            date_b=date_b,
            index_type=index_type_upper,
            threshold=threshold
        )

        return success_response(
            data=data,
            message="Area change analysis retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error fetching area change: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch area change: {str(e)}"
        )


@router.get("/tiles/pixel/{z}/{x}/{y}.png")
async def get_pixel_tile(
    z: int,
    x: int,
    y: int,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE")
):
    """
    Render a map tile directly from stored pixel_data — no Sentinel Hub
    request, no quota. Transparent where no pixel data exists.
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date)

    tile = await tile_cache_service.render_tile_from_pixels(z, x, y, date, index_type_upper)

    return Response(
        content=tile if tile else empty_tile_png(),
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
            "X-Pixel-Data": "HIT" if tile else "EMPTY"
        }
    )


@router.post("/tiles/cache", response_model=dict)
async def cache_tile(
    z: int = Query(..., description="Zoom level"),
    x: int = Query(..., description="Tile X coordinate"),
    y: int = Query(..., description="Tile Y coordinate"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type")
):
    """
    Cache a tile in the database
    
    This endpoint fetches a tile from Sentinel Hub and stores it in the database
    """
    index_type_upper = validate_index_type(index_type)
    validate_date(date)
    validate_bbox_in_coverage(*tile_cache_service.tile_to_bbox(z, x, y))

    try:
        result = await tile_cache_service.cache_tile(z, x, y, date, index_type_upper)
        
        return success_response(
            data=result,
            message="Tile cached successfully"
        )
        
    except Exception as e:
        logger.error(f"Error caching tile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cache tile: {str(e)}"
        )


@router.post("/tiles/fetch-pixels", response_model=dict)
async def fetch_and_store_pixels(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    resolution: int = Query(100, ge=10, le=500, description="Grid resolution (pixels per side)")
):
    """
    Получить пиксельные данные из Sentinel Hub и сохранить в БД
    
    Этот endpoint:
    1. Запрашивает сырые значения индексов (NDVI, NDWI, NDBI, MOISTURE) из Sentinel Hub
    2. Вычисляет координаты для каждого пикселя
    3. Сохраняет данные в таблицу pixel_data
    
    Args:
        min_lat, max_lat, min_lon, max_lon: границы области
        date: дата в формате YYYY-MM-DD
        resolution: размер сетки (по умолчанию 100x100 пикселей)
    
    Returns:
        Статистика сохраненных данных
    """
    validate_date(date)
    validate_bbox_in_coverage(min_lon, min_lat, max_lon, max_lat)

    try:
        logger.info(f"Fetching pixels for area: [{min_lon},{min_lat}] to [{max_lon},{max_lat}], date={date}, resolution={resolution}")
        
        result = await tile_cache_service.fetch_and_store_pixel_data(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            date=date,
            resolution=resolution
        )
        
        return success_response(
            data=result,
            message=f"Successfully processed {result.get('pixels_stored', 0)} pixels"
        )
        
    except Exception as e:
        logger.error(f"Error fetching and storing pixels: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch and store pixels: {str(e)}"
        )
