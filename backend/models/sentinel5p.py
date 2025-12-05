"""
Pydantic models for Sentinel-5P atmospheric data
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class AtmosphericDataBase(BaseModel):
    """Base model for atmospheric measurements"""
    product_id: str = Field(..., description="Copernicus product ID")
    acquisition_date: datetime = Field(..., description="Measurement date")
    platform: str = Field(default="Sentinel-5P", description="Satellite platform")


class AtmosphericMeasurement(BaseModel):
    """Single atmospheric measurement"""
    parameter: str = Field(..., description="Measurement type (NO2, O3, SO2, AER_AI, CO)")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Measurement unit")
    quality: Optional[float] = Field(None, ge=0, le=1, description="Data quality (0-1)")


class Sentinel5PData(AtmosphericDataBase):
    """Sentinel-5P atmospheric data"""
    # NO₂ (діоксид азоту) - забруднення від транспорту/промисловості
    no2: Optional[float] = Field(None, description="NO₂ concentration (mol/m²)")
    no2_quality: Optional[float] = Field(None, ge=0, le=1)
    
    # O₃ (озон) - поверхневий озон
    o3: Optional[float] = Field(None, description="O₃ concentration (mol/m²)")
    o3_quality: Optional[float] = Field(None, ge=0, le=1)
    
    # SO₂ (сірчистий газ) - промислові викиди
    so2: Optional[float] = Field(None, description="SO₂ concentration (mol/m²)")
    so2_quality: Optional[float] = Field(None, ge=0, le=1)
    
    # AER_AI (аерозольний індекс) - дим, пил, PM2.5
    aer_ai: Optional[float] = Field(None, description="Aerosol Index")
    aer_ai_quality: Optional[float] = Field(None, ge=0, le=1)
    
    # CO (чадний газ) - пожежі, транспорт
    co: Optional[float] = Field(None, description="CO concentration (mol/m²)")
    co_quality: Optional[float] = Field(None, ge=0, le=1)
    
    location: Optional[Dict[str, float]] = Field(None, description="Center point {lat, lon}")
    bounds: Optional[Dict[str, float]] = Field(None, description="Bounding box")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Sentinel5PCreate(Sentinel5PData):
    """Model for creating Sentinel-5P data record"""
    pass


class Sentinel5PResponse(Sentinel5PData):
    """Model for Sentinel-5P data response"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class AirQualityIndex(BaseModel):
    """Air quality assessment"""
    overall_aqi: int = Field(..., ge=0, le=500, description="Overall Air Quality Index")
    category: str = Field(..., description="Good, Moderate, Unhealthy, etc.")
    dominant_pollutant: str = Field(..., description="Main pollutant (NO2, O3, SO2, CO, PM2.5)")
    health_implications: str = Field(..., description="Health advisory")
    color: str = Field(..., description="Color code for visualization")


class PollutionTrend(BaseModel):
    """Pollution trend analysis"""
    parameter: str
    current_value: float
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: str = Field(..., description="increasing, decreasing, stable")
    severity: str = Field(..., description="low, moderate, high, very_high")
