# 🚀 Quick Start Guide - Automated NDVI/NDWI System

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Supabase account with database setup
- Copernicus Open Access Hub account

## Setup Instructions

### 1. Clone and Navigate

```bash
cd /home/dmytro/Repository/V-Axis/Hackaton-MTF-2025/SattelishMaps
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required credentials:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `COPERNICUS_USERNAME`: Your Copernicus username
- `COPERNICUS_PASSWORD`: Your Copernicus password

### 3. Setup Database

1. Open Supabase SQL Editor
2. Run the schema: `database/schemas/sentinel2_schema.sql`
3. Verify tables are created: `satellites`, `satellite_images`, `ndvi_data`, `ndwi_data`, `user_requests`

### 4. Install Dependencies

**Option A: Local Development**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Option B: Docker (Recommended)**
```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## Running the Application

### Local Development

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker-compose up -d
```

## Verify Installation

### 1. Check Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "SattelishMaps Backend is running",
  "version": "1.0.0",
  "environment": "development"
}
```

### 2. Check Scheduler Status

```bash
curl http://localhost:8000/api/scheduler/status
```

Expected response:
```json
{
  "enabled": true,
  "running": true,
  "interval_hours": 6,
  "last_run": null,
  "next_run": "2025-12-06T06:30:00",
  ...
}
```

### 3. Access API Documentation

Open in browser: http://localhost:8000/docs

## Testing the System

### Manual Search and Processing

```bash
# Search for Sentinel-2 data
curl -X POST http://localhost:8000/api/satellite-data/search \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-11-29",
    "date_to": "2025-12-06",
    "bounds": {
      "min_lat": 48,
      "max_lat": 52,
      "min_lon": 12,
      "max_lon": 16
    },
    "cloud_max": 30
  }'
```

### Get Satellite Images

```bash
curl http://localhost:8000/api/satellite-data
```

### Calculate Indices for an Image

```bash
# Replace {image_id} with actual UUID from previous response
curl -X POST http://localhost:8000/api/indices/calculate/{image_id}
```

### Get NDVI/NDWI Data

```bash
# Get NDVI data
curl http://localhost:8000/api/ndvi/{image_id}

# Get NDWI data
curl http://localhost:8000/api/ndwi/{image_id}

# Get both indices
curl http://localhost:8000/api/indices/{image_id}
```

## Scheduler Configuration

The scheduler automatically runs every 6 hours by default. Configure in `.env`:

```bash
# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Interval in hours
SCHEDULER_INTERVAL_HOURS=6

# Search area (WKT POLYGON)
DEFAULT_SEARCH_BOUNDS=POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))

# Maximum cloud coverage
DEFAULT_CLOUD_MAX=30.0

# Process historical data on startup
PROCESS_HISTORICAL_DATA=false
```

## Monitoring Logs

### Docker

```bash
# All logs
docker-compose logs -f backend

# Scheduler logs only
docker-compose logs -f backend | grep scheduler

# NDVI/NDWI processing logs
docker-compose logs -f backend | grep -E "NDVI|NDWI"
```

### Local

```bash
# View application logs
tail -f logs/app.log

# Filter for scheduler
tail -f logs/app.log | grep scheduler
```

## Troubleshooting

### Scheduler Not Starting

1. Check `.env`: `SCHEDULER_ENABLED=true`
2. Verify Copernicus credentials
3. Check logs for errors

### No Data Found

1. Verify search bounds cover your area of interest
2. Increase `DEFAULT_CLOUD_MAX`
3. Check Copernicus API status

### Database Errors

1. Verify Supabase credentials
2. Ensure schema is created
3. Check Supabase dashboard for errors

## Next Steps

1. **Customize Search Area**: Edit `DEFAULT_SEARCH_BOUNDS` in `.env`
2. **Adjust Scheduler**: Change `SCHEDULER_INTERVAL_HOURS` as needed
3. **Monitor Data**: Check Supabase dashboard for new data
4. **Integrate Frontend**: Use API endpoints in your frontend application

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/satellite-data` | GET | List satellite images |
| `/api/satellite-data/{id}` | GET | Get specific image |
| `/api/satellite-data/search` | POST | Search Copernicus |
| `/api/ndvi/{image_id}` | GET | Get NDVI data |
| `/api/ndwi/{image_id}` | GET | Get NDWI data |
| `/api/indices/{image_id}` | GET | Get both indices |
| `/api/indices/calculate/{image_id}` | POST | Calculate indices |
| `/api/scheduler/status` | GET | Scheduler status |

## Documentation

- **Scheduler**: See `docs/SCHEDULER.md`
- **Database**: See `database/README.md`
- **Backend Setup**: See `docs/BACKEND_SETUP.md`
- **API Docs**: http://localhost:8000/docs

## Support

For issues or questions, check:
1. Application logs
2. Supabase dashboard
3. Copernicus API status
4. API documentation at `/docs`
