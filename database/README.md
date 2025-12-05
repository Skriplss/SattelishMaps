# 🗄️ Database Schema Documentation

## Overview

Database schema for Sentinel-2 satellite data with NDVI and NDWI indices.

## Tables

### 1. `satellites`
Stores satellite platform information.

**Columns:**
- `id` - UUID primary key
- `name` - Satellite name (e.g., 'Sentinel-2A')
- `platform` - Platform type ('Sentinel-2')
- `description` - Description
- `active` - Is satellite active
- `created_at` - Creation timestamp

### 2. `satellite_images`
Stores metadata about satellite images from Copernicus.

**Columns:**
- `id` - UUID primary key
- `satellite_id` - Reference to satellites table
- `product_id` - Copernicus product ID (unique)
- `title` - Image title
- `acquisition_date` - When image was captured
- `processing_date` - When image was processed
- `center_point` - Center coordinates (PostGIS POINT)
- `bounds` - Bounding box (PostGIS POLYGON)
- `cloud_coverage` - Cloud coverage percentage (0-100)
- `thumbnail_url` - URL to thumbnail
- `preview_url` - URL to preview
- `download_url` - URL to download
- `metadata` - Additional metadata (JSONB)
- `created_at`, `updated_at` - Timestamps

### 3. `user_requests`
Stores user search and analysis requests.

**Columns:**
- `id` - UUID primary key
- `request_type` - Type: 'search', 'analysis', 'download'
- `area_name` - Name of area
- `bounds` - Search area (PostGIS POLYGON)
- `date_from`, `date_to` - Date range
- `max_cloud_coverage` - Maximum cloud coverage filter
- `parameters` - Additional parameters (JSONB)
- `status` - 'pending', 'processing', 'completed', 'failed'
- `result_count` - Number of results
- `created_at`, `completed_at` - Timestamps

### 4. `ndvi_data`
Stores NDVI (Normalized Difference Vegetation Index) calculations.

**NDVI Formula:** `(NIR - Red) / (NIR + Red)`

**Columns:**
- `id` - UUID primary key
- `image_id` - Reference to satellite_images
- `request_id` - Reference to user_requests
- `ndvi_mean` - Mean NDVI value (-1 to 1)
- `ndvi_min`, `ndvi_max` - Min/max values
- `ndvi_std` - Standard deviation
- `ndvi_median` - Median value
- `vegetation_category` - 'bare_soil', 'sparse', 'moderate', 'dense'
- `vegetation_percentage` - Percentage of area with vegetation
- `area_coverage` - Area in square meters
- `location` - Center point (PostGIS POINT)
- `quality_score` - Data quality (0-1)
- `metadata` - Additional data (JSONB)
- `calculated_at` - Calculation timestamp

**NDVI Interpretation:**
- `-1 to 0` - Water, bare soil, rocks
- `0 to 0.2` - Bare soil, sparse vegetation
- `0.2 to 0.5` - Moderate vegetation
- `0.5 to 1` - Dense vegetation, healthy plants

### 5. `ndwi_data`
Stores NDWI (Normalized Difference Water Index) calculations.

**NDWI Formula:** `(Green - NIR) / (Green + NIR)`

**Columns:**
- `id` - UUID primary key
- `image_id` - Reference to satellite_images
- `request_id` - Reference to user_requests
- `ndwi_mean` - Mean NDWI value (-1 to 1)
- `ndwi_min`, `ndwi_max` - Min/max values
- `ndwi_std` - Standard deviation
- `ndwi_median` - Median value
- `water_category` - 'no_water', 'low', 'moderate', 'high'
- `water_percentage` - Percentage of area with water
- `area_coverage` - Area in square meters
- `location` - Center point (PostGIS POINT)
- `quality_score` - Data quality (0-1)
- `metadata` - Additional data (JSONB)
- `calculated_at` - Calculation timestamp

**NDWI Interpretation:**
- `< 0` - No water
- `0 to 0.2` - Low water content
- `0.2 to 0.5` - Moderate water content
- `> 0.5` - High water content, water bodies

## Indexes

Performance indexes created on:
- `satellite_images`: acquisition_date, cloud_coverage, product_id, spatial (center_point, bounds)
- `user_requests`: status, created_at, spatial (bounds)
- `ndvi_data`: image_id, request_id, ndvi_mean, spatial (location)
- `ndwi_data`: image_id, request_id, ndwi_mean, spatial (location)

## Views

### `latest_satellite_data`
Combines satellite images with NDVI and NDWI data for easy querying.

## Example Queries

### Get images with high vegetation
```sql
SELECT si.*, nd.ndvi_mean, nd.vegetation_category
FROM satellite_images si
JOIN ndvi_data nd ON si.id = nd.image_id
WHERE nd.ndvi_mean > 0.5
  AND si.cloud_coverage < 20
ORDER BY si.acquisition_date DESC;
```

### Get images with water bodies
```sql
SELECT si.*, nw.ndwi_mean, nw.water_category
FROM satellite_images si
JOIN ndwi_data nw ON si.id = nw.image_id
WHERE nw.ndwi_mean > 0.3
ORDER BY si.acquisition_date DESC;
```

### Search images in bounding box
```sql
SELECT *
FROM satellite_images
WHERE ST_Intersects(
    bounds,
    ST_GeogFromText('POLYGON((12 48, 16 48, 16 52, 12 52, 12 48))')
)
AND cloud_coverage < 30;
```

## Setup Instructions

1. Open Supabase SQL Editor
2. Copy contents of `sentinel2_schema.sql`
3. Run the SQL script
4. Verify tables are created in Table Editor

## Notes

- PostGIS extension is required for spatial queries
- Row Level Security (RLS) is enabled with public read access for MVP
- In production, restrict RLS policies based on user authentication
