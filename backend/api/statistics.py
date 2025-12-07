"""
API endpoints for statistics operations
"""
from fastapi import APIRouter, Query, Path
from typing import List, Optional
from uuid import UUID
from datetime import date
import logging

from models.statistics import StatisticsResponse, TimeSeriesData, AreaStatistics
from utils.response_formatter import success_response
from utils.error_handlers import NotFoundError, SupabaseError
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/statistics/{image_id}", response_model=dict)
async def get_image_statistics(
    image_id: UUID = Path(..., description="Satellite image UUID")
):
    """
    Get statistics for a specific satellite image
    
    - **image_id**: UUID of the satellite image
    
    Returns NDVI statistics, vegetation indices, and change detection data
    """
    try:
        logger.info(f"Fetching statistics for image: {image_id}")
        
        stats = supabase_service.get_statistics(str(image_id))
        
        if not stats:
            raise NotFoundError(f"Statistics for image {image_id} not found")
        
        return success_response(
            data=stats,
            message="Statistics retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics for {image_id}: {str(e)}")
        raise SupabaseError(f"Failed to fetch statistics: {str(e)}")


@router.get("/statistics/timeseries/{area_name}", response_model=dict)
async def get_timeseries_data(
    area_name: str = Path(..., description="Area name or identifier"),
    index_type: str = Query("NDVI", description="Index type (NDVI, NDWI)"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=365, description="Number of data points")
):
    """
    Get time series statistics for an area
    
    - **area_name**: Name or identifier of the area
    - **index_type**: Type of index (NDVI, NDWI)
    - **date_from**: Start date for time series
    - **date_to**: End date for time series
    - **limit**: Maximum number of data points
    
    Returns time series data with mean values over time
    """
    try:
        logger.info(f"Fetching time series for area: {area_name}, index: {index_type}")
        
        # Convert dates to string if present
        d_from = str(date_from) if date_from else None
        d_to = str(date_to) if date_to else None
        
        data = supabase_service.get_region_statistics_timeseries(
            region_name=area_name,
            index_type=index_type.upper(),
            date_from=d_from,
            date_to=d_to,
            limit=limit
        )
        
        return success_response(
            data=data,
            message=f"Time series data retrieved ({len(data)} points)",
            meta={"count": len(data)}
        )
        
    except Exception as e:
        logger.error(f"Error fetching time series for {area_name}: {str(e)}")
        raise SupabaseError(f"Failed to fetch time series data: {str(e)}")


@router.get("/statistics/area/summary", response_model=dict)
async def get_area_summary(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """
    Get summary statistics for a geographic area
    
    - **min_lat, max_lat, min_lon, max_lon**: Bounding box coordinates
    - **date_from, date_to**: Optional date range filter
    
    Returns aggregated statistics including average NDVI, cloud coverage, and vegetation health
    """
    try:
        logger.info(f"Fetching area summary for bounds: ({min_lat},{min_lon}) to ({max_lat},{max_lon})")
        
        summary = supabase_service.get_area_summary(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            date_from=date_from,
            date_to=date_to
        )
        
        return success_response(
            data=summary,
            message="Area summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error fetching area summary: {str(e)}")
        raise SupabaseError(f"Failed to fetch area summary: {str(e)}")
