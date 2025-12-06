# Backend Service Documentation

The backend is built with **FastAPI** and served via **Uvicorn**. It acts as the core orchestration layer for data fetching, processing, and serving.

## Directory Structure

```
backend/
├── api/             # API Route Handlers
├── config/          # Environment Configuration
├── services/        # Business Logic & External Integrations
│   ├── copernicus_service.py
│   ├── ndvi_calculator.py
│   ├── ndwi_calculator.py
│   └── supabase_service.py
├── scripts/         # Utility Scripts (Import/Fetch)
├── app.py           # Application Entry Point
└── scheduler.py     # Job Scheduling
```

## Core Services

### Scheduler
*   **File**: `backend/scheduler.py`
*   **Function**: Runs every 6 hours (configurable via `SCHEDULER_INTERVAL_HOURS`).
*   **Job**: `fetch_and_process_sentinel_data`.
*   **Behavior**: Searches for new imagery in the configured AOI (Area of Interest), saves metadata, and triggers index calculation.

### Copernicus Service
*   **File**: `backend/services/copernicus_service.py`
*   **Function**: Interacts with Copernicus Data Space Ecosystem (CDSE).
*   **Auth**: Uses OData credentials from environment variables.

### Index Calculators
*   **Files**: `ndvi_calculator.py`, `ndwi_calculator.py`
*   **Methods**:
    *   `calculate_from_bands`: Uses Rasterio to read .jp2 files and compute indices using numpy arrays.
    *   `calculate_from_metadata`: Fallback estimation based on cloud coverage and seasonality.

## Manual Data Import
Due to API rate limits or restrictions, a manual import workflow is supported.
Scripts located in `backend/scripts/import_safe_data.py` parse local `.SAFE` directories and ingest them into the system.
