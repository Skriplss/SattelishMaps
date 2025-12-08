# Database Schema

The project uses **Supabase (PostgreSQL)** with **PostGIS** for geospatial data storage.

## Core Tables

### 1. `satellite_images`
Stores metadata about Sentinel-2 products retrieved from Copernicus/Sentinel Hub.

- **`id`**: `UUID` (Primary Key)
- **`product_id`**: `TEXT` - Unique Copernicus identifier (e.g., `S2A_MSIL2A...`)
- **`acquisition_date`**: `TIMESTAMP` - Timestamp of capture
- **`cloud_coverage`**: `FLOAT` - Percentage (0-100)
- **`bounds`**: `GEOMETRY(POLYGON, 4326)` - PostGIS footprint of the image
- **`metadata`**: `JSONB` - Extra attributes

### 2. `ndvi_data`
Stores calculated Normalized Difference Vegetation Index (NDVI) results.

- **`image_id`**: `UUID` (Foreign Key to `satellite_images.id`)
- **`ndvi_mean`**: `FLOAT` (-1.0 to 1.0)
- **`vegetation_category`**: `ENUM` - `['bare_soil', 'sparse', 'moderate', 'dense']`
- **`metadata`**: `JSONB` - Calculation details

### 3. `ndwi_data`
Stores calculated Normalized Difference Water Index (NDWI) results.

- **`image_id`**: `UUID` (Foreign Key to `satellite_images.id`)
- **`ndwi_mean`**: `FLOAT` (-1.0 to 1.0)
- **`water_category`**: `ENUM` - `['no_water', 'low', 'moderate', 'high']`

## Setup
The schema initialization script is located at `database/schemas/sentinel2_schema.sql` (if available in the repo).
