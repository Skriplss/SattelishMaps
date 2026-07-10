"""
API endpoints for statistics operations
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
from datetime import date
import logging

from utils.response_formatter import success_response
from utils.error_handlers import SupabaseError
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/statistics/regions", response_model=dict)
async def get_regions():
    """Get the list of regions that have statistics in the database"""
    try:
        regions = supabase_service.get_region_names()

        return success_response(
            data={"regions": regions},
            message=f"Found {len(regions)} regions",
            meta={"count": len(regions)}
        )

    except Exception as e:
        logger.error(f"Error fetching regions: {str(e)}")
        raise SupabaseError(f"Failed to fetch regions: {str(e)}")


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
