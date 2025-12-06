import os
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import statistics

from sentinelhub import (
    SHConfig,
    SentinelHubStatistical,
    DataCollection,
    Geometry,
    CRS,
    BBox
)
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

class SentinelHubService:
    """
    Service for interacting with Sentinel Hub API using Evalscript V3 
    and Statistical API.
    """
    
    # Evalscript for NDVI
    NDVI_EVALSCRIPT = """
    //VERSION=3
    function setup() {
        return {
            input: ["B04", "B08", "dataMask"],
            output: [
                { id: "ndvi", bands: 1 },
                { id: "dataMask", bands: 1 }
            ]
        };
    }

    function evaluatePixel(sample) {
        let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
        return {
            ndvi: [ndvi],
            dataMask: [sample.dataMask]
        };
    }
    """

    # Evalscript for NDWI
    NDWI_EVALSCRIPT = """
    //VERSION=3
    function setup() {
        return {
            input: ["B03", "B08", "dataMask"],
            output: [
                { id: "ndwi", bands: 1 },
                { id: "dataMask", bands: 1 }
            ]
        };
    }

    function evaluatePixel(sample) {
        let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
        return {
            ndwi: [ndwi],
            dataMask: [sample.dataMask]
        };
    }
    """

    def __init__(self):
        self._config = None
        self._init_config()

    def _init_config(self):
        from config.settings import settings
        
        client_id = settings.SH_CLIENT_ID
        client_secret = settings.SH_CLIENT_SECRET
        
        if client_id and client_secret:
            self._config = SHConfig()
            self._config.sh_client_id = client_id
            self._config.sh_client_secret = client_secret
            logger.info("SentinelHub config initialized")
        else:
            logger.error("SentinelHub credentials missing (SH_CLIENT_ID, SH_CLIENT_SECRET). Service will fail.")

    def fetch_statistics(
        self,
        bbox_coords: List[float],
        time_interval: Tuple[str, str],
        aggregation_period: str = "P1D",  # 1 day
        resolution: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch statistics for NDVI and NDWI using Sentinel Hub Statistical API.
        
        Args:
            bbox_coords: [min_lon, min_lat, max_lon, max_lat]
            time_interval: (start_date_iso, end_date_iso)
            aggregation_period: ISO 8601 duration (e.g. P1D)
            resolution: Resolution in meters
            
        Returns:
            Dictionary containing processed statistics for NDVI and NDWI
        """
        if not self._config:
            raise Exception("SentinelHub credentials not configured")

        try:
            # Create Geometry
            # Note: Statistical API typically requires a geometry (Polygon) or specific BBox object
            bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
            geometry = Geometry(bbox.geometry, crs=CRS.WGS84)




            # Convert resolution from meters to degrees (approx) if needed
            # 1 degree ~ 111km = 111000m at equator
            if resolution > 1:
                resolution = resolution / 111000.0

            # Dynamic resolution scaling to respect API limit (2500px)
            # Check dimensions in degrees
            width_deg = bbox_coords[2] - bbox_coords[0]
            height_deg = bbox_coords[3] - bbox_coords[1]
            
            # Calculate pixels
            pixels_x = width_deg / resolution
            pixels_y = height_deg / resolution
            
            limit = 2400 # slightly under 2500 to be safe
            
            if pixels_x > limit or pixels_y > limit:
                scale = max(pixels_x / limit, pixels_y / limit)
                resolution = resolution * scale
                logger.warning(f"Resolution adjusted to {resolution:.6f} degrees to fit API limits")

            # Execution Helper
            return self._execute_requests(bbox, time_interval, resolution)

        except Exception as e:
            logger.error(f"Error preparing Sentinel Hub request: {e}")
            raise

    def _execute_requests(self, bbox: BBox, time_interval: Tuple[str, str], resolution: float) -> Dict[str, Any]:
        """
        Execute the actual requests to Sentinel Hub
        """
        stats_data = {
            "ndvi": [],
            "ndwi": []
        }

        # We will fetch NDVI and NDWI separately or we could try to combine them if the API allows multiple outputs
        # For clarity and strictness, let's do two requests or one request with two calculations if script allows.
        # Statistical API standard usually runs one script.
        
        # 1. Fetch NDVI
        logger.info("Fetching NDVI statistics...")
        stats_ndvi = self._run_statistical_request(
            bbox, time_interval, self.NDVI_EVALSCRIPT, "ndvi", resolution
        )
        stats_data["ndvi"] = stats_ndvi

        # 2. Fetch NDWI
        logger.info("Fetching NDWI statistics...")
        stats_ndwi = self._run_statistical_request(
            bbox, time_interval, self.NDWI_EVALSCRIPT, "ndwi", resolution
        )
        stats_data["ndwi"] = stats_ndwi
        
        return stats_data

    def _run_statistical_request(
        self, 
        bbox: BBox, 
        time_interval: Tuple[str, str], 
        evalscript: str, 
        output_name: str,
        resolution: float
    ) -> List[Dict[str, Any]]:
        
        request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=evalscript,
                time_interval=time_interval,
                aggregation_interval="P1D",
                resolution=(resolution, resolution)
            ),
            input_data=[
                SentinelHubStatistical.input_data(
                    DataCollection.SENTINEL2_L2A
                )
            ],
            bbox=bbox,
            config=self._config
        )

        data = request.get_data()
        logger.info(f"Sentinel Hub returned {len(data)} intervals. First item keys: {data[0].keys() if data else 'None'}")
        
        # Process results
        processed_results = []
        
        for page in data:
            # The API returns a list of pages (or just one), where each item is a dict containing "data" list
            if "data" not in page:
                 continue
            
            if len(page["data"]) > 0:
                # logger.info(f"First data item interval: {page['data'][0].get('interval')}")
                pass

            for item in page["data"]:
                if not item.get("outputs") or not item["outputs"].get(output_name):
                    continue
                    
                bands_data = item["outputs"][output_name].get("bands", {})
                if not bands_data:
                     logger.warning(f"No bands data for {output_name}")
                     continue
                     
                # Try to find the correct band name. It should be same as output_name usually, or numeric key "0"
                # If output_name is not in keys, take the first key
                band_key = output_name
                if output_name not in bands_data:
                    band_key = list(bands_data.keys())[0]

                stats = bands_data.get(band_key, {}).get("stats", {})
                
                if not stats:
                    continue
                    
                if stats.get("sampleCount", 0) == 0:
                    continue
                    
                processed_results.append({
                    "date": item["interval"]["from"],
                    "mean": stats.get("mean"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "stDev": stats.get("stDev"),
                    "percentiles": stats.get("percentiles", {}),
                    "sample_count": stats.get("sampleCount")
                })
            
        return processed_results

# Singleton
sentinelhub_service = SentinelHubService()
