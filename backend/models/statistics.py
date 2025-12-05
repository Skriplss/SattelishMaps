"""
Pydantic models for statistics
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


class NDVIStatistics(BaseModel):
    """NDVI (Normalized Difference Vegetation Index) statistics"""
    mean: float = Field(..., description="Mean NDVI value")
    std: float = Field(..., description="Standard deviation")
    min: float = Field(..., description="Minimum NDVI value")
    max: float = Field(..., description="Maximum NDVI value")
    median: float = Field(..., description="Median NDVI value")


class VegetationIndex(BaseModel):
    """Vegetation health index"""
    index: str = Field(..., description="Index category (healthy, moderate, poor, bare)")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of area")
    color: str = Field(..., description="Color code for visualization")


class ChangeDetection(BaseModel):
    """Change detection data"""
    previous_value: Optional[float] = None
    current_value: float
    change: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = Field(None, description="increasing, decreasing, stable")


class StatisticsBase(BaseModel):
    """Base statistics model"""
    image_id: UUID
    ndvi: Optional[NDVIStatistics] = None
    vegetation_indices: Optional[List[VegetationIndex]] = None
    change_detection: Optional[ChangeDetection] = None


class StatisticsCreate(StatisticsBase):
    """Model for creating statistics"""
    pass


class StatisticsResponse(StatisticsBase):
    """Model for statistics response"""
    id: UUID
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class TimeSeriesData(BaseModel):
    """Time series statistics"""
    date: datetime
    ndvi_mean: float
    cloud_coverage: float
    
    class Config:
        from_attributes = True


class AreaStatistics(BaseModel):
    """Statistics for a specific area"""
    area_name: Optional[str] = None
    total_images: int
    date_range: Dict[str, datetime]
    average_cloud_coverage: float
    average_ndvi: Optional[float] = None
    vegetation_health: Optional[str] = None
