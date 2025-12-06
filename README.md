# SattelishMaps

SattelishMaps is a backend system for automated retrieval and analysis of Sentinel-2 satellite imagery. It calculates vegetation (NDVI) and water (NDWI) indices to monitor environmental changes.

## Features

*   **Automated Data Retrieval**: Fetches new satellite imagery from Copernicus Data Space Ecosystem.
*   **Index Calculation**: Computes NDVI and NDWI using spectral bands or metadata estimation.
*   **Geospatial Database**: Stores data in PostgreSQL with PostGIS support.
*   **REST API**: Provides endpoints for frontend integration and data access.
*   **Dockerized**: Fully containerized for easy deployment.

## Documentation

*   [System Architecture](docs/architecture/001-system-architecture.md)
*   [Backend Overview](docs/backend/overview.md)
*   [Scheduler Details](docs/backend/scheduler.md)
*   [API Reference](docs/api/reference.md)
*   [Database Schema](docs/database/schema.md)
*   [Deployment Guide](docs/deployment/docker-setup.md)

## Quick Start

1.  **Configure Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

2.  **Start Services**:
    ```bash
    docker-compose up -d
    ```

3.  **Access API**:
    Open http://localhost:8000/docs for Swagger UI.