# System Architecture

SattelishMaps is a three-tier system: a React SPA, a FastAPI backend, and a
Supabase (PostgreSQL + PostGIS) database, with Sentinel Hub as the satellite
data provider and MapTiler for basemaps and geocoding.

## High-level view

```mermaid
flowchart LR
    subgraph Client["Browser"]
        UI["React SPA<br/>MapLibre GL + Chart.js"]
    end

    subgraph Backend["FastAPI Backend"]
        API["REST API<br/>/api/*"]
        SCHED["APScheduler<br/>background jobs"]
        SVC["Services<br/>tile cache · pixel pipeline · renderer"]
    end

    subgraph Data["Supabase"]
        DB[("PostgreSQL + PostGIS<br/>region_statistics · pixel_data · tile_cache")]
    end

    subgraph External["External services"]
        SH["Sentinel Hub<br/>Process / Statistical / Catalog API"]
        MT["MapTiler<br/>basemap tiles · geocoding"]
    end

    UI -->|"REST (JSON, PNG tiles)"| API
    UI -->|"basemap + geocoding<br/>(direct, VITE_MAPTILER_KEY)"| MT
    API --> SVC
    SVC -->|"service_role key<br/>(PostgREST + RPC)"| DB
    SVC -->|"OAuth2"| SH
    SCHED -->|"NDVI/NDWI stats"| SH
    SCHED --> DB
```

Key boundaries:

- The **frontend never talks to Supabase directly** — all data access goes
  through the backend, which uses the `service_role` key (RLS is enabled with
  no public policies).
- The frontend talks to **MapTiler directly** (basemap styles + geocoding),
  authenticated with `VITE_MAPTILER_KEY`.
- All Sentinel Hub traffic goes through the backend; requests outside the
  configured **coverage area (Slovakia, `COVERAGE_BBOX`)** are rejected or
  served as transparent tiles so quota is never spent outside the product
  scope.

## Two data models: rendered vs raw

The same Sentinel-2 scenes power two distinct paths:

```mermaid
flowchart TB
    SH["Sentinel Hub Process API"]

    subgraph Rendered["Rendered path — 'show'"]
        PNG["PNG tiles<br/>(color-mapped by evalscript)"]
        TC[("tile_cache")]
    end

    subgraph Raw["Raw path — 'analyze'"]
        TIFF["FLOAT32 TIFF<br/>(raw index values)"]
        PD[("pixel_data<br/>partitioned by month")]
        AN["Analytics RPCs<br/>stats · timeseries · histogram · change"]
        RT["DB-side tile renderer<br/>(same palette)"]
    end

    SH -->|"image/png"| PNG --> TC
    SH -->|"application/tar (tiff)"| TIFF --> PD
    PD --> AN
    PD --> RT
```

- **Rendered path**: quick visualization; tiles are cached in `tile_cache`
  and reused (see [backend/services.md](../backend/services.md)).
- **Raw path**: per-pixel FLOAT32 values stored with coordinates in
  `pixel_data`; powers area statistics, histograms, change detection, and
  can render tiles itself without Sentinel Hub (`PREFER_PIXEL_TILES`).

## Request lifecycles

### Area analysis (user selects an area on the map)

```mermaid
sequenceDiagram
    actor U as User
    participant FE as StatsPanel (React)
    participant BE as FastAPI
    participant DB as Supabase (RPC)

    U->>FE: select area (drag / city search)
    par four parallel requests
        FE->>BE: GET /tiles/area/stats
        FE->>BE: GET /tiles/area/timeseries
        FE->>BE: GET /tiles/area/histogram
        FE->>BE: GET /tiles/area/change
    end
    BE->>DB: get_area_pixel_* RPCs
    DB-->>BE: aggregates (SQL-side)
    BE-->>FE: stats · series · buckets · diff
    FE-->>U: stats grid, charts, change card

    opt no pixel data yet
        U->>FE: "Load data for this area"
        FE->>BE: POST /tiles/fetch-pixels
        BE->>BE: 4 indices in parallel → Sentinel Hub
        BE->>DB: upsert pixels (batched, partitioned)
        FE->>FE: reload analysis
    end
```

All aggregation happens **in SQL** (RPC functions) — the backend never pulls
raw pixel rows to compute statistics.

## Coverage constraint

The product serves Slovakia only. The constraint is enforced at every layer:

| Layer | Mechanism |
|---|---|
| Map UI | `maxBounds` + `minZoom` lock the viewport to Slovakia |
| Area selection | client-side clamp to `COVERAGE` bbox (`src/config.ts`) |
| Geocoding | `country=sk` + bbox filter |
| Backend tiles | out-of-coverage tiles → transparent PNG, no Sentinel Hub call |
| Backend data APIs | out-of-coverage bbox → HTTP 400 |

Coverage is configuration, not code: change `COVERAGE_BBOX` (backend) and
`COVERAGE` / `MAP_MAX_BOUNDS` (frontend `src/config.ts`) to serve another
region.

## Technology stack

| Tier | Tech | Notes |
|---|---|---|
| Frontend | React 18, TypeScript, Vite | code-split: maplibre / charts / app chunks |
| Mapping | MapLibre GL JS | raster tiles from backend, theme-aware basemap |
| Charts | Chart.js + react-chartjs-2 | line, bar (histogram) |
| Backend | FastAPI, Python 3.11 | async, OpenAPI at `/docs` (DEBUG only) |
| Scheduler | APScheduler | interval jobs in-process |
| Database | Supabase (PostgreSQL 15 + PostGIS) | PostgREST + SQL RPCs, RLS locked |
| Satellite data | Sentinel Hub (Sentinel-2 L2A) | Process / Statistical / Catalog APIs |
| Infra | Docker Compose | dev (hot-reload) and prod variants |
