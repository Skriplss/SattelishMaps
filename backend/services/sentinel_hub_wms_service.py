"""
Sentinel Hub WMS/Process API Service.
"""
import io
import os
import logging
import tarfile
from typing import Dict, List, Tuple
import requests
import numpy as np
from PIL import Image
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 60  # seconds, for Sentinel Hub HTTP calls


class SentinelHubWMSService:
    def __init__(self):
        self.client_id = os.getenv('SH_CLIENT_ID')
        self.client_secret = os.getenv('SH_CLIENT_SECRET')
        self.base_url = "https://services.sentinel-hub.com"
        self.token = None
        self.token_expires = None
        # Connection pooling — tile bursts reuse TCP/TLS sessions
        self.session = requests.Session()

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
            response = self.session.post(token_url, data=data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)
            
            return self.token

        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise

    @staticmethod
    def _date_search_window(date: str, days: int = 7) -> Tuple[str, str]:
        """Return (date_from, date_to) — ±days around the target date."""
        target_date = datetime.strptime(date, '%Y-%m-%d')
        date_from = (target_date - timedelta(days=days)).strftime('%Y-%m-%d')
        date_to = (target_date + timedelta(days=days)).strftime('%Y-%m-%d')
        return date_from, date_to

    def get_evalscript_for_values(self, index_type: str) -> str:
        """
        Evalscript для получения сырых значений индексов (не картинки)
        Возвращает реальные числа от -1 до 1
        """
        evalscripts = {
            'NDVI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04", "B08", "dataMask"],
                        output: [
                            { id: "default", bands: 1, sampleType: "FLOAT32" },
                            { id: "dataMask", bands: 1, sampleType: "UINT8" }
                        ]
                    };
                }

                function evaluatePixel(sample) {
                    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                    return {
                        default: [ndvi],
                        dataMask: [sample.dataMask]
                    };
                }
            """,
            
            'NDWI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B03", "B08", "dataMask"],
                        output: [
                            { id: "default", bands: 1, sampleType: "FLOAT32" },
                            { id: "dataMask", bands: 1, sampleType: "UINT8" }
                        ]
                    };
                }

                function evaluatePixel(sample) {
                    let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
                    return {
                        default: [ndwi],
                        dataMask: [sample.dataMask]
                    };
                }
            """,
            
            'NDBI': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B08", "B11", "dataMask"],
                        output: [
                            { id: "default", bands: 1, sampleType: "FLOAT32" },
                            { id: "dataMask", bands: 1, sampleType: "UINT8" }
                        ]
                    };
                }

                function evaluatePixel(sample) {
                    let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
                    return {
                        default: [ndbi],
                        dataMask: [sample.dataMask]
                    };
                }
            """,
            
            'MOISTURE': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B08", "B11", "dataMask"],
                        output: [
                            { id: "default", bands: 1, sampleType: "FLOAT32" },
                            { id: "dataMask", bands: 1, sampleType: "UINT8" }
                        ]
                    };
                }

                function evaluatePixel(sample) {
                    let moisture = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
                    return {
                        default: [moisture],
                        dataMask: [sample.dataMask]
                    };
                }
            """
        }
        
        return evalscripts.get(index_type.upper(), evalscripts['NDVI'])
    
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
            date_from, date_to = self._date_search_window(date)

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

            response = self.session.post(url, json=request_payload, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to get image: {str(e)}")
            raise
    
    def get_pixel_values(
        self,
        bbox: List[float],
        date: str,
        index_type: str,
        width: int = 256,
        height: int = 256
    ) -> Dict:
        """
        Получить сырые значения пикселей (не картинку)

        Возвращает:
        - values: numpy-массив значений индекса для каждого пикселя
        - mask: numpy-маска валидных данных (или None)
        - bbox: границы области
        - width, height: размеры
        """
        try:
            token = self.get_access_token()
            date_from, date_to = self._date_search_window(date)

            evalscript = self.get_evalscript_for_values(index_type)
            
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
                            "maxCloudCoverage": 50
                        }
                    }]
                },
                "output": {
                    "width": width,
                    "height": height,
                    "responses": [
                        {
                            "identifier": "default",
                            "format": {
                                "type": "image/tiff"
                            }
                        },
                        {
                            "identifier": "dataMask",
                            "format": {
                                "type": "image/tiff"
                            }
                        }
                    ]
                },
                "evalscript": evalscript
            }
            
            url = f"{self.base_url}/api/v1/process"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/tar'
            }

            response = self.session.post(url, json=request_payload, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Распаковываем tar архив с TIFF файлами
            values = None
            mask = None

            with tarfile.open(fileobj=io.BytesIO(response.content), mode='r') as tar:
                for member in tar.getmembers():
                    file_data = tar.extractfile(member)
                    if file_data:
                        arr = np.array(Image.open(io.BytesIO(file_data.read())))

                        if 'default' in member.name:
                            values = arr
                        elif 'dataMask' in member.name:
                            mask = arr

            if values is None:
                raise ValueError("Failed to extract pixel values from Sentinel Hub response")

            return {
                "values": values,
                "mask": mask,
                "bbox": bbox,
                "width": width,
                "height": height,
                "index_type": index_type,
                "date": date
            }
            
        except Exception as e:
            logger.error(f"Failed to get pixel values: {str(e)}")
            raise


sentinel_hub_wms_service = SentinelHubWMSService()
