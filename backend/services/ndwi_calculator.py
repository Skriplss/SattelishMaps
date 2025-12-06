"""
NDWI (Normalized Difference Water Index) Calculator Service

NDWI Formula: (Green - NIR) / (Green + NIR)
Range: -1 to 1

Interpretation:
- < 0: No water
- 0 to 0.2: Low water content
- 0.2 to 0.5: Moderate water content
- > 0.5: High water content, water bodies
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class NDWICalculator:
    """Service for calculating NDWI indices"""
    
    @staticmethod
    def classify_water(ndwi_mean: float) -> str:
        """Classify water content based on NDWI value"""
        if ndwi_mean < 0:
            return "no_water"
        elif ndwi_mean < 0.2:
            return "low"
        elif ndwi_mean < 0.5:
            return "moderate"
        else:
            return "high"
    
    @staticmethod
    def calculate_water_percentage(ndwi_mean: float) -> float:
        """Estimate water percentage from NDWI"""
        # Simple linear mapping: NDWI 0-1 -> 0-100%
        if ndwi_mean < 0:
            return 0.0
        return min(100.0, ndwi_mean * 100)
    
    def calculate_ndwi_from_metadata(
        self,
        image_id: str,
        product_id: str,
        cloud_coverage: float,
        center_point: Optional[Dict[str, float]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate NDWI from metadata (MVP version)
        
        For MVP, we estimate NDWI based on cloud coverage.
        In production, this should process actual Green and NIR bands from GeoTIFF.
        
        Args:
            image_id: UUID of satellite image
            product_id: Copernicus product ID
            cloud_coverage: Cloud coverage percentage
            center_point: Center coordinates {lat, lon}
            request_id: Optional request ID
        
        Returns:
            Dictionary with NDWI statistics
        """
        try:
            logger.info(f"Calculating NDWI for image {image_id} (MVP mode)")
            
            # MVP: Estimate NDWI based on cloud coverage
            # Higher cloud coverage might indicate more moisture
            # This is a simplified estimation for demonstration
            base_ndwi = 0.2  # Assume low water content
            cloud_bonus = (cloud_coverage / 100) * 0.15
            ndwi_mean = min(0.5, base_ndwi + cloud_bonus)
            
            # Add some realistic variance
            ndwi_std = 0.12
            ndwi_min = max(-0.3, ndwi_mean - 2 * ndwi_std)
            ndwi_max = min(0.8, ndwi_mean + 2 * ndwi_std)
            ndwi_median = ndwi_mean
            
            # Classify water content
            water_category = self.classify_water(ndwi_mean)
            water_percentage = self.calculate_water_percentage(ndwi_mean)
            
            # Quality score (higher for lower cloud coverage)
            quality_score = (100 - cloud_coverage) / 100
            
            result = {
                "image_id": image_id,
                "request_id": request_id,
                "ndwi_mean": round(ndwi_mean, 4),
                "ndwi_min": round(ndwi_min, 4),
                "ndwi_max": round(ndwi_max, 4),
                "ndwi_std": round(ndwi_std, 4),
                "ndwi_median": round(ndwi_median, 4),
                "water_category": water_category,
                "water_percentage": round(water_percentage, 2),
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
            
            logger.info(f"NDWI calculated: mean={ndwi_mean:.4f}, category={water_category}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating NDWI for {image_id}: {str(e)}")
            raise
    
    def calculate_ndwi_from_bands(
        self,
        green_band_path: str,
        nir_band_path: str,
        image_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate NDWI from actual Green and NIR band GeoTIFF files
        
        This is the production version that processes actual satellite data.
        Requires downloading and processing GeoTIFF files.
        
        Args:
            green_band_path: Path to Green band GeoTIFF
            nir_band_path: Path to NIR band GeoTIFF
            image_id: UUID of satellite image
            request_id: Optional request ID
        
        Returns:
            Dictionary with NDWI statistics
        """
        try:
            import rasterio
            
            logger.info(f"Calculating NDWI from bands for image {image_id}")
            
            # Read Green band (Band 3 for Sentinel-2)
            with rasterio.open(green_band_path) as green_src:
                green = green_src.read(1).astype(float)
            
            # Read NIR band (Band 8 for Sentinel-2)
            with rasterio.open(nir_band_path) as nir_src:
                nir = nir_src.read(1).astype(float)
            
            # Calculate NDWI: (Green - NIR) / (Green + NIR)
            # Avoid division by zero
            denominator = green + nir
            ndwi = np.where(
                denominator != 0,
                (green - nir) / denominator,
                0
            )
            
            # Calculate statistics
            ndwi_mean = float(np.mean(ndwi))
            ndwi_min = float(np.min(ndwi))
            ndwi_max = float(np.max(ndwi))
            ndwi_std = float(np.std(ndwi))
            ndwi_median = float(np.median(ndwi))
            
            # Classify water content
            water_category = self.classify_water(ndwi_mean)
            water_percentage = self.calculate_water_percentage(ndwi_mean)
            
            # Calculate quality score based on data validity
            valid_pixels = np.sum((ndwi >= -1) & (ndwi <= 1))
            total_pixels = ndwi.size
            quality_score = valid_pixels / total_pixels if total_pixels > 0 else 0
            
            result = {
                "image_id": image_id,
                "request_id": request_id,
                "ndwi_mean": round(ndwi_mean, 4),
                "ndwi_min": round(ndwi_min, 4),
                "ndwi_max": round(ndwi_max, 4),
                "ndwi_std": round(ndwi_std, 4),
                "ndwi_median": round(ndwi_median, 4),
                "water_category": water_category,
                "water_percentage": round(water_percentage, 2),
                "quality_score": round(quality_score, 2),
                "metadata": {
                    "calculation_method": "band_processing",
                    "total_pixels": int(total_pixels),
                    "valid_pixels": int(valid_pixels)
                }
            }
            
            logger.info(f"NDWI calculated from bands: mean={ndwi_mean:.4f}")
            return result
            
        except ImportError:
            logger.error("rasterio not installed - cannot process GeoTIFF files")
            raise
        except Exception as e:
            logger.error(f"Error calculating NDWI from bands: {str(e)}")
            raise


# Singleton instance
ndwi_calculator = NDWICalculator()
