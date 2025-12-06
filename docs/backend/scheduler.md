# Automated Scheduler Documentation

## Overview
The SattelishMaps backend includes an automated scheduler that periodically fetches new Sentinel-2 satellite data from Copernicus and calculates NDVI and NDWI indices.

## How It Works

### Workflow
1. **Periodic Execution**: Runs every N hours (configurable via `SCHEDULER_INTERVAL_HOURS`).
2. **Search for New Data**: Queries Copernicus API for new Sentinel-2 images.
3. **Save to Database**: Stores metadata in Supabase.
4. **Calculate Indices**: Computes NDVI and NDWI for each new image.
5. **Store Results**: Saves calculated indices to the database.

### Architecture
The scheduler is integrated into the FastAPI application lifecycle. It starts when the application starts (`app.py` lifespan) and runs in the background.

## Configuration

Environment variables control the scheduler behavior:

*   `SCHEDULER_ENABLED`: Set to `true` to enable.
*   `SCHEDULER_INTERVAL_HOURS`: Frequency of checks (default: 6).
*   `DEFAULT_SEARCH_BOUNDS`: WKT Polygon defining the Area of Interest (AOI).
*   `DEFAULT_CLOUD_MAX`: Maximum allowed cloud coverage percentage (default: 30.0).
*   `PROCESS_HISTORICAL_DATA`: Set to `true` to process past data on startup (default: `false`).

## Monitoring

### Status Endpoint
`GET /api/scheduler/status`

Returns the current state:
```json
{
  "enabled": true,
  "running": true,
  "interval_hours": 6,
  "last_run": "2025-12-06T00:30:00",
  "next_run": "2025-12-06T06:30:00",
  "total_runs": 5,
  "successful_runs": 4,
  "failed_runs": 1
}
```

### Manual Trigger
You can force index calculation for a specific image via API:
`POST /api/indices/calculate/{image_id}?force=true`

## Production Notes
*   **Rate Limiting**: The scheduler handles Copernicus API rate limits with exponential backoff.
*   **Resource Usage**: Consumes minimal resources in metadata mode; GeoTIFF processing is more CPU/RAM intensive.
*   **Logs**: Check `docker-compose logs backend` for `[scheduler]` tagged logs.
