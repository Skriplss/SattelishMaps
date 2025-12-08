# 001. Technology Stack Selection

## Status
ACCEPTED

## Context
We are building SattelishMaps, a system for analyzing satellite imagery (Sentinel-2) and visualizing environmental indices.
We need a stack that supports:
- Efficient processing of large geospatial data (raster images).
- Interactive, responsive mapping on the frontend.
- Robust storage for geospatial vector data (regions, sales).
- Ease of deployment and maintenance.

## Decision

### Backend: FastAPI & Python 3.11+
- **Why**: Python is the standard for data science and geospatial processing (`rasterio`, `shapely`, `numpy`).
- **Framework**: FastAPI provides high performance (async), automatic OpenAPI documentation, and easy type safety integration (Pydantic).
- **Asynchrony**: Essential for handling long-running external API calls (Sentinel Hub) without blocking.

### Frontend: Vanilla JS + MapLibre GL JS
- **Why**: The project requirements emphasize simplicity and performance.
- **Library**: MapLibre GL JS is an open-source fork of Mapbox GL JS, ensuring no license fees while providing GPU-accelerated vector tile rendering.
- **No Framework**: For this scale, a full SPA framework (React/Vue) adds unnecessary build complexity. Modern Vanilla JS (ES6+) is sufficient.

### Database: Supabase (PostgreSQL + PostGIS)
- **Why**: We need to store complex geometries (Admin boundaries).
- **Extension**: PostGIS is the industry standard for spatial databases.
- **Provider**: Supabase offers a managed Postgres instance with easy setup, alleviating the burden of maintaining a database cluster.

### Infrastructure: Docker
- **Why**: Ensures consistency across development and production environments. Simplifies the "works on my machine" problem.

## Consequences

### Pros
- **Performance**: High-speed API and client-side rendering.
- **Ecosystem**: Access to the rich Python geospatial ecosystem.
- **Cost**: Open-source tools (MapLibre) avoid vendor lock-in and fees.

### Cons
- **Complexity**: Managing geospatial libraries in Docker can be tricky (GDAL dependencies).
- **Learning Curve**: PostGIS syntax requires specific SQL knowledge.
