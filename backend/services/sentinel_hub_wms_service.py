"""
Sentinel Hub WMS/Process API Service
Provides high-resolution pixel-level visualization
"""
import os
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SentinelHubWMSService:
    """Service for Sentinel Hub WMS and Process API"""
    
    def __init__(self):
        self.client_id = os.getenv('SH_CLIENT_ID')
        self.client_secret = os.getenv('SH_CLIENT_SECRET')
        self.base_url = "https://services.sentinel-hub.com"
        self.token = None
        self.token_expires = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("Sentinel Hub credentials not found")
    
    def get_access_token(self) -> str:
        """Get OAuth2 access token"""
        # Check if token is still valid
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        
        # Request new token
        token_url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data['access_token']
            # Token expires in 1 hour, refresh 5 minutes before
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)
            
            logger.info("Successfully obtained Sentinel Hub access token")
            return self.token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise
    
    def get_evalscript(self, index_type: str) -> str:
        """Get evalscript for specific index type"""
        
        evalscripts = {
            'NDVI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04", "B08", "dataMask"],
                        output: { bands: 4 }
                    };
                }

                function evaluatePixel(sample) {
                    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                    
                    // Color mapping for NDVI
                    if (ndvi < -0.1) return [0.5, 0.3, 0.1, sample.dataMask]; // Brown (bare soil)
                    if (ndvi < 0) return [0.8, 0.7, 0.4, sample.dataMask]; // Light brown
                    if (ndvi < 0.2) return [0.9, 0.9, 0.6, sample.dataMask]; // Yellow (sparse)
                    if (ndvi < 0.4) return [0.6, 0.8, 0.3, sample.dataMask]; // Light green
                    if (ndvi < 0.6) return [0.3, 0.7, 0.2, sample.dataMask]; // Green
                    return [0.1, 0.5, 0.1, sample.dataMask]; // Dark green (dense)
                }
            """,
            
            'NDWI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B03", "B08", "dataMask"],
                        output: { bands: 4 }
                    };
                }

                function evaluatePixel(sample) {
                    let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
                    
                    // Color mapping for NDWI
                    if (ndwi < -0.5) return [0.5, 0.3, 0.1, sample.dataMask]; // Dry soil
                    if (ndwi < -0.2) return [0.8, 0.7, 0.5, sample.dataMask]; // Moist soil
                    if (ndwi < 0) return [0.5, 0.8, 0.9, sample.dataMask]; // Wet soil
                    if (ndwi < 0.2) return [0.3, 0.5, 0.9, sample.dataMask]; // Shallow water
                    if (ndwi < 0.5) return [0.0, 0.0, 0.8, sample.dataMask]; // Deep water
                    return [0.0, 0.0, 0.5, sample.dataMask]; // Very deep water
                }
            """,
            
            'NDBI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B08", "B11", "dataMask"],
                        output: { bands: 4 }
                    };
                }

                function evaluatePixel(sample) {
                    let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
                    
                    // Color mapping for NDBI
                    if (ndbi < -0.5) return [0.0, 0.0, 0.8, sample.dataMask]; // Water
                    if (ndbi < -0.2) return [0.1, 0.5, 0.1, sample.dataMask]; // Vegetation
                    if (ndbi < 0) return [0.8, 0.7, 0.5, sample.dataMask]; // Bare soil
                    if (ndbi < 0.2) return [0.6, 0.3, 0.1, sample.dataMask]; // Light urban
                    if (ndbi < 0.4) return [0.5, 0.2, 0.1, sample.dataMask]; // Dense urban
                    return [0.5, 0.0, 0.0, sample.dataMask]; // Very dense urban
                }
            """,
            
            'MOISTURE': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B08", "B11", "dataMask"],
                        output: { bands: 4 }
                    };
                }

                function evaluatePixel(sample) {
                    let moisture = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
                    
                    // Color mapping for Moisture
                    if (moisture < -0.8) return [0.5, 0.0, 0.0, sample.dataMask]; // Extreme stress
                    if (moisture < -0.6) return [0.8, 0.2, 0.2, sample.dataMask]; // High stress
                    if (moisture < -0.4) return [0.9, 0.5, 0.5, sample.dataMask]; // Moderate stress
                    if (moisture < -0.2) return [1.0, 1.0, 0.0, sample.dataMask]; // Low stress
                    if (moisture < 0) return [0.6, 0.9, 0.6, sample.dataMask]; // Normal
                    if (moisture < 0.2) return [0.0, 1.0, 1.0, sample.dataMask]; // High moisture
                    return [0.0, 0.0, 0.5, sample.dataMask]; // Very high moisture
                }
            """
        }
        
        return evalscripts.get(index_type.upper(), evalscripts['NDVI'])
    
    def get_process_api_request(
        self,
        bbox: List[float],
        date_from: str,
        date_to: str,
        index_type: str,
        width: int = 512,
        height: int = 512
    ) -> Dict:
        """Build Process API request payload"""
        
        evalscript = self.get_evalscript(index_type)
        
        request_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date_from}T00:00:00Z",
                            "to": f"{date_to}T23:59:59Z"
                        },
                        "maxCloudCoverage": 30
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/png"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        return request_payload
    
    def get_image(
        self,
        bbox: List[float],
        date: str,
        index_type: str,
        width: int = 512,
        height: int = 512
    ) -> bytes:
        """Get processed image from Sentinel Hub Process API"""
        
        try:
            token = self.get_access_token()
            
            # Expand time range to ±7 days to get better coverage
            # Sentinel Hub will find the best available image
            from datetime import datetime, timedelta
            target_date = datetime.strptime(date, '%Y-%m-%d')
            date_from = (target_date - timedelta(days=7)).strftime('%Y-%m-%d')
            date_to = (target_date + timedelta(days=7)).strftime('%Y-%m-%d')
            
            logger.info(f"Requesting {index_type} for date range: {date_from} to {date_to}")
            
            request_payload = self.get_process_api_request(
                bbox=bbox,
                date_from=date_from,
                date_to=date_to,
                index_type=index_type,
                width=width,
                height=height
            )
            
            # Increase cloud coverage tolerance for better coverage
            request_payload['input']['data'][0]['dataFilter']['maxCloudCoverage'] = 50
            
            url = f"{self.base_url}/api/v1/process"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'image/png'
            }
            
            response = requests.post(url, json=request_payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully retrieved {index_type} image for {date}")
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to get image: {str(e)}")
            raise


# Singleton instance
sentinel_hub_wms_service = SentinelHubWMSService()
