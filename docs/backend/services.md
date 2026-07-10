# Service Layer

All business logic lives in `backend/services/` as module-level singletons.

| Service | File | Responsibility |
|---|---|---|
| `supabase_service` | `supabase_service.py` | The only entry point to the database (PostgREST + RPC) |
| `sentinel_hub_wms_service` | `sentinel_hub_wms_service.py` | Sentinel Hub **Process API** via raw HTTP: rendered PNGs and raw FLOAT32 pixel values. OAuth token caching, pooled `requests.Session`, 60 s timeouts |
| `sentinelhub_service` | `sentinelhub_service.py` | Sentinel Hub **Statistical + Catalog API** via the `sentinelhub` SDK (aggregated NDVI/NDWI stats for the scheduler) |
| `tile_cache_service` | `tile_cache_service.py` | Tile caching, pixel-data pipeline, area analytics RPC calls, DB-side tile rendering |
| `pixel_tile_renderer` | `pixel_tile_renderer.py` | Pure functions: value grid → colored PNG (palettes identical to the evalscripts) |

## Tile serving pipeline

`GET /api/wms/tile/{z}/{x}/{y}.png` — the endpoint the map actually calls:

```mermaid
sequenceDiagram
    participant M as Map (MapLibre)
    participant W as wms.py
    participant TC as tile_cache (DB)
    participant PD as pixel_data (DB)
    participant SH as Sentinel Hub

    M->>W: GET /wms/tile/z/x/y.png?date&index_type

    alt tile outside COVERAGE_BBOX
        W-->>M: transparent PNG (X-Tile-Cache: OUT_OF_COVERAGE)
    end

    W->>TC: RPC get_cached_tile(z,x,y,date,index)
    alt cache hit
        TC-->>W: base64 PNG (+bumps access stats)
        W-->>M: PNG (HIT)
    else PREFER_PIXEL_TILES=true and data exists
        W->>PD: RPC get_pixel_grid(bbox, date, index, 64)
        PD-->>W: ≤64×64 value cells
        W->>W: colorize + upscale (NEAREST)
        W-->>M: PNG (PIXEL)
    else miss
        W->>SH: Process API (PNG, ±7 days, cloud ≤50%)
        SH-->>W: rendered tile
        W->>TC: store_tile (base64, upsert)
        W-->>M: PNG (MISS)
    end
```

Cache failures never fail tile serving — `store_tile` errors are logged and
swallowed. Stale tiles are evicted daily (see [scheduler.md](scheduler.md)).

## Pixel data pipeline

`POST /api/tiles/fetch-pixels` / `scripts/fetch_pixel_data.py`:

```mermaid
flowchart TB
    A["Request: bbox + date + resolution"] --> B["Warm OAuth token"]
    B --> C["asyncio.gather — 4 indices in parallel"]
    C --> D1["NDVI<br/>FLOAT32 TIFF"]
    C --> D2["NDWI"]
    C --> D3["NDBI"]
    C --> D4["MOISTURE"]
    D1 & D2 & D3 & D4 --> E["numpy: validity masks<br/>(dataMask > 0, finite values)"]
    E --> F["pixel rows for cells where<br/>any index is valid"]
    F --> G["RPC ensure_pixel_data_partition(date)<br/>creates monthly partition if missing"]
    G --> H["upsert batches of 1000<br/>ON CONFLICT (date, lon, lat)"]
```

Notes:

- Sentinel Hub returns a tar of TIFFs (`default` = values, `dataMask` =
  validity); decoded with Pillow + numpy, no temp files.
- Pixel coordinates are grid-cell centers computed from the bbox, so
  re-fetching the same bbox/resolution upserts onto the same rows —
  this is what makes change detection joins work.

## DB-side tile rendering

`tile_cache_service.render_tile_from_pixels` + `pixel_tile_renderer`:

1. `get_pixel_grid` RPC aggregates pixels into ≤64×64 cells **in SQL**
   (bounded output regardless of zoom or pixel density).
2. Grid is colorized with `COLOR_SCALES` — thresholds copied 1:1 from the
   Sentinel Hub evalscripts, so DB tiles are visually identical.
3. NaN cells → transparent; upscaled to 256×256 with nearest-neighbor.
4. Fewer than 4 populated cells → `None` (caller falls through to
   Sentinel Hub).

## Area analytics

`tile_cache_service` methods are thin wrappers over SQL RPCs — aggregation
never happens in Python:

| Method | RPC |
|---|---|
| `get_area_statistics` | `get_area_pixel_stats` (mean/median/min/max/std/count) |
| `get_area_timeseries` | `get_area_pixel_timeseries` |
| `get_area_histogram` | `get_area_pixel_histogram` |
| `get_area_change` | `get_area_pixel_change` |

See [../database/schema.md](../database/schema.md) for the RPC definitions.
