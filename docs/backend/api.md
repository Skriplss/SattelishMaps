# REST API Reference

Base URL: `http://localhost:8000`. Interactive OpenAPI docs at `/docs`
(enabled when `DEBUG=true`).

All JSON endpoints return the standard envelope:

```json
{ "success": true, "message": "...", "data": ..., "timestamp": "..." }
```

Common validation (shared, `utils/validation.py`):

- `index_type` ∈ `NDVI | NDWI | NDBI | MOISTURE` (case-insensitive) → else 400
- dates must be `YYYY-MM-DD` → else 400
- bboxes must intersect `COVERAGE_BBOX` (Slovakia) → else 400 (or transparent tile)

## Service

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + database connectivity (`status: ok / degraded`) |
| GET | `/` | Welcome + links |
| GET | `/api/scheduler/status` | Scheduler state, run counters, last run |

## Map tiles & images

| Method | Path | Description |
|---|---|---|
| GET | `/api/wms/tile/{z}/{x}/{y}.png?date&index_type` | Map tile. Order: cache → *(optional)* pixel render → Sentinel Hub. Response header `X-Tile-Cache: HIT / PIXEL / MISS / OUT_OF_COVERAGE` |
| GET | `/api/wms/image?bbox&date&index_type&width&height` | Arbitrary-bbox rendered PNG (`bbox=min_lon,min_lat,max_lon,max_lat`) |
| GET | `/api/tiles/pixel/{z}/{x}/{y}.png?date&index_type` | Tile rendered **from stored pixel_data** (no Sentinel Hub, no quota). Transparent where no data; header `X-Pixel-Data: HIT / EMPTY` |
| POST | `/api/tiles/cache?z&x&y&date&index_type` | Fetch a tile from Sentinel Hub and store it in the cache |

## Pixel data & area analytics

All endpoints take a bbox as `min_lat, max_lat, min_lon, max_lon` query params.

| Method | Path | Extra params | Returns |
|---|---|---|---|
| POST | `/api/tiles/fetch-pixels` | `date`, `resolution` (10–500) | Fetches raw FLOAT32 values for all 4 indices **in parallel** and upserts into `pixel_data` |
| GET | `/api/tiles/area/stats` | `date`, `index_type` | `mean, median, min, max, std, pixel_count` |
| GET | `/api/tiles/area/timeseries` | `index_type`, `date_from`, `date_to` | `[{date, mean, min, max, pixel_count}]` |
| GET | `/api/tiles/area/histogram` | `date`, `index_type`, `bins` (4–100) | `[{range_min, range_max, count}]` |
| GET | `/api/tiles/area/change` | `date_a`, `date_b`, `index_type`, `threshold` | `mean_a, mean_b, mean_diff, improved / declined / stable / pixel counts` |

> Change detection joins pixels on exact coordinates — fetch both dates with
> the same bbox and resolution, or the join finds no pairs.

## Region statistics

| Method | Path | Description |
|---|---|---|
| GET | `/api/statistics/regions` | Distinct region names present in the DB |
| GET | `/api/statistics/region?date&index_type[&region_name]` | GeoJSON FeatureCollection of region stats for a date |
| GET | `/api/statistics/region/dates[?index_type&region_name]` | Available dates |
| GET | `/api/statistics/timeseries/{region}?index_type[&date_from&date_to&limit]` | Region timeseries |

## Sentinel Hub catalog

| Method | Path | Description |
|---|---|---|
| GET | `/api/sentinelhub/catalog/search?min_lat&…&date_from&date_to&cloud_max&limit` | Scene availability straight from the Sentinel Hub Catalog (not the local DB) |

## Error semantics

| Code | Meaning |
|---|---|
| 400 | Validation failure (index type, date format, out-of-coverage bbox) |
| 404 | `not_found` — e.g. no region statistics for the requested date |
| 422 | Request parameter validation (FastAPI/Pydantic) |
| 500 | `database_error` / `internal_server_error` |

Error body:

```json
{ "success": false, "error": "validation_error", "message": "...", "status_code": 400 }
```
