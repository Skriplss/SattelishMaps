-- ============================================
-- MIGRATION: Sentinel-2 (Old) -> Sentinel Hub (New)
-- ============================================

-- 1. DROP OLD TABLES
-- Drop tables in order of dependency (child first)
DROP TABLE IF EXISTS ndvi_data CASCADE;
DROP TABLE IF EXISTS ndwi_data CASCADE;
DROP TABLE IF EXISTS satellite_images CASCADE;
DROP TABLE IF EXISTS user_requests CASCADE;
DROP TABLE IF EXISTS satellites CASCADE;

-- 2. CREATE NEW SCHEMA

-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================
-- Table: region_statistics
-- Stores daily aggregated statistics for a region
-- ============================================
CREATE TABLE region_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Spatial / Temporal
    region_name TEXT DEFAULT 'Trnava', -- Can be parameterized later
    date DATE NOT NULL,
    bbox GEOGRAPHY(POLYGON, 4326),
    
    -- NDVI Statistics
    ndvi_mean DECIMAL(6,4),
    ndvi_min DECIMAL(6,4),
    ndvi_max DECIMAL(6,4),
    ndvi_std DECIMAL(6,4),
    ndvi_sample_count INTEGER,
    
    -- NDWI Statistics
    ndwi_mean DECIMAL(6,4),
    ndwi_min DECIMAL(6,4),
    ndwi_max DECIMAL(6,4),
    ndwi_std DECIMAL(6,4),
    ndwi_sample_count INTEGER,
    
    -- Metadata
    processing_date TIMESTAMP DEFAULT NOW(),
    provider TEXT DEFAULT 'Sentinel Hub',
    
    -- Constraint: One entry per region per day
    UNIQUE(region_name, date)
);

-- Indexes
CREATE INDEX idx_region_statistics_date ON region_statistics(date);
CREATE INDEX idx_region_statistics_bbox ON region_statistics USING GIST(bbox);

-- RLS
ALTER TABLE region_statistics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read/write" ON region_statistics USING (true) WITH CHECK (true);
