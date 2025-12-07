/*
   LAYERS CLASS - Manages satellite and raster layers
   Handles adding, removing, and updating map layers
*/

class SatelliteLayers {
    constructor(mapInstance) {
        this.map = mapInstance;
        this.activeLayers = new Set();
    }

    /**
     * Adds a raster layer to the map (e.g., satellite imagery)
     * @param {string} id - Unique layer ID
     * @param {string} url - Tile URL template (z/x/y)
     * @param {object} options - Optional settings (opacity, etc.)
     */
    addRasterLayer(id, url, options = {}) {
        if (!this.map || !this.map.getSource) {
            console.error('❌ Map instance not ready');
            return;
        }

        // Remove if exists to avoid collision
        this.removeLayer(id);

        console.log(`🌍 Adding raster layer: ${id}`);

        try {
            // 1. Add Source
            this.map.addSource(id, {
                type: 'raster',
                tiles: [url],
                tileSize: 256,
                attribution: 'Sentinel-2 Data'
            });

            // 2. Add Layer
            // We want the satellite image to be UNDER the gray world mask
            // so the world stays gray, and only Slovakia (the hole) shows the satellite clearly
            let beforeLayerId = undefined;

            if (this.map.getLayer('world-gray-layer')) {
                beforeLayerId = 'world-gray-layer';
            } else if (this.map.getLayer('slovakia-border')) {
                beforeLayerId = 'slovakia-border';
            } else {
                // Fallback: finding labels
                const layers = this.map.getStyle().layers;
                const labelLayer = layers.find(l => l.type === 'symbol' || l.id.includes('label'));
                if (labelLayer) {
                    beforeLayerId = labelLayer.id;
                }
            }

            this.map.addLayer({
                id: id,
                type: 'raster',
                source: id,
                paint: {
                    'raster-opacity': options.opacity || 1.0,
                    'raster-fade-duration': 300
                }
            }, beforeLayerId);

            this.activeLayers.add(id);
            console.log(`✅ Layer ${id} added successfully`);

        } catch (error) {
            console.error(`❌ Error adding layer ${id}:`, error);
        }
    }

    /**
     * Removes a layer and its source
     * @param {string} id - Layer ID to remove
     */
    removeLayer(id) {
        if (!this.map) return;

        if (this.map.getLayer(id)) {
            this.map.removeLayer(id);
            this.activeLayers.delete(id);
            console.log(`🗑️ Layer ${id} removed`);
        }

        if (this.map.getSource(id)) {
            this.map.removeSource(id);
        }
    }

    /**
     * Updates opacity of an existing layer
     * @param {string} id - Layer ID
     * @param {number} opacity - 0.0 to 1.0
     */
    setLayerOpacity(id, opacity) {
        if (this.map && this.map.getLayer(id)) {
            this.map.setPaintProperty(id, 'raster-opacity', opacity);
        }
    }

    /**
     * Remove all managed layers
     */
    clearAll() {
        this.activeLayers.forEach(id => this.removeLayer(id));
    }

    /**
     * Show a specific layer type (ndvi, ndwi, ndbi, moisture) using WMS tiles
     * @param {string} layerType
     */
    async showLayer(layerType) {
        console.log(`👁️ Showing layer: ${layerType}`);

        try {
            // 1. Get current date from calendar
            const mapDateInput = document.getElementById('map-date');

            if (!mapDateInput || !mapDateInput.value) {
                console.error('❌ No date selected');
                alert('Пожалуйста, выберите дату');
                return;
            }

            const selectedDate = mapDateInput.value;
            console.log(`📅 Selected date: ${selectedDate}`);

            // 2. Clear old layers
            this.clearAll();

            // 3. Show loader
            const loader = document.getElementById('loader');
            if (loader) loader.classList.remove('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = 'wait';

            // 4. Build WMS tile URL
            const API_BASE_URL = window.SatelliteAPI?.API_BASE_URL || 'http://localhost:8000';
            const tileUrl = `${API_BASE_URL}/api/wms/tile/{z}/{x}/{y}.png?date=${selectedDate}&index_type=${layerType.toUpperCase()}`;

            console.log(`🗺️ Loading WMS tiles: ${tileUrl}`);

            // 5. Add WMS raster layer
            this.addRasterLayer(layerType, tileUrl, { opacity: 0.8 });

            // 6. Show legend
            this.showLegend(layerType);

            // 7. Hide loader
            if (loader) loader.classList.add('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = '';

            console.log(`✅ WMS layer ${layerType} loaded successfully`);

        } catch (error) {
            console.error('❌ Failed to show layer:', error);

            // Hide loader
            const loader = document.getElementById('loader');
            if (loader) loader.classList.add('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = '';

            alert(`Ошибка загрузки данных: ${error.message}`);
        }
    }

    /**
     * Add vector layer from region statistics GeoJSON
     * @param {string} id - Layer ID
     * @param {object} geojson - GeoJSON FeatureCollection
     */
    addVectorLayerFromRegionStats(id, geojson) {
        if (!this.map) return;
        this.removeLayer(id);

        try {
            this.map.addSource(id, {
                type: 'geojson',
                data: geojson
            });

            // Determine color scale based on index type
            const indexType = geojson.features[0]?.properties?.index_type?.toLowerCase() || id;

            let fillColor = [
                'interpolate',
                ['linear'],
                ['get', 'mean'],  // Use 'mean' property from region statistics
                -1, '#000000'
            ];

            // Color scales for different indices
            if (indexType === 'ndvi') {
                fillColor.push(
                    -0.1, '#8B4513',  // Bare soil/rock
                    0, '#D2B48C',      // Very sparse vegetation
                    0.2, '#FEE090',    // Sparse vegetation
                    0.4, '#91CF60',    // Moderate vegetation
                    0.6, '#41A636',    // Dense vegetation
                    0.8, '#006400'     // Very dense vegetation
                );
            } else if (indexType === 'ndwi') {
                fillColor.push(
                    -0.5, '#8B4513',   // Dry soil
                    -0.2, '#D2B48C',   // Moist soil
                    0, '#87CEEB',      // Wet soil
                    0.2, '#4169E1',    // Shallow water
                    0.5, '#0000CD',    // Deep water
                    1.0, '#000080'     // Very deep water
                );
            } else if (indexType === 'ndbi') {
                fillColor.push(
                    -0.5, '#0000CD',   // Water
                    -0.2, '#228B22',   // Vegetation
                    0, '#D2B48C',      // Bare soil
                    0.2, '#A0522D',    // Light urban
                    0.4, '#8B4513',    // Dense urban
                    0.6, '#800000'     // Very dense urban
                );
            } else if (indexType === 'moisture') {
                fillColor.push(
                    -0.8, '#8B0000',   // Extreme stress
                    -0.6, '#CD5C5C',   // High stress
                    -0.4, '#F08080',   // Moderate stress
                    -0.2, '#FFFF00',   // Low stress
                    0, '#90EE90',      // Normal
                    0.2, '#00FFFF',    // High moisture
                    0.4, '#00008B'     // Very high moisture
                );
            }

            // Add fill layer
            this.map.addLayer({
                id: id,
                type: 'fill',
                source: id,
                paint: {
                    'fill-color': fillColor,
                    'fill-opacity': 0.6
                }
            });

            // Add outline layer for better visibility
            this.map.addLayer({
                id: `${id}-outline`,
                type: 'line',
                source: id,
                paint: {
                    'line-color': '#ffffff',
                    'line-width': 1,
                    'line-opacity': 0.5
                }
            });

            this.activeLayers.add(id);
            this.activeLayers.add(`${id}-outline`);

            // Show legend
            this.showLegend(indexType);

            console.log(`✅ Vector layer ${id} added with ${geojson.features.length} features`);

        } catch (e) {
            console.error('❌ Vector layer error:', e);
        }
    }

    /**
     * Show legend for the active layer
     * @param {string} layerType 
     */
    showLegend(layerType) {
        const legendContainer = document.getElementById('legend-container');
        if (!legendContainer) return;

        const legendHTML = this.getLegendHTML(layerType);
        if (legendHTML) {
            legendContainer.innerHTML = legendHTML;
            legendContainer.classList.remove('hidden');
        }
    }

    /**
     * Get HTML for legend based on layer type
     * @param {string} layerType 
     * @returns {string} HTML string
     */
    getLegendHTML(layerType) {
        if (layerType === 'ndvi') {
            return `
                <div class="legend-item" style="font-family: sans-serif; font-size: 12px;">
                    <h4 style="margin: 0 0 8px;">NDVI (Vegetation)</h4>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #D73027; display: inline-block; margin-right: 8px;"></span>
                        <span>&lt; 0: Water, Asphalt</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #FC8D59; display: inline-block; margin-right: 8px;"></span>
                        <span>0 - 0.2: Bare Soil, Buildings</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #FEE090; display: inline-block; margin-right: 8px;"></span>
                        <span>0.2 - 0.4: Sparse Vegetation</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #41A636; display: inline-block; margin-right: 8px;"></span>
                        <span>0.4 - 0.6: Moderate Vegetation</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #168043; display: inline-block; margin-right: 8px;"></span>
                        <span>&gt; 0.6: Dense Vegetation</span>
                    </div>

                    <div style="background: linear-gradient(to right, #D73027, #FC8D59, #FEE090, #41A636, #168043); height: 8px; width: 100%; margin-top: 8px; border-radius: 4px;"></div>
                </div>
            `;
        } else if (layerType === 'ndwi') {
            return `
                <div class="legend-item" style="font-family: sans-serif; font-size: 12px;">
                    <h4 style="margin: 0 0 8px;">NDWI (Water Index)</h4>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #00005C; display: inline-block; margin-right: 8px;"></span>
                        <span>&lt; 0: Dry Soil, Asphalt</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #0000CD; display: inline-block; margin-right: 8px;"></span>
                        <span>0 - 0.2: Moderate Moisture</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #4169E1; display: inline-block; margin-right: 8px;"></span>
                        <span>0.2 - 0.5: Moist Soil</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #87CEEB; display: inline-block; margin-right: 8px;"></span>
                        <span>&gt; 0.5: Water</span>
                    </div>

                    <div style="background: linear-gradient(to right, #00005C, #0000CD, #4169E1, #87CEEB); height: 8px; width: 100%; margin-top: 8px; border-radius: 4px;"></div>
                </div>
            `;
        } else if (layerType === 'ndbi') {
            return `
                <div class="legend-item" style="font-family: sans-serif; font-size: 12px;">
                    <h4 style="margin: 0 0 8px;">NDBI (Built-up)</h4>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #D73027; display: inline-block; margin-right: 8px;"></span>
                        <span>&lt; -0.5: Water</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #FFFFFF; display: inline-block; margin-right: 8px;"></span>
                        <span>-0.5 - 0: Vegetation</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #A0522D; display: inline-block; margin-right: 8px;"></span>
                        <span>0 - 0.2: Bare Soil</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #800000; display: inline-block; margin-right: 8px;"></span>
                        <span>&gt; 0.2: Built-up</span>
                    </div>

                    <div style="background: linear-gradient(to right, #D73027, #FFFFFF, #A0522D, #800000); height: 8px; width: 100%; margin-top: 8px; border-radius: 4px;"></div>
                </div>
            `;
        } else if (layerType === 'moisture') {
            return `
                <div class="legend-item" style="font-family: sans-serif; font-size: 12px;">
                    <h4 style="margin: 0 0 8px;">Moisture Index</h4>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #8B0000; display: inline-block; margin-right: 8px;"></span>
                        <span>&lt; -0.6: Stress</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #FFFF00; display: inline-block; margin-right: 8px;"></span>
                        <span>-0.6 - -0.2: Moderate</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #00FFFF; display: inline-block; margin-right: 8px;"></span>
                        <span>-0.2 - 0.2: High</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="width: 15px; height: 15px; background: #00008B; display: inline-block; margin-right: 8px;"></span>
                        <span>&gt; 0.2: Very High</span>
                    </div>

                    <div style="background: linear-gradient(to right, #8B0000, #FFFF00, #00FFFF, #00008B); height: 8px; width: 100%; margin-top: 8px; border-radius: 4px;"></div>
                </div>
            `;
        }
    }
}
