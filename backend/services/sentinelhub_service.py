import os
import logging
from sentinelhub import SHConfig, SentinelHubCatalog
from typing import List, Dict, Any, Tuple, Optional
from datetime import date

logger = logging.getLogger(__name__)

class SentinelHubService:
    """Service for interacting with SentinelHub API"""
    
    def __init__(self):
        self._config = None
        self._init_config()

    def _init_config(self):
        client_id = os.getenv("SH_CLIENT_ID")
        client_secret = os.getenv("SH_CLIENT_SECRET")
        
        if client_id and client_secret:
            self._config = SHConfig()
            self._config.sh_client_id = client_id
            self._config.sh_client_secret = client_secret
            logger.info("SentinelHub config initialized")
        else:
            logger.warning("SentinelHub credentials missing. Service will fail if called.")

    def search_catalog(
        self,
        bbox: List[float],
        date_from: str,
        date_to: str,
        cloud_max: float = 1.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search SentinelHub Catalog for Sentinel-2 L2A scenes.
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_from: "YYYY-MM-DD"
            date_to: "YYYY-MM-DD"
            cloud_max: 0.0 to 1.0 (SentinelHub uses 0-100 in docs, but 0-1 in some APIs, let's assume 0.0-1.0 here for consistency with internal logic, converted from UI % if needed)
            limit: max results
            
        Returns:
            List of simplified scene objects
        """
        if not self._config:
            raise Exception("SentinelHub credentials not configured")
            
        try:
            catalog = SentinelHubCatalog(config=self._config)
            
            # Convert cloud_max from 0-100 to 0-1 if passed as percentage
            maxcc = cloud_max if cloud_max <= 1.0 else cloud_max / 100.0
            
            iterator = catalog.search(
                collection="sentinel-2-l2a",
                bbox=bbox,
                time=(date_from, date_to),
                maxcc=maxcc,
                limit=limit
            )
            
            results = []
            for result in iterator:
                props = result.get('properties', {})
                geom = result.get('geometry', {})
                
                # Simplified object for frontend
                scene = {
                    "id": result.get('id'),
                    "acquisition_date": props.get('datetime'),
                    "cloud_coverage": props.get('eo:cloud_cover'),
                    "platform": props.get('platform', 'Sentinel-2'),
                    "geometry": geom,
                    # Fallback center point for simple view
                    "center_point": f"POINT({(bbox[0]+bbox[2])/2} {(bbox[1]+bbox[3])/2})" 
                }
                results.append(scene)
                
            return results
            
        except Exception as e:
            logger.error(f"SentinelHub Catalog search failed: {e}")
            raise

# Singleton
sentinelhub_service = SentinelHubService()
