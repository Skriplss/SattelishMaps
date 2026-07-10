"""
API endpoints for WMS/Process API tiles
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import logging

from config.settings import settings
from services.sentinel_hub_wms_service import sentinel_hub_wms_service
from services.tile_cache_service import tile_cache_service
from services.pixel_tile_renderer import empty_tile_png
from utils.validation import (
    validate_index_type,
    validate_date,
    validate_bbox_in_coverage,
    bbox_intersects_coverage
)

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
    index_type_upper = validate_index_type(index_type)
    validate_date(date)

    try:
        # Parse bbox
        bbox_coords = [float(x) for x in bbox.split(',')]
        if len(bbox_coords) != 4:
            raise ValueError("bbox must have 4 coordinates")

        validate_bbox_in_coverage(*bbox_coords)

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
    index_type_upper = validate_index_type(index_type)
    validate_date(date)

    # Tiles outside coverage: transparent PNG, no Sentinel Hub call
    tile_bbox = tile_cache_service.tile_to_bbox(z, x, y)
    if not bbox_intersects_coverage(*tile_bbox):
        return Response(
            content=empty_tile_png(),
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=604800",
                "Access-Control-Allow-Origin": "*",
                "X-Tile-Cache": "OUT_OF_COVERAGE"
            }
        )

    try:
        # Try DB cache first — saves a Sentinel Hub request on repeat views
        cached = await tile_cache_service.get_cached_tile(z, x, y, date, index_type_upper)
        if cached:
            return Response(
                content=cached,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                    "X-Tile-Cache": "HIT"
                }
            )

        # Optionally render from stored pixel_data before hitting Sentinel Hub
        if settings.PREFER_PIXEL_TILES:
            pixel_tile = await tile_cache_service.render_tile_from_pixels(
                z, x, y, date, index_type_upper
            )
            if pixel_tile:
                return Response(
                    content=pixel_tile,
                    media_type="image/png",
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "Access-Control-Allow-Origin": "*",
                        "X-Tile-Cache": "PIXEL"
                    }
                )

        logger.info(f"Fetching tile: z={z}, x={x}, y={y}, date={date}, index={index_type_upper}")

        image_data = sentinel_hub_wms_service.get_image(
            bbox=tile_bbox,
            date=date,
            index_type=index_type_upper,
            width=256,
            height=256
        )

        # Cache failures must not break tile serving
        try:
            await tile_cache_service.store_tile(z, x, y, date, index_type_upper, image_data)
        except Exception as e:
            logger.warning(f"Failed to cache tile z={z}/{x}/{y}: {e}")

        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*",
                "X-Tile-Cache": "MISS"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tile: {str(e)}"
        )
