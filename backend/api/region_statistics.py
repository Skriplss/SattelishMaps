"""
API endpoints for region statistics operations
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date
import logging

from utils.response_formatter import success_response
from utils.error_handlers import NotFoundError, SupabaseError
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/statistics/region", response_model=dict)
async def get_region_statistics(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, or MOISTURE"),
    region_name: Optional[str] = Query(None, description="Optional region name filter")
):
    """
    Get region statistics for a specific date and index type
    
    Returns GeoJSON FeatureCollection with polygons and statistics
    
    - **date**: Date in YYYY-MM-DD format
    - **index_type**: One of: NDVI, NDWI, NDBI, MOISTURE
    - **region_name**: Optional filter by region name
    """
    try:
        # Validate index_type
        valid_indices = ["NDVI", "NDWI", "NDBI", "MOISTURE"]
        index_type_upper = index_type.upper()
        
        if index_type_upper not in valid_indices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index_type. Must be one of: {', '.join(valid_indices)}"
            )
        
        logger.info(f"Fetching region statistics: date={date}, index={index_type_upper}, region={region_name}")
        
        # Get data from Supabase
        geojson_data = supabase_service.get_region_statistics_geojson(
            date=date,
            index_type=index_type_upper,
            region_name=region_name
        )
        
        if not geojson_data or not geojson_data.get('features'):
            raise NotFoundError(
                f"No statistics found for date={date}, index={index_type_upper}"
            )
        
        return success_response(
            data=geojson_data,
            message=f"Region statistics retrieved successfully ({len(geojson_data['features'])} regions)",
            meta={
                "date": date,
                "index_type": index_type_upper,
                "region_count": len(geojson_data['features'])
            }
        )
        
    except NotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching region statistics: {str(e)}")
        raise SupabaseError(f"Failed to fetch region statistics: {str(e)}")


@router.get("/statistics/region/dates", response_model=dict)
async def get_available_dates(
    index_type: Optional[str] = Query(None, description="Filter by index type"),
    region_name: Optional[str] = Query(None, description="Filter by region name")
):
    """
    Get list of available dates for region statistics
    
    - **index_type**: Optional filter by index type
    - **region_name**: Optional filter by region name
    """
    try:
        logger.info(f"Fetching available dates: index={index_type}, region={region_name}")
        
        dates = supabase_service.get_available_dates(
            index_type=index_type.upper() if index_type else None,
            region_name=region_name
        )
        
        return success_response(
            data={"dates": dates},
            message=f"Found {len(dates)} available dates",
            meta={"count": len(dates)}
        )
        
    except Exception as e:
        logger.error(f"Error fetching available dates: {str(e)}")
        raise SupabaseError(f"Failed to fetch available dates: {str(e)}")
