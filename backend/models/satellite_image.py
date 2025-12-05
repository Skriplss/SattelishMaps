"""
Pydantic models for satellite images
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID


class SatelliteImageBase(BaseModel):
    """Base satellite image model"""
    product_id: str = Field(..., description="Copernicus product ID")
    acquisition_date: datetime = Field(..., description="Image acquisition date")
    cloud_coverage: float = Field(..., ge=0, le=100, description="Cloud coverage percentage")
    platform: str = Field(default="Sentinel-2", description="Satellite platform")


class SatelliteImageCreate(SatelliteImageBase):
    """Model for creating satellite image"""
    location: Optional[Dict[str, float]] = Field(None, description="Center point {lat, lon}")
    bounds: Optional[Dict[str, float]] = Field(None, description="Bounding box coordinates")
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SatelliteImageResponse(SatelliteImageBase):
    """Model for satellite image response"""
    id: UUID
    location: Optional[Dict[str, float]] = None
    bounds: Optional[Dict[str, float]] = None
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SatelliteImageDetail(SatelliteImageResponse):
    """Detailed satellite image with statistics"""
    statistics: Optional[Dict[str, Any]] = None


class CopernicusProduct(BaseModel):
    """Copernicus search result"""
    product_id: str
    title: str
    size: str
    acquisition_date: datetime
    cloud_coverage: float
    footprint: str
    download_url: str
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True
