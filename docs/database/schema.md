# Database Schema

The project uses **Supabase (PostgreSQL)** with **PostGIS** for geospatial data storage.

## Core Tables

### 1. `satellite_images`
Stores metadata about Sentinel-2 products retrieved from Copernicus.

*   `id`: UUID (PK)
*   `product_id`: Unique Copernicus identifier (e.g., `S2A_MSIL2A...`)
*   `acquisition_date`: Timestamp of capture
*   `cloud_coverage`: Percentage (0-100)
*   `bounds`: PostGIS POLYGON of the image footprint
*   `metadata`: JSONB for extra attributes

### 2. `ndvi_data`
Stores calculated Normalized Difference Vegetation Index (NDVI) results.

*   `image_id`: FK to `satellite_images`
*   `ndvi_mean`: Float (-1 to 1)
*   `vegetation_category`: Enum ('bare_soil', 'sparse', 'moderate', 'dense')
*   `metadata`: JSONB containing calculation details (e.g., method used)

### 3. `ndwi_data`
Stores calculated Normalized Difference Water Index (NDWI) results.

*   `image_id`: FK to `satellite_images`
*   `ndwi_mean`: Float (-1 to 1)
*   `water_category`: Enum ('no_water', 'low', 'moderate', 'high')

## Setup
The schema initialization script is located at:
`database/schemas/sentinel2_schema.sql`

## Example Queries

### Find Clean Images with High Vegetation
```sql
SELECT si.product_id, si.acquisition_date, nd.ndvi_mean
FROM satellite_images si
JOIN ndvi_data nd ON si.id = nd.image_id
WHERE si.cloud_coverage < 10
  AND nd.ndvi_mean > 0.6;
```
