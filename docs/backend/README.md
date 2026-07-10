# Backend Documentation

FastAPI backend: serves the map tiles and analytics API, runs background
data-fetch jobs, and owns all database access.

## Contents

| Doc | What's inside |
|---|---|
| [setup.md](setup.md) | Environment variables, local & Docker runs |
| [api.md](api.md) | Full REST endpoint reference |
| [services.md](services.md) | Service layer + tile/pixel pipeline diagrams |
| [scheduler.md](scheduler.md) | Background jobs & monitoring |
| [pixel-data.md](pixel-data.md) | Pixel data deep-dive: workflow, endpoints, troubleshooting (RU) |

## Directory Structure

```
backend/
├── api/                 # Route handlers (thin: validate → service → envelope)
│   ├── wms.py           #   tiles & rendered images
│   ├── tiles.py         #   pixel data, area analytics, tile cache
│   ├── statistics.py    #   region list & timeseries
│   ├── region_statistics.py  # GeoJSON region stats, available dates
│   └── sentinelhub.py   #   catalog search
├── services/            # Business logic (singletons)
│   ├── supabase_service.py          # all DB access
│   ├── sentinel_hub_wms_service.py  # Process API (PNG + raw pixels)
│   ├── sentinelhub_service.py       # Statistical + Catalog API (SDK)
│   ├── tile_cache_service.py        # cache, pixel pipeline, analytics
│   └── pixel_tile_renderer.py       # value grid → colored PNG
├── utils/                # logging, error handlers, response envelope, validation
├── config/settings.py    # pydantic-settings (env-driven)
├── scripts/              # fetch_now, fetch_historical_stats, fetch_pixel_data
├── scheduler.py          # APScheduler jobs
└── app.py                # FastAPI app, middleware, routers, /health
```

Database schema lives in [`database/schemas/init.sql`](../../database/schemas/init.sql)
— see [../database/schema.md](../database/schema.md) for diagrams and
[../../database/README.md](../../database/README.md) for setup.

## Request handling conventions

- Endpoints are thin: shared validation (`utils/validation.py`) → service
  call → `success_response` envelope.
- Domain errors (`SupabaseError`, `NotFoundError`) are raised by routes and
  converted to JSON by handlers registered in `utils/error_handlers.py`.
- Coverage enforcement: anything that would spend Sentinel Hub quota
  validates its bbox against `COVERAGE_BBOX` first.

## Technologies

- **FastAPI** — web framework (async), OpenAPI at `/docs` in debug.
- **Supabase (PostgREST + RPC)** — PostgreSQL/PostGIS access; heavy
  aggregation is done in SQL functions, not Python.
- **sentinelhub SDK / requests.Session** — Sentinel Hub integrations.
- **NumPy + Pillow** — decoding TIFF rasters, rendering PNG tiles.
- **APScheduler** — in-process background jobs.
