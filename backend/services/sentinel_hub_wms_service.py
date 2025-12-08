"""
Sentinel Hub WMS/Process API Service.
"""
import os
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SentinelHubWMSService:
    def __init__(self):
        self.client_id = os.getenv('SH_CLIENT_ID')
        self.client_secret = os.getenv('SH_CLIENT_SECRET')
        self.base_url = "https://services.sentinel-hub.com"
        self.token = None
        self.token_expires = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("Sentinel Hub credentials not found")
    
    def get_access_token(self) -> str:
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        
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
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)
            
            return self.token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise
    
    def get_evalscript(self, index_type: str) -> str:
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
                    
                    if (ndvi < -0.1) return [0.5, 0.3, 0.1, sample.dataMask];
                    if (ndvi < 0) return [0.8, 0.7, 0.4, sample.dataMask];
                    if (ndvi < 0.2) return [0.9, 0.9, 0.6, sample.dataMask];
                    if (ndvi < 0.4) return [0.6, 0.8, 0.3, sample.dataMask];
                    if (ndvi < 0.6) return [0.3, 0.7, 0.2, sample.dataMask];
                    return [0.1, 0.5, 0.1, sample.dataMask];
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
                    
                    if (ndwi < -0.5) return [0.5, 0.3, 0.1, sample.dataMask];
                    if (ndwi < -0.2) return [0.8, 0.7, 0.5, sample.dataMask];
                    if (ndwi < 0) return [0.5, 0.8, 0.9, sample.dataMask];
                    if (ndwi < 0.2) return [0.3, 0.5, 0.9, sample.dataMask];
                    if (ndwi < 0.5) return [0.0, 0.0, 0.8, sample.dataMask];
                    return [0.0, 0.0, 0.5, sample.dataMask];
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
                    
                    if (ndbi < -0.5) return [0.0, 0.0, 0.8, sample.dataMask];
                    if (ndbi < -0.2) return [0.1, 0.5, 0.1, sample.dataMask];
                    if (ndbi < 0) return [0.8, 0.7, 0.5, sample.dataMask];
                    if (ndbi < 0.2) return [0.6, 0.3, 0.1, sample.dataMask];
                    if (ndbi < 0.4) return [0.5, 0.2, 0.1, sample.dataMask];
                    return [0.5, 0.0, 0.0, sample.dataMask];
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
                    
                    if (moisture < -0.8) return [0.5, 0.0, 0.0, sample.dataMask];
                    if (moisture < -0.6) return [0.8, 0.2, 0.2, sample.dataMask];
                    if (moisture < -0.4) return [0.9, 0.5, 0.5, sample.dataMask];
                    if (moisture < -0.2) return [1.0, 1.0, 0.0, sample.dataMask];
                    if (moisture < 0) return [0.6, 0.9, 0.6, sample.dataMask];
                    if (moisture < 0.2) return [0.0, 1.0, 1.0, sample.dataMask];
                    return [0.0, 0.0, 0.5, sample.dataMask];
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
        evalscript = self.get_evalscript(index_type)
        
        return {
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
    
    def get_image(
        self,
        bbox: List[float],
        date: str,
        index_type: str,
        width: int = 512,
        height: int = 512
    ) -> bytes:
        try:
            token = self.get_access_token()
            
            from datetime import datetime, timedelta
            target_date = datetime.strptime(date, '%Y-%m-%d')
            date_from = (target_date - timedelta(days=7)).strftime('%Y-%m-%d')
            date_to = (target_date + timedelta(days=7)).strftime('%Y-%m-%d')
            
            request_payload = self.get_process_api_request(
                bbox=bbox,
                date_from=date_from,
                date_to=date_to,
                index_type=index_type,
                width=width,
                height=height
            )
            
            request_payload['input']['data'][0]['dataFilter']['maxCloudCoverage'] = 50
            
            url = f"{self.base_url}/api/v1/process"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'image/png'
            }
            
            response = requests.post(url, json=request_payload, headers=headers)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to get image: {str(e)}")
            raise


sentinel_hub_wms_service = SentinelHubWMSService()
