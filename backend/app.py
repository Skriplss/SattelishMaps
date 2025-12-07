"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from utils.logger import setup_logging
from utils.error_handlers import register_exception_handlers
from api import satellite, statistics, indices, region_statistics
from scheduler import satellite_scheduler



# Setup logging
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="logs/app.log" if settings.ENVIRONMENT == "production" else None
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting SattelishMaps Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Start scheduler
    satellite_scheduler.start()
    
    yield
    
    # Stop scheduler
    logger.info("Shutting down SattelishMaps Backend...")
    satellite_scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title="SattelishMaps API",
    description="Backend API for satellite data visualization",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Register exception handlers
register_exception_handlers(app)


# Register routers (order matters! More specific routes first)
app.include_router(region_statistics.router, prefix="/api", tags=["Region Statistics"])
app.include_router(satellite.router, prefix="/api", tags=["Satellite Data"])
app.include_router(statistics.router, prefix="/api", tags=["Statistics"])
app.include_router(indices.router, prefix="/api", tags=["Indices"])



# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health status"""
    return {
        "status": "ok",
        "message": "SattelishMaps Backend is running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SattelishMaps API",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health"
    }


@app.get("/api/scheduler/status", tags=["Scheduler"])
async def scheduler_status():
    """Get scheduler status and statistics"""
    return satellite_scheduler.get_status()
