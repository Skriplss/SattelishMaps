-- ============================================
-- Supabase Database Schema for Sentinel-2
-- ============================================

-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================
-- Table: satellites
-- Stores information about satellite platforms
-- ============================================
CREATE TABLE satellites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL, -- e.g., 'Sentinel-2A', 'Sentinel-2B'
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default Sentinel-2 satellites
INSERT INTO satellites (name, platform, description) VALUES
    ('Sentinel-2A', 'Sentinel-2', 'Sentinel-2A satellite launched in 2015'),
    ('Sentinel-2B', 'Sentinel-2', 'Sentinel-2B satellite launched in 2017');

-- ============================================
-- Table: satellite_images
-- Stores metadata about satellite images
-- ============================================
CREATE TABLE satellite_images (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    satellite_id UUID REFERENCES satellites(id) ON DELETE SET NULL,
    
    -- Copernicus product information
    product_id TEXT UNIQUE NOT NULL,
    title TEXT,
    
    -- Temporal information
    acquisition_date TIMESTAMP NOT NULL,
    processing_date TIMESTAMP,
    
    -- Spatial information
    center_point GEOGRAPHY(POINT, 4326),
    bounds GEOGRAPHY(POLYGON, 4326),
    
    -- Image quality
    cloud_coverage DECIMAL(5,2) CHECK (cloud_coverage >= 0 AND cloud_coverage <= 100),
    
    -- URLs
    thumbnail_url TEXT,
    preview_url TEXT,
    download_url TEXT,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Table: user_requests
-- Stores user search/analysis requests
-- ============================================
CREATE TABLE user_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Request parameters
    request_type TEXT NOT NULL, -- 'search', 'analysis', 'download'
    
    -- Spatial parameters
    area_name TEXT,
    bounds GEOGRAPHY(POLYGON, 4326),
    
    -- Temporal parameters
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    
    -- Filter parameters
    max_cloud_coverage DECIMAL(5,2) DEFAULT 30,
    
    -- Request metadata
    parameters JSONB DEFAULT '{}',
    
    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    result_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- ============================================
-- Table: ndvi_data
-- Stores NDVI (vegetation) index calculations
-- ============================================
CREATE TABLE ndvi_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    image_id UUID REFERENCES satellite_images(id) ON DELETE CASCADE,
    request_id UUID REFERENCES user_requests(id) ON DELETE SET NULL,
    
    -- NDVI statistics
    ndvi_mean DECIMAL(6,4) CHECK (ndvi_mean >= -1 AND ndvi_mean <= 1),
    ndvi_min DECIMAL(6,4) CHECK (ndvi_min >= -1 AND ndvi_min <= 1),
    ndvi_max DECIMAL(6,4) CHECK (ndvi_max >= -1 AND ndvi_max <= 1),
    ndvi_std DECIMAL(6,4),
    ndvi_median DECIMAL(6,4),
    
    -- Vegetation classification
    vegetation_category TEXT, -- 'bare_soil', 'sparse', 'moderate', 'dense'
    vegetation_percentage DECIMAL(5,2),
    
    -- Spatial data
    area_coverage DECIMAL(10,2), -- in square meters
    location GEOGRAPHY(POINT, 4326),
    
    -- Quality
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    
    -- Additional data
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Table: ndwi_data
-- Stores NDWI (water) index calculations
-- ============================================
CREATE TABLE ndwi_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    image_id UUID REFERENCES satellite_images(id) ON DELETE CASCADE,
    request_id UUID REFERENCES user_requests(id) ON DELETE SET NULL,
    
    -- NDWI statistics
    ndwi_mean DECIMAL(6,4) CHECK (ndwi_mean >= -1 AND ndwi_mean <= 1),
    ndwi_min DECIMAL(6,4) CHECK (ndwi_min >= -1 AND ndwi_min <= 1),
    ndwi_max DECIMAL(6,4) CHECK (ndwi_max >= -1 AND ndwi_max <= 1),
    ndwi_std DECIMAL(6,4),
    ndwi_median DECIMAL(6,4),
    
    -- Water classification
    water_category TEXT, -- 'no_water', 'low', 'moderate', 'high'
    water_percentage DECIMAL(5,2),
    
    -- Spatial data
    area_coverage DECIMAL(10,2), -- in square meters
    location GEOGRAPHY(POINT, 4326),
    
    -- Quality
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    
    -- Additional data
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Indexes for performance
-- ============================================

-- Satellite images indexes
CREATE INDEX idx_satellite_images_acquisition_date ON satellite_images(acquisition_date);
CREATE INDEX idx_satellite_images_cloud_coverage ON satellite_images(cloud_coverage);
CREATE INDEX idx_satellite_images_product_id ON satellite_images(product_id);
CREATE INDEX idx_satellite_images_center_point ON satellite_images USING GIST(center_point);
CREATE INDEX idx_satellite_images_bounds ON satellite_images USING GIST(bounds);

-- User requests indexes
CREATE INDEX idx_user_requests_status ON user_requests(status);
CREATE INDEX idx_user_requests_created_at ON user_requests(created_at);
CREATE INDEX idx_user_requests_bounds ON user_requests USING GIST(bounds);

-- NDVI data indexes
CREATE INDEX idx_ndvi_data_image_id ON ndvi_data(image_id);
CREATE INDEX idx_ndvi_data_request_id ON ndvi_data(request_id);
CREATE INDEX idx_ndvi_data_ndvi_mean ON ndvi_data(ndvi_mean);
CREATE INDEX idx_ndvi_data_location ON ndvi_data USING GIST(location);

-- NDWI data indexes
CREATE INDEX idx_ndwi_data_image_id ON ndwi_data(image_id);
CREATE INDEX idx_ndwi_data_request_id ON ndwi_data(request_id);
CREATE INDEX idx_ndwi_data_ndwi_mean ON ndwi_data(ndwi_mean);
CREATE INDEX idx_ndwi_data_location ON ndwi_data USING GIST(location);

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE satellites ENABLE ROW LEVEL SECURITY;
ALTER TABLE satellite_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ndvi_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ndwi_data ENABLE ROW LEVEL SECURITY;

-- Public read access policies (for MVP)
CREATE POLICY "Public read access" ON satellites FOR SELECT USING (true);
CREATE POLICY "Public read access" ON satellite_images FOR SELECT USING (true);
CREATE POLICY "Public read access" ON user_requests FOR SELECT USING (true);
CREATE POLICY "Public read access" ON ndvi_data FOR SELECT USING (true);
CREATE POLICY "Public read access" ON ndwi_data FOR SELECT USING (true);

-- Public insert access policies (for MVP - restrict in production)
CREATE POLICY "Public insert access" ON satellite_images FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert access" ON user_requests FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert access" ON ndvi_data FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert access" ON ndwi_data FOR INSERT WITH CHECK (true);

-- ============================================
-- Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for satellite_images
CREATE TRIGGER update_satellite_images_updated_at
    BEFORE UPDATE ON satellite_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Views for easy querying
-- ============================================

-- View: Latest images with NDVI and NDWI data
CREATE OR REPLACE VIEW latest_satellite_data AS
SELECT 
    si.id,
    si.product_id,
    si.acquisition_date,
    si.cloud_coverage,
    si.center_point,
    s.name as satellite_name,
    nd.ndvi_mean,
    nd.vegetation_category,
    nw.ndwi_mean,
    nw.water_category
FROM satellite_images si
LEFT JOIN satellites s ON si.satellite_id = s.id
LEFT JOIN ndvi_data nd ON si.id = nd.image_id
LEFT JOIN ndwi_data nw ON si.id = nw.image_id
ORDER BY si.acquisition_date DESC;

-- ============================================
-- Sample data for testing (optional)
-- ============================================

-- Uncomment to insert sample data
/*
INSERT INTO satellite_images (satellite_id, product_id, title, acquisition_date, cloud_coverage, center_point)
VALUES (
    (SELECT id FROM satellites WHERE name = 'Sentinel-2A'),
    'S2A_MSIL2A_20231205T100321_N0509_R122_T33UXP_20231205T134512',
    'Sentinel-2A MSI Level-2A',
    '2023-12-05 10:03:21',
    15.5,
    ST_GeogFromText('POINT(14.4378 50.0755)')
);
*/
