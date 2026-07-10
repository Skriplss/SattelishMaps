# 003. Database Redesign: Long-Format Stats & Partitioned Pixel Data

## Status
ACCEPTED (2026-07)

## Context
The original schema had drifted out of sync with the code:

- `region_statistics` was defined **wide** (`ndvi_mean`, `ndwi_mean`, … in one
  row) while most readers queried it **long** (`index_type` + `mean`/`min`/…);
  writers disagreed with each other too.
- Legacy Copernicus-era tables (`satellite_images`, `ndvi_data`, `ndwi_data`)
  had no remaining writers after the Copernicus flow was removed.
- `pixel_data` used a UUID PK plus `UNIQUE(location geography, date)` — a
  fragile upsert target and two redundant indexes on the highest-volume table.
- `tile_cache` stored BYTEA, which PostgREST cannot round-trip; the cache
  write path could never have worked.

## Decision
One schema file (`database/schemas/init.sql`) is the single source of truth:

1. **`region_statistics` in long format** — one row per
   region × date × index_type, `UNIQUE` on that triple; every reader and
   writer aligned to it.
2. **`pixel_data` partitioned by month** (`PARTITION BY RANGE (date)`), with
   a natural PK `(date, lon, lat)` and a **generated** `geom` column with a
   GIST index. Partitions are created lazily via the
   `ensure_pixel_data_partition(date)` RPC called by the backend before
   upserts.
3. **`tile_cache` stores base64 TEXT** with a natural composite PK; access
   stats are bumped atomically by the `get_cached_tile` RPC; eviction via
   `cleanup_tile_cache(days)`.
4. **All aggregation in SQL RPCs** (stats, timeseries, histogram, change
   detection, GeoJSON conversion, tile grids) — the backend never aggregates
   raw pixels in Python.
5. **RLS locked down**: enabled everywhere with no public policies; only the
   backend's `service_role` key can touch data. Function EXECUTE is revoked
   from PUBLIC.
6. Legacy tables and their API endpoints were **dropped**, not migrated —
   nothing wrote to them anymore.

## Consequences
- Change detection joins pixels on exact `(lon, lat)`, which requires
  fetching compared dates with the same bbox/resolution (documented).
- Creating a new environment is a single SQL file run — no migration chain
  (acceptable pre-production; introduce migrations once the schema is live
  with real data).
- Pixel volume scales by adding partitions, not by rebuilding indexes; a
  month's data can be dropped with `DROP TABLE pixel_data_YYYYMM`.
