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
}
