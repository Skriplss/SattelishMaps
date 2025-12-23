"""
API endpoints for NDVI and NDWI indices operations
"""
from fastapi import APIRouter, HTTPException, status
from uuid import UUID
import logging

from utils.response_formatter import success_response, created_response
from utils.error_handlers import NotFoundError, SupabaseError
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ndvi/{image_id}", response_model=dict)
async def get_ndvi_data(image_id: UUID):
    """
    Get NDVI data for a specific satellite image
    
    - **image_id**: UUID of the satellite image
    """
    try:
        logger.info(f"Fetching NDVI data for image: {image_id}")
        
        data = supabase_service.get_ndvi_data(str(image_id))
        
        if not data:
            raise NotFoundError(f"NDVI data not found for image {image_id}")
        
        return success_response(
            data=data,
            message="NDVI data retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching NDVI data: {str(e)}")
        raise SupabaseError(f"Failed to fetch NDVI data: {str(e)}")


@router.get("/ndwi/{image_id}", response_model=dict)
async def get_ndwi_data(image_id: UUID):
    """
    Get NDWI data for a specific satellite image
    
    - **image_id**: UUID of the satellite image
    """
    try:
        logger.info(f"Fetching NDWI data for image: {image_id}")
        
        data = supabase_service.get_ndwi_data(str(image_id))
        
        if not data:
            raise NotFoundError(f"NDWI data not found for image {image_id}")
        
        return success_response(
            data=data,
            message="NDWI data retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching NDWI data: {str(e)}")
        raise SupabaseError(f"Failed to fetch NDWI data: {str(e)}")


@router.get("/indices/{image_id}", response_model=dict)
async def get_all_indices(image_id: UUID):
    """
    Get both NDVI and NDWI data for a specific satellite image
    
    - **image_id**: UUID of the satellite image
    """
    try:
        logger.info(f"Fetching all indices for image: {image_id}")
        
        # Get image info
        image = supabase_service.get_satellite_image_by_id(str(image_id))
        if not image:
            raise NotFoundError(f"Satellite image {image_id} not found")
        
        # Get indices
        ndvi_data = supabase_service.get_ndvi_data(str(image_id))
        ndwi_data = supabase_service.get_ndwi_data(str(image_id))
        
        return success_response(
            data={
                "image": image,
                "ndvi": ndvi_data,
                "ndwi": ndwi_data,
                "has_ndvi": ndvi_data is not None,
                "has_ndwi": ndwi_data is not None
            },
            message="Indices data retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching indices: {str(e)}")
        raise SupabaseError(f"Failed to fetch indices: {str(e)}")




# DISABLED: Manual indices calculation - indices are fetched from Sentinel Hub automatically
@router.post("/indices/calculate/{image_id}", response_model=dict, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def calculate_indices(image_id: UUID, force: bool = False):
    """
    Calculate NDVI and NDWI indices for a specific satellite image
    
    NOTE: This endpoint is disabled. Indices are automatically fetched from Sentinel Hub.
    """
    raise HTTPException(
        status_code=501,
        detail="Manual indices calculation is disabled. Indices are fetched automatically from Sentinel Hub."
    )




@router.get("/indices/status/{image_id}", response_model=dict)
async def get_indices_status(image_id: UUID):
    """
    Check if NDVI and NDWI indices have been calculated for an image
    
    - **image_id**: UUID of the satellite image
    """
    try:
        logger.info(f"Checking indices status for image: {image_id}")
        
        # Check if image exists
        image = supabase_service.get_satellite_image_by_id(str(image_id))
        if not image:
            raise NotFoundError(f"Satellite image {image_id} not found")
        
        status = supabase_service.check_image_has_indices(str(image_id))
        
        return success_response(
            data={
                "image_id": str(image_id),
                "product_id": image['product_id'],
                **status
            },
            message="Indices status retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error checking indices status: {str(e)}")
        raise SupabaseError(f"Failed to check indices status: {str(e)}")
