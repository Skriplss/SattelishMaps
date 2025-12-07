-- ============================================
-- Migration: Add ST_AsGeoJSON function wrapper
-- ============================================

-- Create a function to convert GEOGRAPHY to GeoJSON
-- This is needed because Supabase RPC requires explicit function definitions

CREATE OR REPLACE FUNCTION st_asgeojson(geom geography)
RETURNS json AS $$
BEGIN
    RETURN ST_AsGeoJSON(geom::geometry)::json;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION st_asgeojson(geography) TO anon, authenticated, service_role;

COMMENT ON FUNCTION st_asgeojson(geography) IS 'Convert GEOGRAPHY to GeoJSON format';
