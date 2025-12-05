"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Copernicus
    COPERNICUS_USERNAME: str = ""
    COPERNICUS_PASSWORD: str = ""
    
    # MapTiler
    MAPTILER_API_KEY: str = ""
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create settings instance
settings = Settings()
