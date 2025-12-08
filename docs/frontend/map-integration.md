# Map Integration & Layers

Visualizing satellite data is the core feature of SattelishMaps. We use **MapLibre GL JS** for rendering.

## Map Initialization
The map is initialized in `SatelliteMap.init()` with a custom style (MapTiler Dataviz).
- **Projection**: Mercator.
- **Constraints**: Locked to plain view (no pitch), restricted zoom levels.
- **Masking**: A "World Gray" layer is added to dim everything outside of Slovakia, highlighting the region of interest.

## Layer Management
Handled by `SatelliteLayers` class.

### 1. Raster Layers (Satellite Imagery)
Used for raw Sentinel-2 RGB images and pre-rendered index tiles.
- **Source**: WMS-like endpoint from our backend (`/api/wms/tile/{z}/{x}/{y}.png`).
- **Implementation**: Added as a `raster` source and layer.
- **Ordering**: Placed *below* labels but *above* the background.

## 2. Vector Layers (Statistics)
Used for visualizing aggregated regional data.
- **Source**: GeoJSON from `/api/statistics/region`.
- **Styling**: `fill-color` is data-driven using MapLibre expressions.
    - **NDVI**: Brown (0.0) to Green (0.8).
    - **NDWI**: Brown (-0.5) to Blue (0.5).
    - **Moisture**: Red (Dry) to Cyan (Wet).

## 3. Legends
Dynamic HTML legends are generated based on the active layer type to help users interpret the colors.
