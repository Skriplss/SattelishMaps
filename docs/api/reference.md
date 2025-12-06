# API Reference

The application exposes a RESTful API for accessing satellite data and calculated indices.

## Base URL
`http://localhost:8000`

## Endpoints

### Satellite Data

#### `GET /api/satellite-data`
Retrieve a paginated list of available satellite images.

*   **Query Params**:
    *   `limit` (int, default=10): Number of records.
    *   `offset` (int, default=0): Pagination offset.
*   **Response**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "uuid",
          "product_id": "S2A_MSIL2A...",
          "cloud_coverage": 15.5,
          "acquisition_date": "2024-12-05T10:00:00"
        }
      ]
    }
    ```

#### `GET /api/satellite-data/search`
Trigger an immediate search for new data from Copernicus.

*   **Body**:
    *   `min_cloud`: float
    *   `max_cloud`: float
    *   `start_date`: string (ISO)
    *   `end_date`: string (ISO)

### Indices

#### `GET /api/indices/{image_id}`
Get calculated NDVI and NDWI indices for a specific image.

*   **Path Params**: `image_id` (UUID)
*   **Response**:
    ```json
    {
      "ndvi": {
        "mean": 0.45,
        "category": "moderate_vegetation"
      },
      "ndwi": {
        "mean": 0.12,
        "category": "low_water"
      }
    }
    ```

#### `GET /api/ndvi/{image_id}`
Get only NDVI data.

#### `GET /api/ndwi/{image_id}`
Get only NDWI data.

### System

#### `GET /health`
Health check endpoint. Returns `{"status": "ok"}`.

#### `GET /api/scheduler/status`
Returns the current status of the background scheduler (running/stopped, next run time).
