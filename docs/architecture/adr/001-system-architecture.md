# Architecture Decision Record (ADR)

## Context
The project requires an automated system to retrieve, store, and process Sentinel-2 satellite imagery to calculate vegetation (NDVI) and water (NDWI) indices. The system must operate autonomously, handle large geospatial datasets, and provide an API for frontend consumption.

## Decision
We adopted a microservice-like architecture using **FastAPI** for the backend, **Supabase (PostgreSQL + PostGIS)** for storage, and **Docker** for containerization.

### Key Components

1.  **Backend (FastAPI)**:
    *   Handles HTTP requests.
    *   Manages background tasks via APScheduler.
    *   Exposes REST endpoints for data retrieval.

2.  **Data Acquisition**:
    *   Primary: CDSE (Copernicus Data Space Ecosystem) OData API.
    *   Fallback: Manual import of `.SAFE` archives via local script.

3.  **Processing Engine**:
    *   **Rasterio**: Used for processing raw GeoTIFF bands (B04, B08, B03) to calculate indices pixel-by-pixel.
    *   **Metadata Estimation (MVP)**: Fallback mechanism to estimate indices when raw bands are unavailable.

4.  **Database (Supabase)**:
    *   Stores metadata in `satellite_images`.
    *   Stores calculated indices in `ndvi_data` and `ndwi_data`.
    *   Uses PostGIS for geospatial queries (e.g., "find images within polygon").

## Consequences
*   **Pros**: Modular design, easy to deploy (Docker), scalable database (Postgres), robust processing (Rasterio).
*   **Cons**: Processing high-resolution GeoTIFFs is CPU/RAM intensive; manual import is required if API access is restricted.
