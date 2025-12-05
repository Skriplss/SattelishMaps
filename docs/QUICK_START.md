# 🚀 Quick Start: Fetch Sentinel-2 Data

## 1. Create .env file

Create `.env` file in root directory with these credentials:

```env
# Supabase
SUPABASE_URL=https://azmpfnyplomrmlgjpqew.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6bXBmbnlwbG9tcm1sZ2pwcWV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5NDcxMzgsImV4cCI6MjA4MDUyMzEzOH0.SkyK6vl9p9vJkAzgVFD_rClmIbjkAC3qNhEyAgt300Y
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6bXBmbnlwbG9tcm1sZ2pwcWV3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDk0NzEzOCwiZXhwIjoyMDgwNTIzMTM4fQ.jIWe-nrvbRAAwlUVVLu_3UXm50A6ax3AHj_qGFfOmhA

# Copernicus (optional for now)
COPERNICUS_USERNAME=
COPERNICUS_PASSWORD=

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

## 2. Setup Database

1. Open Supabase SQL Editor: https://azmpfnyplomrmlgjpqew.supabase.co
2. Copy SQL from `database/schemas/sentinel2_schema.sql`
3. Run the script
4. Verify tables created: satellites, satellite_images, user_requests, ndvi_data, ndwi_data

## 3. Run Backend

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

## 4. Test API

Open: http://localhost:5000/docs

### Search Sentinel-2 Data

POST `/api/satellite-data/search`

```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-05",
  "bounds": {
    "min_lat": 48.0,
    "max_lat": 52.0,
    "min_lon": 12.0,
    "max_lon": 16.0
  },
  "cloud_max": 30
}
```

This will:
1. Search Copernicus for Sentinel-2 images
2. Save found images to Supabase
3. Return list of products

### Get Saved Images

GET `/api/satellite-data?limit=10&cloud_max=20`

Returns images from Supabase database.

## What's Working

✅ Sentinel-2 API integration
✅ Automatic save to Supabase
✅ Database schema with NDVI/NDWI tables
✅ Search by date range and cloud coverage
✅ Spatial queries support

## Next Steps

1. Add NDVI calculation service
2. Add NDWI calculation service  
3. Process downloaded images
4. Calculate vegetation/water indices
