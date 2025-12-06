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
     * Show a specific layer type (ndvi, ndwi, etc.) using mock data for now
     * @param {string} layerType
     */
    showLayer(layerType) {
        console.log(`👁️ Showing layer: ${layerType}`);

        // Use Mock Data from SatelliteAPI
        if (window.SatelliteAPI && window.SatelliteAPI.MOCK_SATELLITE_DATA) {
            const scene = window.SatelliteAPI.MOCK_SATELLITE_DATA[0];
            const url = scene.bands[layerType];

            if (url) {
                // Remove other layers first to avoid clutter
                this.clearAll();
                this.addRasterLayer(layerType, url, { opacity: 1.0 });
            } else {
                console.warn(`⚠️ No URL found for layer type: ${layerType}`);
            }
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
        }
        return '';
    }
}
