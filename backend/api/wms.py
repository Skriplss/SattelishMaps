"""
API endpoints for WMS/Process API tiles
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from typing import List
import logging

from services.sentinel_hub_wms_service import sentinel_hub_wms_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/wms/image")
async def get_wms_image(
    bbox: str = Query(..., description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE"),
    width: int = Query(512, ge=256, le=2048, description="Image width"),
    height: int = Query(512, ge=256, le=2048, description="Image height")
):
    """
    Get processed satellite image from Sentinel Hub
    
    Returns PNG image with color-coded index values
    
    - **bbox**: Bounding box as "min_lon,min_lat,max_lon,max_lat"
    - **date**: Date in YYYY-MM-DD format
    - **index_type**: One of: NDVI, NDWI, NDBI, MOISTURE
    - **width**: Image width in pixels (256-2048)
    - **height**: Image height in pixels (256-2048)
    """
    try:
        # Parse bbox
        bbox_coords = [float(x) for x in bbox.split(',')]
        if len(bbox_coords) != 4:
            raise ValueError("bbox must have 4 coordinates")
        
        # Validate index type
        valid_indices = ["NDVI", "NDWI", "NDBI", "MOISTURE"]
        index_type_upper = index_type.upper()
        
        if index_type_upper not in valid_indices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index_type. Must be one of: {', '.join(valid_indices)}"
            )
        
        logger.info(f"Fetching WMS image: bbox={bbox}, date={date}, index={index_type_upper}")
        
        # Get image from Sentinel Hub
        image_data = sentinel_hub_wms_service.get_image(
            bbox=bbox_coords,
            date=date,
            index_type=index_type_upper,
            width=width,
            height=height
        )
        
        # Return PNG image
        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching WMS image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch image: {str(e)}"
        )


@router.get("/wms/tile/{z}/{x}/{y}.png")
async def get_wms_tile(
    z: int,
    x: int,
    y: int,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    index_type: str = Query(..., description="Index type: NDVI, NDWI, NDBI, MOISTURE")
):
    """
    Get map tile in XYZ format
    
    - **z**: Zoom level
    - **x**: Tile X coordinate
    - **y**: Tile Y coordinate
    - **date**: Date in YYYY-MM-DD format
    - **index_type**: One of: NDVI, NDWI, NDBI, MOISTURE
    """
    try:
        # Convert tile coordinates to bbox
        import math
        
        def tile_to_bbox(z, x, y):
            """Convert XYZ tile coordinates to lat/lon bbox"""
            n = 2.0 ** z
            lon_min = x / n * 360.0 - 180.0
            lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
            lon_max = (x + 1) / n * 360.0 - 180.0
            lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
            return [lon_min, lat_min, lon_max, lat_max]
        
        bbox_coords = tile_to_bbox(z, x, y)
        
        # Validate index type
        valid_indices = ["NDVI", "NDWI", "NDBI", "MOISTURE"]
        index_type_upper = index_type.upper()
        
        if index_type_upper not in valid_indices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index_type. Must be one of: {', '.join(valid_indices)}"
            )
        
        logger.info(f"Fetching tile: z={z}, x={x}, y={y}, date={date}, index={index_type_upper}")
        
        # Get image from Sentinel Hub
        image_data = sentinel_hub_wms_service.get_image(
            bbox=bbox_coords,
            date=date,
            index_type=index_type_upper,
            width=256,
            height=256
        )
        
        # Return PNG tile
        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching tile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tile: {str(e)}"
        )
