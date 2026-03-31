"""
API endpoints for tile caching and pixel data
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from typing import Optional
import logging

from services.tile_cache_service import tile_cache_service
from utils.response_formatter import success_response

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
    try:
        valid_indices = ["NDVI", "NDWI", "NDBI", "MOISTURE"]
        index_type_upper = index_type.upper()
        
        if index_type_upper not in valid_indices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index_type. Must be one of: {', '.join(valid_indices)}"
            )
        
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
    try:
        result = await tile_cache_service.cache_tile(z, x, y, date, index_type.upper())
        
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
