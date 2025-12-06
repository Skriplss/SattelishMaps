# 🤖 Automated Scheduler Documentation

## Overview

The SattelishMaps backend includes an automated scheduler that periodically fetches new Sentinel-2 satellite data from Copernicus and calculates NDVI and NDWI indices.

## How It Works

### Workflow

1. **Periodic Execution**: Runs every N hours (configurable via `SCHEDULER_INTERVAL_HOURS`)
2. **Search for New Data**: Queries Copernicus API for new Sentinel-2 images
3. **Save to Database**: Stores satellite image metadata in Supabase
4. **Calculate Indices**: Computes NDVI and NDWI for each new image
5. **Store Results**: Saves calculated indices to database

### Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (app.py)      │
└────────┬────────┘
         │
         │ starts/stops
         ▼
┌─────────────────┐
│   Scheduler     │
│ (scheduler.py)  │
└────────┬────────┘
         │
         │ every N hours
         ▼
┌─────────────────┐
│  Fetch Job      │
│  - Search       │
│  - Calculate    │
│  - Save         │
└─────────────────┘
```

## Configuration

### Environment Variables

```bash
# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Run interval in hours
SCHEDULER_INTERVAL_HOURS=6

# Default search area (WKT POLYGON)
DEFAULT_SEARCH_BOUNDS=POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))

# Maximum cloud coverage percentage
DEFAULT_CLOUD_MAX=30.0

# Process historical data on startup
PROCESS_HISTORICAL_DATA=false
```

### Customizing Search Area

The `DEFAULT_SEARCH_BOUNDS` uses WKT (Well-Known Text) format for defining the search polygon:

```
POLYGON((lon1 lat1, lon2 lat2, lon3 lat3, lon4 lat4, lon1 lat1))
```

**Example areas:**

- **Central Europe**: `POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))`
- **Ukraine**: `POLYGON((22 44, 40 44, 40 52, 22 52, 22 44))`
- **Custom area**: Use [geojson.io](https://geojson.io) to draw your area and convert to WKT

## Monitoring

### Check Scheduler Status

```bash
curl http://localhost:8000/api/scheduler/status
```

**Response:**
```json
{
  "enabled": true,
  "running": true,
  "interval_hours": 6,
  "last_run": "2025-12-06T00:30:00",
  "next_run": "2025-12-06T06:30:00",
  "total_runs": 5,
  "successful_runs": 4,
  "failed_runs": 1,
  "search_bounds": "POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))",
  "max_cloud_coverage": 30.0
}
```

### View Logs

**Docker:**
```bash
docker-compose logs -f backend | grep scheduler
```

**Local:**
```bash
tail -f logs/app.log | grep scheduler
```

### Log Output Example

```
🛰️  Starting automated Sentinel-2 data fetch and processing
Searching Copernicus: 2025-11-29 to 2025-12-06
Bounds: POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))
Max cloud coverage: 30%
Found 12 new Sentinel-2 products
Saved 12 products to database
Calculating NDVI for S2A_MSIL2A_20251205...
Calculating NDWI for S2A_MSIL2A_20251205...
✅ Processed S2A_MSIL2A_20251205
✅ Scheduler job completed successfully
   Products found: 12
   Products saved: 12
   Products processed: 12
```

## Manual Operations

### Trigger Manual Run

The scheduler runs automatically, but you can also manually calculate indices for specific images:

```bash
# Calculate indices for a specific image
curl -X POST http://localhost:8000/api/indices/calculate/{image_id}

# Force recalculation
curl -X POST "http://localhost:8000/api/indices/calculate/{image_id}?force=true"
```

### Disable Scheduler

Set in `.env`:
```bash
SCHEDULER_ENABLED=false
```

Or restart with environment variable:
```bash
docker-compose up -d -e SCHEDULER_ENABLED=false
```

## Troubleshooting

### Scheduler Not Running

**Check status:**
```bash
curl http://localhost:8000/api/scheduler/status
```

**Verify configuration:**
```bash
docker-compose exec backend env | grep SCHEDULER
```

### No New Data Found

**Possible reasons:**
1. No new images in the specified area/date range
2. All images exceed cloud coverage threshold
3. Copernicus API credentials not configured

**Solutions:**
- Increase `DEFAULT_CLOUD_MAX`
- Expand `DEFAULT_SEARCH_BOUNDS`
- Set `PROCESS_HISTORICAL_DATA=true` for initial run

### Copernicus API Errors

**Rate limiting:**
- Scheduler includes exponential backoff retry logic
- Free tier has limits: ~2 requests/second
- Consider increasing `SCHEDULER_INTERVAL_HOURS`

**Authentication errors:**
- Verify `COPERNICUS_USERNAME` and `COPERNICUS_PASSWORD`
- Register at [Copernicus Open Access Hub](https://scihub.copernicus.eu/dhus/#/self-registration)

### Database Errors

**Connection issues:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase dashboard for service status

**Schema errors:**
- Ensure database schema is up to date
- Run migrations: `database/schemas/sentinel2_schema.sql`

## Performance Considerations

### Resource Usage

- **Memory**: ~200-500MB per run (MVP mode)
- **CPU**: Low (metadata processing only)
- **Network**: ~1-5MB per search query
- **Storage**: ~1KB per image metadata

### Optimization Tips

1. **Adjust interval**: Balance freshness vs. resource usage
2. **Limit search area**: Smaller bounds = faster queries
3. **Cloud threshold**: Lower threshold = fewer results
4. **Batch processing**: Scheduler processes up to 20 products per run

## Production Recommendations

### High-Availability Setup

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

### Monitoring Integration

Add monitoring tools:
- **Prometheus**: Metrics export
- **Grafana**: Dashboards
- **Sentry**: Error tracking

### Backup Strategy

- Database: Supabase automatic backups
- Logs: Rotate and archive daily
- Configuration: Version control `.env`

## Future Enhancements

### Planned Features

1. **Full GeoTIFF Processing**: Download and process actual band data
2. **Multi-Region Support**: Configure multiple search areas
3. **Smart Scheduling**: Adjust interval based on data availability
4. **Notification System**: Email/webhook alerts for new data
5. **Celery Integration**: Distributed task processing
6. **Redis Caching**: Cache API responses

### Migration Path

Current MVP uses metadata estimation. To upgrade to full processing:

1. Enable GeoTIFF download in `copernicus_service.py`
2. Use `calculate_ndvi_from_bands()` instead of `calculate_ndvi_from_metadata()`
3. Add storage for downloaded files (S3/MinIO)
4. Increase scheduler interval (processing takes longer)

## Support

For issues or questions:
- Check logs first
- Review configuration
- Consult API documentation at `/docs`
- Check Copernicus API status
