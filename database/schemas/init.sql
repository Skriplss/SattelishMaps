-- ============================================================
-- SattelishMaps — Database Schema (single source of truth)
--
-- Run this ONCE on a fresh Supabase project:
--   Dashboard → SQL Editor → paste → Run
--
-- Design notes:
--   * region_statistics uses the LONG format (one row per
--     region+date+index) — matches every reader in the backend.
--   * pixel_data is RANGE-partitioned by month for scale;
--     partitions are created on demand via
--     ensure_pixel_data_partition() (called by the backend).
--   * tile_cache stores PNG tiles as base64 TEXT (PostgREST
--     cannot round-trip BYTEA reliably).
--   * RLS is enabled with NO public policies: the backend uses
--     the service_role key which bypasses RLS. If you later
--     read directly from the frontend, add SELECT policies.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. region_statistics — aggregated stats per region/date/index
-- ============================================================
CREATE TABLE region_statistics (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name     TEXT NOT NULL,
    date            DATE NOT NULL,
    index_type      TEXT NOT NULL CHECK (index_type IN ('NDVI', 'NDWI', 'NDBI', 'MOISTURE')),
    bbox            GEOMETRY(POLYGON, 4326),

    mean            REAL,
    min             REAL,
    max             REAL,
    std             REAL,
    sample_count    INTEGER,

    provider        TEXT NOT NULL DEFAULT 'Sentinel Hub Statistical API',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (region_name, date, index_type)
);

CREATE INDEX idx_region_statistics_lookup ON region_statistics (index_type, date);
CREATE INDEX idx_region_statistics_region ON region_statistics (region_name, index_type, date);
CREATE INDEX idx_region_statistics_bbox   ON region_statistics USING GIST (bbox);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_region_statistics_updated_at
    BEFORE UPDATE ON region_statistics
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 2. pixel_data — raw per-pixel index values, partitioned by month
-- ============================================================
CREATE TABLE pixel_data (
    date        DATE NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    lat         DOUBLE PRECISION NOT NULL,

    ndvi        REAL,
    ndwi        REAL,
    ndbi        REAL,
    moisture    REAL,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    geom        GEOMETRY(POINT, 4326) GENERATED ALWAYS AS
                    (ST_SetSRID(ST_MakePoint(lon, lat), 4326)) STORED,

    PRIMARY KEY (date, lon, lat)
) PARTITION BY RANGE (date);

-- Indexes declared on the parent propagate to every partition
CREATE INDEX idx_pixel_data_geom ON pixel_data USING GIST (geom);

-- Create the partition for a given month if it does not exist yet.
-- The backend calls this (as an RPC) before every pixel upsert.
CREATE OR REPLACE FUNCTION ensure_pixel_data_partition(p_date DATE)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    part_start DATE := date_trunc('month', p_date)::date;
    part_end   DATE := (date_trunc('month', p_date) + interval '1 month')::date;
    part_name  TEXT := 'pixel_data_' || to_char(part_start, 'YYYYMM');
BEGIN
    IF to_regclass(part_name) IS NULL THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF pixel_data FOR VALUES FROM (%L) TO (%L)',
            part_name, part_start, part_end
        );
    END IF;
END;
$$;

-- ============================================================
-- 3. tile_cache — rendered PNG tiles (base64) with access stats
-- ============================================================
CREATE TABLE tile_cache (
    z            SMALLINT NOT NULL CHECK (z BETWEEN 0 AND 22),
    x            INTEGER NOT NULL,
    y            INTEGER NOT NULL,
    date         DATE NOT NULL,
    index_type   TEXT NOT NULL CHECK (index_type IN ('NDVI', 'NDWI', 'NDBI', 'MOISTURE')),

    tile_data    TEXT NOT NULL,  -- base64-encoded PNG

    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    accessed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    access_count INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (z, x, y, date, index_type)
);

CREATE INDEX idx_tile_cache_accessed_at ON tile_cache (accessed_at);

-- Atomically fetch a tile and bump its access stats.
-- Returns NULL on cache miss.
CREATE OR REPLACE FUNCTION get_cached_tile(
    p_z SMALLINT, p_x INTEGER, p_y INTEGER, p_date DATE, p_index_type TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    result TEXT;
BEGIN
    UPDATE tile_cache
    SET accessed_at = now(), access_count = access_count + 1
    WHERE z = p_z AND x = p_x AND y = p_y
      AND date = p_date AND index_type = p_index_type
    RETURNING tile_data INTO result;
    RETURN result;
END;
$$;

-- Evict tiles not accessed for p_keep_days. Returns rows deleted.
-- Call periodically (backend job or pg_cron).
CREATE OR REPLACE FUNCTION cleanup_tile_cache(p_keep_days INTEGER DEFAULT 30)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    deleted BIGINT;
BEGIN
    DELETE FROM tile_cache
    WHERE accessed_at < now() - make_interval(days => p_keep_days);
    GET DIAGNOSTICS deleted = ROW_COUNT;
    RETURN deleted;
END;
$$;

-- ============================================================
-- 4. Analysis RPCs over pixel_data
-- ============================================================

-- Aggregated statistics for a bbox on a given date
CREATE OR REPLACE FUNCTION get_area_pixel_stats(
    p_min_lon DOUBLE PRECISION, p_min_lat DOUBLE PRECISION,
    p_max_lon DOUBLE PRECISION, p_max_lat DOUBLE PRECISION,
    p_date DATE, p_index_type TEXT
)
RETURNS TABLE (
    mean_value   DOUBLE PRECISION,
    min_value    DOUBLE PRECISION,
    max_value    DOUBLE PRECISION,
    std_value    DOUBLE PRECISION,
    median_value DOUBLE PRECISION,
    pixel_count  BIGINT
)
LANGUAGE sql STABLE
AS $$
    WITH vals AS (
        SELECT (CASE upper(p_index_type)
                    WHEN 'NDVI' THEN ndvi
                    WHEN 'NDWI' THEN ndwi
                    WHEN 'NDBI' THEN ndbi
                    WHEN 'MOISTURE' THEN moisture
                END)::double precision AS v
        FROM pixel_data
        WHERE date = p_date
          AND geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
    )
    SELECT AVG(v), MIN(v), MAX(v), STDDEV(v),
           percentile_cont(0.5) WITHIN GROUP (ORDER BY v),
           COUNT(v)
    FROM vals
    WHERE v IS NOT NULL;
$$;

-- Per-date aggregates for a bbox over a date range (charting)
CREATE OR REPLACE FUNCTION get_area_pixel_timeseries(
    p_min_lon DOUBLE PRECISION, p_min_lat DOUBLE PRECISION,
    p_max_lon DOUBLE PRECISION, p_max_lat DOUBLE PRECISION,
    p_index_type TEXT,
    p_date_from DATE, p_date_to DATE
)
RETURNS TABLE (
    date        DATE,
    mean_value  DOUBLE PRECISION,
    min_value   DOUBLE PRECISION,
    max_value   DOUBLE PRECISION,
    pixel_count BIGINT
)
LANGUAGE sql STABLE
AS $$
    SELECT pd.date,
           AVG(v.val), MIN(v.val), MAX(v.val), COUNT(v.val)
    FROM pixel_data pd,
         LATERAL (SELECT (CASE upper(p_index_type)
                              WHEN 'NDVI' THEN pd.ndvi
                              WHEN 'NDWI' THEN pd.ndwi
                              WHEN 'NDBI' THEN pd.ndbi
                              WHEN 'MOISTURE' THEN pd.moisture
                          END)::double precision AS val) v
    WHERE pd.date BETWEEN p_date_from AND p_date_to
      AND pd.geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
      AND v.val IS NOT NULL
    GROUP BY pd.date
    ORDER BY pd.date;
$$;

-- Value distribution (histogram) for a bbox on a given date.
-- Index values live in [-1, 1].
CREATE OR REPLACE FUNCTION get_area_pixel_histogram(
    p_min_lon DOUBLE PRECISION, p_min_lat DOUBLE PRECISION,
    p_max_lon DOUBLE PRECISION, p_max_lat DOUBLE PRECISION,
    p_date DATE, p_index_type TEXT,
    p_bins INTEGER DEFAULT 20
)
RETURNS TABLE (
    bucket    INTEGER,
    range_min DOUBLE PRECISION,
    range_max DOUBLE PRECISION,
    count     BIGINT
)
LANGUAGE sql STABLE
AS $$
    WITH vals AS (
        SELECT (CASE upper(p_index_type)
                    WHEN 'NDVI' THEN ndvi
                    WHEN 'NDWI' THEN ndwi
                    WHEN 'NDBI' THEN ndbi
                    WHEN 'MOISTURE' THEN moisture
                END)::double precision AS v
        FROM pixel_data
        WHERE date = p_date
          AND geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
    )
    SELECT width_bucket(v, -1.0, 1.0, p_bins) AS bucket,
           -1.0 + (width_bucket(v, -1.0, 1.0, p_bins) - 1) * (2.0 / p_bins) AS range_min,
           -1.0 + width_bucket(v, -1.0, 1.0, p_bins) * (2.0 / p_bins) AS range_max,
           COUNT(*)
    FROM vals
    WHERE v IS NOT NULL
    GROUP BY 1
    ORDER BY 1;
$$;

-- Change detection: compare two dates over a bbox.
-- NOTE: pixels are joined on exact (lon, lat) — fetch both dates
-- with the same bbox and resolution for a full join.
CREATE OR REPLACE FUNCTION get_area_pixel_change(
    p_min_lon DOUBLE PRECISION, p_min_lat DOUBLE PRECISION,
    p_max_lon DOUBLE PRECISION, p_max_lat DOUBLE PRECISION,
    p_date_a DATE, p_date_b DATE, p_index_type TEXT,
    p_threshold DOUBLE PRECISION DEFAULT 0.05
)
RETURNS TABLE (
    mean_a         DOUBLE PRECISION,
    mean_b         DOUBLE PRECISION,
    mean_diff      DOUBLE PRECISION,
    improved_count BIGINT,
    declined_count BIGINT,
    stable_count   BIGINT,
    pixel_count    BIGINT
)
LANGUAGE sql STABLE
AS $$
    WITH a AS (
        SELECT lon, lat,
               (CASE upper(p_index_type)
                    WHEN 'NDVI' THEN ndvi WHEN 'NDWI' THEN ndwi
                    WHEN 'NDBI' THEN ndbi WHEN 'MOISTURE' THEN moisture
                END)::double precision AS v
        FROM pixel_data
        WHERE date = p_date_a
          AND geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
    ),
    b AS (
        SELECT lon, lat,
               (CASE upper(p_index_type)
                    WHEN 'NDVI' THEN ndvi WHEN 'NDWI' THEN ndwi
                    WHEN 'NDBI' THEN ndbi WHEN 'MOISTURE' THEN moisture
                END)::double precision AS v
        FROM pixel_data
        WHERE date = p_date_b
          AND geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
    ),
    joined AS (
        SELECT a.v AS va, b.v AS vb, b.v - a.v AS diff
        FROM a JOIN b USING (lon, lat)
        WHERE a.v IS NOT NULL AND b.v IS NOT NULL
    )
    SELECT AVG(va), AVG(vb), AVG(diff),
           COUNT(*) FILTER (WHERE diff > p_threshold),
           COUNT(*) FILTER (WHERE diff < -p_threshold),
           COUNT(*) FILTER (WHERE diff BETWEEN -p_threshold AND p_threshold),
           COUNT(*)
    FROM joined;
$$;

-- Downsampled value grid for a bbox — powers DB-side tile rendering.
-- Returns at most p_grid × p_grid cells regardless of pixel density.
CREATE OR REPLACE FUNCTION get_pixel_grid(
    p_min_lon DOUBLE PRECISION, p_min_lat DOUBLE PRECISION,
    p_max_lon DOUBLE PRECISION, p_max_lat DOUBLE PRECISION,
    p_date DATE, p_index_type TEXT,
    p_grid INTEGER DEFAULT 64
)
RETURNS TABLE (gx INTEGER, gy INTEGER, value DOUBLE PRECISION)
LANGUAGE sql STABLE
AS $$
    SELECT width_bucket(pd.lon, p_min_lon, p_max_lon, p_grid) - 1 AS gx,
           width_bucket(pd.lat, p_min_lat, p_max_lat, p_grid) - 1 AS gy,
           AVG(v.val)::double precision AS value
    FROM pixel_data pd,
         LATERAL (SELECT (CASE upper(p_index_type)
                              WHEN 'NDVI' THEN pd.ndvi
                              WHEN 'NDWI' THEN pd.ndwi
                              WHEN 'NDBI' THEN pd.ndbi
                              WHEN 'MOISTURE' THEN pd.moisture
                          END)::double precision AS val) v
    WHERE pd.date = p_date
      AND pd.geom && ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)
      AND pd.lon >= p_min_lon AND pd.lon < p_max_lon
      AND pd.lat >= p_min_lat AND pd.lat < p_max_lat
      AND v.val IS NOT NULL
    GROUP BY 1, 2;
$$;

-- ============================================================
-- 5. Region statistics as GeoJSON (single call, no N+1)
-- ============================================================
CREATE OR REPLACE FUNCTION get_region_stats_geojson(
    p_date DATE,
    p_index_type TEXT,
    p_region_name TEXT DEFAULT NULL
)
RETURNS TABLE (
    id           BIGINT,
    region_name  TEXT,
    date         DATE,
    index_type   TEXT,
    mean         REAL,
    min          REAL,
    max          REAL,
    std          REAL,
    sample_count INTEGER,
    geometry     JSON
)
LANGUAGE sql STABLE
AS $$
    SELECT rs.id, rs.region_name, rs.date, rs.index_type,
           rs.mean, rs.min, rs.max, rs.std, rs.sample_count,
           ST_AsGeoJSON(rs.bbox)::json
    FROM region_statistics rs
    WHERE rs.date = p_date
      AND rs.index_type = upper(p_index_type)
      AND (p_region_name IS NULL OR rs.region_name = p_region_name);
$$;

-- ============================================================
-- 6. Row Level Security
-- ============================================================
-- No public policies: all access goes through the backend with
-- the service_role key (bypasses RLS). Add SELECT policies here
-- only if the frontend ever reads Supabase directly.
ALTER TABLE region_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE pixel_data        ENABLE ROW LEVEL SECURITY;
ALTER TABLE tile_cache        ENABLE ROW LEVEL SECURITY;

-- Functions: PUBLIC execute is Postgres default; restrict to the
-- roles that actually need them.
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ensure_pixel_data_partition(DATE) TO service_role;
GRANT EXECUTE ON FUNCTION get_cached_tile(SMALLINT, INTEGER, INTEGER, DATE, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_tile_cache(INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION get_area_pixel_stats(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DATE, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION get_area_pixel_timeseries(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, TEXT, DATE, DATE) TO service_role;
GRANT EXECUTE ON FUNCTION get_area_pixel_histogram(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DATE, TEXT, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION get_region_stats_geojson(DATE, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION get_area_pixel_change(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DATE, DATE, TEXT, DOUBLE PRECISION) TO service_role;
GRANT EXECUTE ON FUNCTION get_pixel_grid(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DATE, TEXT, INTEGER) TO service_role;
