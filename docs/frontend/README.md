# Frontend Documentation

The frontend is a lightweight, single-page application built with **Vanilla JavaScript** and **MapLibre GL JS**. It avoids heavy frameworks to ensure maximum performance and simplicity.

## 📂 Directory Structure

```
frontend/
├── js/
│   ├── main.js        # Entry point, initialization
│   ├── map.js         # Map interaction logic (SatelliteMap class)
│   ├── layers.js      # Layer management (SatelliteLayers class)
│   ├── api.js         # Backend API communication
│   ├── ui.js          # UI controls interaction
│   └── stats.js       # Statistics panel logic
├── css/               # Styles (variables, components)
├── components/        # HTML partials (if any)
└── index.html         # Main application entry
```

## 🏗️ Architecture

The application follows a simple class-based modular structure (simulated without ES6 modules for broad compatibility if needed, or just simplicity).

- **`SatelliteMap`**: Wrapper around `maplibregl.Map`. Handles initialization, camera controls, and base style.
- **`SatelliteLayers`**: Manages the addition/removal of raster (satellite) and vector (stats) layers.
- **`SatelliteAPI`**: Centralized place for all `fetch` calls to the backend.

## 🎨 Design System
- **CSS Variables**: Used for theming (Light/Dark mode).
- **Responsive**: Flexbox/Grid layouts ensure usability on mobile and desktop.
