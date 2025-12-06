from fastapi import APIRouter, HTTPException, Query
from services.sentinelhub_service import sentinelhub_service
from typing import Optional

router = APIRouter()

@router.get("/bounds/search", response_model=dict)
def search_sentinelhub_bounds(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    date_from: str = Query(None),
    date_to: str = Query(None),
    cloud_max: float = 100,
    limit: int = 100
):
    """
    Proxy endpoint to search SentinelHub Catalog
    Matches the frontend expectation: /api/satellite-data/bounds/search
    (This will be mounted under /api/satellite-data)
    """
    try:
        # Defaults if not provided
        d_from = date_from or "2024-01-01"
        d_to = date_to or "2024-12-05"
        
        results = sentinelhub_service.search_catalog(
            bbox=[min_lon, min_lat, max_lon, max_lat],
            date_from=d_from,
            date_to=d_to,
            cloud_max=cloud_max,
            limit=limit
        )
        
        return {"status": "success", "data": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
