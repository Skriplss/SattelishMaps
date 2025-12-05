"""
Request validators using Pydantic
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Tuple
from datetime import datetime, date


class DateRangeValidator(BaseModel):
    """Валидация диапазона дат"""
    date_from: date = Field(..., description="Start date (YYYY-MM-DD)")
    date_to: date = Field(..., description="End date (YYYY-MM-DD)")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if 'date_from' in values and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v


class BoundingBoxValidator(BaseModel):
    """Валидация координат bounding box"""
    min_lat: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    max_lat: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    min_lon: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_lon: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    
    @validator('max_lat')
    def validate_lat_range(cls, v, values):
        if 'min_lat' in values and v <= values['min_lat']:
            raise ValueError('max_lat must be greater than min_lat')
        return v
    
    @validator('max_lon')
    def validate_lon_range(cls, v, values):
        if 'min_lon' in values and v <= values['min_lon']:
            raise ValueError('max_lon must be greater than min_lon')
        return v
    
    def to_wkt(self) -> str:
        """Convert to WKT POLYGON format for Copernicus API"""
        return f"POLYGON(({self.min_lon} {self.min_lat},{self.max_lon} {self.min_lat},{self.max_lon} {self.max_lat},{self.min_lon} {self.max_lat},{self.min_lon} {self.min_lat}))"


class CloudCoverageValidator(BaseModel):
    """Валидация облачности"""
    cloud_min: float = Field(0, ge=0, le=100, description="Minimum cloud coverage %")
    cloud_max: float = Field(30, ge=0, le=100, description="Maximum cloud coverage %")
    
    @validator('cloud_max')
    def validate_cloud_range(cls, v, values):
        if 'cloud_min' in values and v < values['cloud_min']:
            raise ValueError('cloud_max must be >= cloud_min')
        return v


class PaginationParams(BaseModel):
    """Валидация пагинации"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.limit


class SatelliteSearchRequest(BaseModel):
    """Запрос на поиск спутниковых данных"""
    date_from: date = Field(..., description="Start date")
    date_to: date = Field(..., description="End date")
    bounds: BoundingBoxValidator
    cloud_max: float = Field(30, ge=0, le=100, description="Max cloud coverage %")
    platform: str = Field("Sentinel-2", description="Satellite platform")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if 'date_from' in values and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        # Limit to 1 year for MVP
        if 'date_from' in values and (v - values['date_from']).days > 365:
            raise ValueError('Date range cannot exceed 365 days')
        return v


class SatelliteFilterParams(BaseModel):
    """Параметры фильтрации спутниковых данных"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    cloud_max: Optional[float] = Field(None, ge=0, le=100)
    platform: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
