"""
NDVI (Normalized Difference Vegetation Index) Calculator Service

NDVI Formula: (NIR - Red) / (NIR + Red)
Range: -1 to 1

Interpretation:
- -1 to 0: Water, bare soil, rocks
- 0 to 0.2: Bare soil, sparse vegetation
- 0.2 to 0.5: Moderate vegetation
- 0.5 to 1: Dense vegetation, healthy plants
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class NDVICalculator:
    """Service for calculating NDVI indices"""
    
    @staticmethod
    def classify_vegetation(ndvi_mean: float) -> str:
        """Classify vegetation based on NDVI value"""
        if ndvi_mean < 0:
            return "bare_soil"
        elif ndvi_mean < 0.2:
            return "sparse"
        elif ndvi_mean < 0.5:
            return "moderate"
        else:
            return "dense"
    
    @staticmethod
    def calculate_vegetation_percentage(ndvi_mean: float) -> float:
        """Estimate vegetation percentage from NDVI"""
        # Simple linear mapping: NDVI 0-1 -> 0-100%
        if ndvi_mean < 0:
            return 0.0
        return min(100.0, ndvi_mean * 100)
    
    def calculate_ndvi_from_metadata(
        self,
        image_id: str,
        product_id: str,
        cloud_coverage: float,
        center_point: Optional[Dict[str, float]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate NDVI from metadata (MVP version)
        
        For MVP, we estimate NDVI based on cloud coverage and season.
        In production, this should process actual NIR and Red bands from GeoTIFF.
        
        Args:
            image_id: UUID of satellite image
            product_id: Copernicus product ID
            cloud_coverage: Cloud coverage percentage
            center_point: Center coordinates {lat, lon}
            request_id: Optional request ID
        
        Returns:
            Dictionary with NDVI statistics
        """
        try:
            logger.info(f"Calculating NDVI for image {image_id} (MVP mode)")
            
            # MVP: Estimate NDVI based on cloud coverage
            # Lower cloud coverage typically means better vegetation visibility
            # This is a simplified estimation for demonstration
            base_ndvi = 0.6  # Assume moderate vegetation
            cloud_penalty = (cloud_coverage / 100) * 0.3
            ndvi_mean = max(0.0, base_ndvi - cloud_penalty)
            
            # Add some realistic variance
            ndvi_std = 0.15
            ndvi_min = max(-0.2, ndvi_mean - 2 * ndvi_std)
            ndvi_max = min(1.0, ndvi_mean + 2 * ndvi_std)
            ndvi_median = ndvi_mean
            
            # Classify vegetation
            vegetation_category = self.classify_vegetation(ndvi_mean)
            vegetation_percentage = self.calculate_vegetation_percentage(ndvi_mean)
            
            # Quality score (higher for lower cloud coverage)
            quality_score = (100 - cloud_coverage) / 100
            
            result = {
                "image_id": image_id,
                "request_id": request_id,
                "ndvi_mean": round(ndvi_mean, 4),
                "ndvi_min": round(ndvi_min, 4),
                "ndvi_max": round(ndvi_max, 4),
                "ndvi_std": round(ndvi_std, 4),
                "ndvi_median": round(ndvi_median, 4),
                "vegetation_category": vegetation_category,
                "vegetation_percentage": round(vegetation_percentage, 2),
                "area_coverage": 10000.0,  # Mock: 10,000 m²
                "quality_score": round(quality_score, 2),
                "metadata": {
                    "calculation_method": "metadata_estimation",
                    "product_id": product_id,
                    "cloud_coverage": cloud_coverage,
                    "note": "MVP estimation - production should use actual band data"
                }
            }
            
            # Add location if provided
            if center_point:
                result["location"] = f"POINT({center_point.get('lon', 0)} {center_point.get('lat', 0)})"
            
            logger.info(f"NDVI calculated: mean={ndvi_mean:.4f}, category={vegetation_category}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating NDVI for {image_id}: {str(e)}")
            raise
    
    def calculate_ndvi_from_bands(
        self,
        nir_band_path: str,
        red_band_path: str,
        image_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate NDVI from actual NIR and Red band GeoTIFF files
        
        This is the production version that processes actual satellite data.
        Requires downloading and processing GeoTIFF files.
        
        Args:
            nir_band_path: Path to NIR band GeoTIFF
            red_band_path: Path to Red band GeoTIFF
            image_id: UUID of satellite image
            request_id: Optional request ID
        
        Returns:
            Dictionary with NDVI statistics
        """
        try:
            import rasterio
            
            logger.info(f"Calculating NDVI from bands for image {image_id}")
            
            # Read NIR band (Band 8 for Sentinel-2)
            with rasterio.open(nir_band_path) as nir_src:
                nir = nir_src.read(1).astype(float)
            
            # Read Red band (Band 4 for Sentinel-2)
            with rasterio.open(red_band_path) as red_src:
                red = red_src.read(1).astype(float)
            
            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            # Avoid division by zero
            denominator = nir + red
            ndvi = np.where(
                denominator != 0,
                (nir - red) / denominator,
                0
            )
            
            # Calculate statistics
            ndvi_mean = float(np.mean(ndvi))
            ndvi_min = float(np.min(ndvi))
            ndvi_max = float(np.max(ndvi))
            ndvi_std = float(np.std(ndvi))
            ndvi_median = float(np.median(ndvi))
            
            # Classify vegetation
            vegetation_category = self.classify_vegetation(ndvi_mean)
            vegetation_percentage = self.calculate_vegetation_percentage(ndvi_mean)
            
            # Calculate quality score based on data validity
            valid_pixels = np.sum((ndvi >= -1) & (ndvi <= 1))
            total_pixels = ndvi.size
            quality_score = valid_pixels / total_pixels if total_pixels > 0 else 0
            
            result = {
                "image_id": image_id,
                "request_id": request_id,
                "ndvi_mean": round(ndvi_mean, 4),
                "ndvi_min": round(ndvi_min, 4),
                "ndvi_max": round(ndvi_max, 4),
                "ndvi_std": round(ndvi_std, 4),
                "ndvi_median": round(ndvi_median, 4),
                "vegetation_category": vegetation_category,
                "vegetation_percentage": round(vegetation_percentage, 2),
                "quality_score": round(quality_score, 2),
                "metadata": {
                    "calculation_method": "band_processing",
                    "total_pixels": int(total_pixels),
                    "valid_pixels": int(valid_pixels)
                }
            }
            
            logger.info(f"NDVI calculated from bands: mean={ndvi_mean:.4f}")
            return result
            
        except ImportError:
            logger.error("rasterio not installed - cannot process GeoTIFF files")
            raise
        except Exception as e:
            logger.error(f"Error calculating NDVI from bands: {str(e)}")
            raise


# Singleton instance
ndvi_calculator = NDVICalculator()
