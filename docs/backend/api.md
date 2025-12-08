# API Reference

The API is built using FastAPI and automatically generates an OpenAPI schema.
Access the interactive documentation at `/docs` (Swagger UI) or `/redoc`.

## Key Endpoints

### 🛰️ Satellite Data

#### `GET /api/satellite/preview`
Get a preview image for a location.
- **Params**: `lat`, `lon`, `date`
- **Response**: JPEG/PNG image bytes.

#### `POST /api/satellite/process`
Trigger a background processing task for a region.
- **Body**: GeoJSON Polygon
- **Response**: Task ID.

### 📊 Statistics & Indices

#### `GET /api/statistics/region`
Retrieve aggregated stats (avg NDVI, etc.) for a named region.
- **Params**: `region_name`, `date_from`, `date_to`

#### `GET /api/indices/{index_type}`
Get raw index values (raster/json).
- **Path**: `index_type` (ndvi, ndwi, ndbi)
- **Params**: `lat`, `lon`

## Error Handling

Standard HTTP status codes are used:
- `200`: Success
- `400`: Validation Error (Invalid coordinates/date)
- `404`: Resource Not Found (Image not available)
- `500`: Internal Server Error (Sentinel Hub connection failed)
