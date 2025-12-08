# Backend Scheduler

The scheduler is responsible for keeping the local dataset in sync with Sentinel Hub. It runs as a background process within the FastAPI application.

## Configuration

It is configured via environment variables:
- `SCHEDULER_ENABLED`: Set to `false` to disable (e.g., for API-only instances).
- `SCHEDULER_INTERVAL_HOURS`: How often to check for new data (Default: 6 hours).

## Tasks

### 1. `fetch_new_data`
- **Frequency**: Every `SCHEDULER_INTERVAL_HOURS`.
- **Action**: Queries Sentinel Hub for available scenes in the defined bounding box since the last fetch.
- **Logic**:
    1. Check `last_run` timestamp in database.
    2. Query Sentinel Hub Catalog API.
    3. If new scene exists (cloud cover < threshold), download bands.
    4. Calculate indices (NDVI, etc.).
    5. Save to `tile_cache/` and update Database metadata.

### 2. `cleanup_cache`
- **Frequency**: Daily (Midnight).
- **Action**: Deletes temporary files older than 7 days to save disk space.

## Monitoring

Check scheduler status via the API:
```http
GET /api/scheduler/status
```
Returns:
```json
{
  "running": true,
  "jobs": [
    {
       "id": "fetch_new_data",
       "next_run_time": "2024-12-08T18:00:00"
    }
  ]
}
```
