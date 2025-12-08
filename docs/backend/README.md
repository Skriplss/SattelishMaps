# Backend Documentation

The backend is built with **FastAPI** to provide a high-performance, asynchronous API for processing satellite imagery and serving geospatial data.

## Directory Structure

```
backend/
├── api/             # API Route Handlers (Endpoints)
├── services/        # Business Logic & External Integrations
├── models/          # Pydantic Data Models
├── utils/           # Helper functions (Image processing, Geometry)
├── config/          # Configuration & Parameter validation
└── scheduler.py     # APScheduler setup for background tasks
```

## Key Components

### API Layer (`api/`)
Handles HTTP requests, validation, and serialization.
- **`satellite.py`**: Endpoints for triggering Sentinel Hub downloads.
- **`indices.py`**: Calculation of NDVI, NDWI, etc.
- **`statistics.py`**: Aggregated statistics for regions.

### Services (`services/`)
- **`sentinel_service.py`**: Communicates with Sentinel Hub API.
- **`image_processor.py`**: Handles raster data using `rasterio`.
- **`database.py`**: Manages Supabase/PostGIS connections.

### Scheduler (`scheduler.py`)
Uses `APScheduler` to run periodic tasks:
- **Daily Data Fetch**: Checks for new satellite passes every 6 hours (configurable).
- **Cleanup**: Removes old temporary files.

## Technologies
- **FastAPI**: Web framework.
- **Rasterio**: Reading/writing GeoTIFFs.
- **Shapely**: Geometric operations (Polygons, validation).
- **AsyncPG**: Asynchronous PostgreSQL driver.
