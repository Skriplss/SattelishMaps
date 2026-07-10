# Frontend Features

## Coverage Area

The application serves **Slovakia only**:

- The map is locked to Slovakia's bounds (`MAP_MAX_BOUNDS` in `src/config.ts`) — you cannot pan or zoom away
- Area selections are automatically clamped to the coverage bbox; selections fully outside are ignored
- The backend rejects data requests outside its `COVERAGE_BBOX` and serves transparent tiles beyond it (protecting Sentinel Hub quota)

## Location Search

The search field in the top bar finds places within Slovakia:

- Powered by the MapTiler Geocoding API (`country=sk` + coverage bbox filter)
- Debounced as you type; results in the current UI language
- Clicking a result flies the map to that location
- The dashed-square button next to a result selects that place's
  administrative bounds as the analysis area — the precise way to analyze
  a city without accidentally capturing its neighbors

## Theme Switching

The application supports light and dark themes:

- Click the theme toggle button in the sidebar (Sun/Moon icon)
- The basemap style follows the theme (dataviz / dataviz-dark)
- Theme preference is saved in localStorage and applied on page load

## Language Support

The application supports English and Slovak languages:

- Click the language button in the sidebar
- Available languages: English (EN) and Slovenčina (SK)
- Language preference is saved in localStorage and shared across all components
- All UI elements are translated

## Area Selection

Two ways to select a custom area on the map (a layer must be active):

1. Hold **Shift**, then click and drag to draw a rectangle, **or**
2. Click **Select Area** in the sidebar to arm draw mode, then just drag, **or**
3. Search for a place and use its "Analyze this area" button (see above)

While drawing, the hint bar shows the live selection size in km. The
selection is highlighted in blue and clamped to Slovakia. Use
**Clear Selection** in the sidebar to remove it.

If the selected area has no pixel data yet, the stats panel offers a
**Load data for this area** button that pulls it from Sentinel Hub
(all four indices in parallel) and refreshes the analysis.

A selected area unlocks in the stats panel:
- Pixel statistics (mean / median / min / max / σ / pixel count)
- Timeseries chart over the chosen date range
- Value distribution histogram
- Change detection between the "From" and "To" dates
- Chart PNG and HTML report export

## Region Statistics

Without an area selection, the stats panel shows aggregated statistics for a
region chosen from the dropdown (the list comes from `/api/statistics/regions`).

## Map Layers

Available satellite indices:
- **NDVI** (Normalized Difference Vegetation Index) - Vegetation health
- **NDWI** (Normalized Difference Water Index) - Water content
- **NDBI** (Normalized Difference Built-up Index) - Urban areas
- **Moisture** (Normalized Difference Moisture Index) - Soil moisture levels

Each layer displays color-coded satellite data. The legend gradient matches
the actual tile palette used by the backend renderer.
