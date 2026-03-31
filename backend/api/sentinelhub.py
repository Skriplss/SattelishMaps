"""
API endpoints for Sentinel Hub catalog search
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.sentinelhub_service import sentinelhub_service
from utils.response_formatter import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/catalog/search", response_model=dict)
async def search_sentinelhub_catalog(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    cloud_max: float = Query(100, ge=0, le=100),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Search Sentinel Hub Catalog for available satellite images
    
    - **min_lat, max_lat, min_lon, max_lon**: Bounding box coordinates
    - **date_from, date_to**: Date range filter
    - **cloud_max**: Maximum cloud coverage percentage
    - **limit**: Maximum number of results
    
    Returns catalog entries from Sentinel Hub (not from local database)
    """
    try:
        # Default dates if not provided
        from datetime import datetime, timedelta
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Searching catalog: bbox=[{min_lon},{min_lat},{max_lon},{max_lat}], dates={date_from} to {date_to}")
        
        results = sentinelhub_service.search_catalog(
            bbox=[min_lon, min_lat, max_lon, max_lat],
            date_from=date_from,
            date_to=date_to,
            cloud_max=cloud_max,
            limit=limit
        )
        
        return success_response(
            data=results,
            message=f"Found {len(results)} catalog entries",
            meta={"count": len(results)}
        )
        
    except Exception as e:
        logger.error(f"Error searching catalog: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search catalog: {str(e)}"
        )
