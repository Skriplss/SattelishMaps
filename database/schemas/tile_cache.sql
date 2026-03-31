-- ============================================
-- Tile Cache Schema
-- Stores pre-rendered satellite tiles with geolocation
-- ============================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================
-- Table: tile_cache
-- Stores rendered tiles with their geographic bounds
-- ============================================
CREATE TABLE tile_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Tile identification
    z INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    
    -- Tile metadata
    date DATE NOT NULL,
    index_type TEXT NOT NULL, -- NDVI, NDWI, NDBI, MOISTURE
    
    -- Geographic bounds
    bbox GEOGRAPHY(POLYGON, 4326) NOT NULL,
    
    -- Tile data
    tile_data BYTEA NOT NULL, -- PNG image data
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    
    -- Unique constraint
    UNIQUE(z, x, y, date, index_type)
);

-- Indexes
CREATE INDEX idx_tile_cache_zxy ON tile_cache(z, x, y);
CREATE INDEX idx_tile_cache_date ON tile_cache(date);
CREATE INDEX idx_tile_cache_index_type ON tile_cache(index_type);
CREATE INDEX idx_tile_cache_bbox ON tile_cache USING GIST(bbox);
CREATE INDEX idx_tile_cache_accessed_at ON tile_cache(accessed_at);

-- RLS
ALTER TABLE tile_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access" ON tile_cache FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON tile_cache FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access" ON tile_cache FOR UPDATE USING (true);

-- ============================================
-- Table: pixel_data
-- Stores individual pixel values with geolocation
-- ============================================
CREATE TABLE pixel_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Location
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    
    -- Temporal
    date DATE NOT NULL,
    
    -- Index values
    ndvi DECIMAL(6,4),
    ndwi DECIMAL(6,4),
    ndbi DECIMAL(6,4),
    moisture DECIMAL(6,4),
    
    -- Metadata
    cloud_mask BOOLEAN DEFAULT false,
    quality_score DECIMAL(3,2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Composite index for spatial-temporal queries
    UNIQUE(location, date)
);

-- Indexes
CREATE INDEX idx_pixel_data_location ON pixel_data USING GIST(location);
CREATE INDEX idx_pixel_data_date ON pixel_data(date);
CREATE INDEX idx_pixel_data_ndvi ON pixel_data(ndvi) WHERE ndvi IS NOT NULL;
CREATE INDEX idx_pixel_data_ndwi ON pixel_data(ndwi) WHERE ndwi IS NOT NULL;

-- RLS
ALTER TABLE pixel_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access" ON pixel_data FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON pixel_data FOR INSERT WITH CHECK (true);

-- ============================================
-- Function: Get pixel statistics for area
-- ============================================
CREATE OR REPLACE FUNCTION get_area_pixel_stats(
    p_min_lon DECIMAL,
    p_min_lat DECIMAL,
    p_max_lon DECIMAL,
    p_max_lat DECIMAL,
    p_date DATE,
    p_index_type TEXT
)
RETURNS TABLE (
    mean_value DECIMAL,
    min_value DECIMAL,
    max_value DECIMAL,
    std_value DECIMAL,
    pixel_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        AVG(CASE 
            WHEN p_index_type = 'NDVI' THEN ndvi
            WHEN p_index_type = 'NDWI' THEN ndwi
            WHEN p_index_type = 'NDBI' THEN ndbi
            WHEN p_index_type = 'MOISTURE' THEN moisture
        END)::DECIMAL AS mean_value,
        MIN(CASE 
            WHEN p_index_type = 'NDVI' THEN ndvi
            WHEN p_index_type = 'NDWI' THEN ndwi
            WHEN p_index_type = 'NDBI' THEN ndbi
            WHEN p_index_type = 'MOISTURE' THEN moisture
        END)::DECIMAL AS min_value,
        MAX(CASE 
            WHEN p_index_type = 'NDVI' THEN ndvi
            WHEN p_index_type = 'NDWI' THEN ndwi
            WHEN p_index_type = 'NDBI' THEN ndbi
            WHEN p_index_type = 'MOISTURE' THEN moisture
        END)::DECIMAL AS max_value,
        STDDEV(CASE 
            WHEN p_index_type = 'NDVI' THEN ndvi
            WHEN p_index_type = 'NDWI' THEN ndwi
            WHEN p_index_type = 'NDBI' THEN ndbi
            WHEN p_index_type = 'MOISTURE' THEN moisture
        END)::DECIMAL AS std_value,
        COUNT(*)::BIGINT AS pixel_count
    FROM pixel_data
    WHERE date = p_date
        AND ST_Intersects(
            location,
            ST_MakeEnvelope(p_min_lon, p_min_lat, p_max_lon, p_max_lat, 4326)::geography
        )
        AND (
            (p_index_type = 'NDVI' AND ndvi IS NOT NULL) OR
            (p_index_type = 'NDWI' AND ndwi IS NOT NULL) OR
            (p_index_type = 'NDBI' AND ndbi IS NOT NULL) OR
            (p_index_type = 'MOISTURE' AND moisture IS NOT NULL)
        );
END;
$$ LANGUAGE plpgsql;
