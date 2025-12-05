"""
API endpoints for satellite data operations
"""
from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
import logging

from models.satellite_image import (
    SatelliteImageResponse,
    SatelliteImageDetail,
    SatelliteImageCreate,
    CopernicusProduct
)
from utils.validators import SatelliteSearchRequest, SatelliteFilterParams
from utils.response_formatter import success_response, paginated_response, created_response
from utils.error_handlers import NotFoundError, SupabaseError, CopernicusAPIError
from services.supabase_service import supabase_service
from services.copernicus_service import copernicus_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/satellite-data", response_model=dict)
async def list_satellite_images(
    date_from: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    cloud_max: Optional[float] = Query(30, ge=0, le=100, description="Maximum cloud coverage %"),
    platform: Optional[str] = Query(None, description="Satellite platform"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get list of satellite images with optional filters
    
    - **date_from**: Filter images from this date
    - **date_to**: Filter images until this date
    - **cloud_max**: Maximum cloud coverage percentage
    - **platform**: Satellite platform (e.g., Sentinel-2)
    - **page**: Page number for pagination
    - **limit**: Number of items per page
    """
    try:
        logger.info(f"Fetching satellite images: page={page}, limit={limit}, cloud_max={cloud_max}")
        
        # Get data from Supabase
        data, total = supabase_service.get_satellite_images(
            date_from=date_from,
            date_to=date_to,
            cloud_max=cloud_max,
            platform=platform,
            page=page,
            limit=limit
        )
        
        return paginated_response(
            data=data,
            page=page,
            limit=limit,
            total=total,
            message="Satellite images retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error fetching satellite images: {str(e)}")
        raise SupabaseError(f"Failed to fetch satellite images: {str(e)}")


@router.get("/satellite-data/{image_id}", response_model=dict)
async def get_satellite_image(image_id: UUID):
    """
    Get detailed information about a specific satellite image
    
    - **image_id**: UUID of the satellite image
    """
    try:
        logger.info(f"Fetching satellite image: {image_id}")
        
        data = supabase_service.get_satellite_image_by_id(str(image_id))
        
        if not data:
            raise NotFoundError(f"Satellite image with ID {image_id} not found")
        
        return success_response(
            data=data,
            message="Satellite image retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching satellite image {image_id}: {str(e)}")
        raise SupabaseError(f"Failed to fetch satellite image: {str(e)}")


@router.post("/satellite-data/search", response_model=dict)
async def search_copernicus(request: SatelliteSearchRequest):
    """
    Search for satellite images in Copernicus API
    
    - **date_from**: Start date for search
    - **date_to**: End date for search
    - **bounds**: Bounding box coordinates
    - **cloud_max**: Maximum cloud coverage percentage
    - **platform**: Satellite platform (default: Sentinel-2)
    """
    try:
        logger.info(f"Searching Copernicus: {request.date_from} to {request.date_to}")
        
        # Search in Copernicus
        products = copernicus_service.search_products(
            area=request.bounds.to_wkt(),
            date_range=(request.date_from, request.date_to),
            cloud_coverage_max=request.cloud_max,
            platform=request.platform
        )
        
        return success_response(
            data=products,
            message=f"Found {len(products)} products",
            meta={"count": len(products)}
        )
        
    except Exception as e:
        logger.error(f"Error searching Copernicus: {str(e)}")
        raise CopernicusAPIError(f"Failed to search Copernicus: {str(e)}")


@router.post("/satellite-data", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_satellite_image(image: SatelliteImageCreate):
    """
    Add a new satellite image to the database
    
    - **product_id**: Copernicus product ID
    - **acquisition_date**: Image acquisition date
    - **cloud_coverage**: Cloud coverage percentage
    - **platform**: Satellite platform
    """
    try:
        logger.info(f"Creating satellite image: {image.product_id}")
        
        data = supabase_service.insert_satellite_image(image.model_dump())
        
        return created_response(
            data=data,
            message="Satellite image created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating satellite image: {str(e)}")
        raise SupabaseError(f"Failed to create satellite image: {str(e)}")


@router.delete("/satellite-data/{image_id}", response_model=dict)
async def delete_satellite_image(image_id: UUID):
    """
    Delete a satellite image from the database
    
    - **image_id**: UUID of the satellite image to delete
    """
    try:
        logger.info(f"Deleting satellite image: {image_id}")
        
        success = supabase_service.delete_satellite_image(str(image_id))
        
        if not success:
            raise NotFoundError(f"Satellite image with ID {image_id} not found")
        
        return success_response(
            data=None,
            message="Satellite image deleted successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting satellite image {image_id}: {str(e)}")
        raise SupabaseError(f"Failed to delete satellite image: {str(e)}")


@router.get("/satellite-data/bounds/search", response_model=dict)
async def get_images_in_bounds(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    cloud_max: float = Query(30, ge=0, le=100),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get satellite images within a bounding box
    
    - **min_lat**: Minimum latitude
    - **max_lat**: Maximum latitude
    - **min_lon**: Minimum longitude
    - **max_lon**: Maximum longitude
    - **cloud_max**: Maximum cloud coverage
    - **limit**: Maximum number of results
    """
    try:
        logger.info(f"Searching images in bounds: ({min_lat},{min_lon}) to ({max_lat},{max_lon})")
        
        data = supabase_service.get_images_in_bounds(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            cloud_max=cloud_max,
            limit=limit
        )
        
        return success_response(
            data=data,
            message=f"Found {len(data)} images in bounds",
            meta={"count": len(data)}
        )
        
    except Exception as e:
        logger.error(f"Error searching images in bounds: {str(e)}")
        raise SupabaseError(f"Failed to search images in bounds: {str(e)}")
