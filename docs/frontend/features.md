# Frontend Features

## Theme Switching

The application supports light and dark themes:

- Click the theme toggle button in the sidebar (Sun/Moon icon)
- Theme preference is saved in localStorage
- Theme is automatically applied on page load
- Smooth transitions between themes

## Language Support

The application supports English and Slovak languages:

- Click the language button in the sidebar
- Available languages: English (EN) and Slovenčina (SK)
- Language preference is saved in localStorage
- All UI elements are translated

## Area Selection

Users can select custom areas on the map:

1. Hold the **Shift** key
2. Click and drag on the map to draw a rectangle
3. The selected area will be highlighted in blue
4. Release to complete the selection

The selected area can be used for:
- Regional statistics analysis
- Custom data export
- Focused satellite imagery requests

## Map Layers

Available satellite indices:
- **NDVI** (Normalized Difference Vegetation Index) - Vegetation health
- **NDWI** (Normalized Difference Water Index) - Water content
- **NDBI** (Normalized Difference Built-up Index) - Urban areas
- **Moisture** - Soil moisture levels

Each layer displays color-coded satellite data with a legend showing the value range.
