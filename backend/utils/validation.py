"""
Shared request validation helpers for API endpoints
"""
from datetime import datetime
from functools import lru_cache
from fastapi import HTTPException

from config.settings import settings

VALID_INDICES = ("NDVI", "NDWI", "NDBI", "MOISTURE")


def validate_index_type(index_type: str) -> str:
    """Normalize and validate an index type. Returns the uppercased value."""
    upper = index_type.upper()
    if upper not in VALID_INDICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index_type. Must be one of: {', '.join(VALID_INDICES)}"
        )
    return upper


def validate_date(date_str: str, field: str = "date") -> str:
    """Validate YYYY-MM-DD date string. Returns it unchanged."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field} format. Expected YYYY-MM-DD"
        )
    return date_str


@lru_cache
def coverage_bbox() -> tuple[float, float, float, float]:
    """Coverage area as (min_lon, min_lat, max_lon, max_lat)"""
    parts = [float(x.strip()) for x in settings.COVERAGE_BBOX.split(',')]
    if len(parts) != 4:
        raise ValueError(f"COVERAGE_BBOX must have 4 values, got: {settings.COVERAGE_BBOX}")
    return parts[0], parts[1], parts[2], parts[3]


def bbox_intersects_coverage(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> bool:
    """True when the bbox overlaps the configured coverage area"""
    c_min_lon, c_min_lat, c_max_lon, c_max_lat = coverage_bbox()
    return not (
        max_lon < c_min_lon or min_lon > c_max_lon or
        max_lat < c_min_lat or min_lat > c_max_lat
    )


def validate_bbox_in_coverage(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> None:
    """Reject requests entirely outside the coverage area (Slovakia)"""
    if not bbox_intersects_coverage(min_lon, min_lat, max_lon, max_lat):
        raise HTTPException(
            status_code=400,
            detail=f"Requested area is outside the coverage area (bbox {settings.COVERAGE_BBOX})"
        )
