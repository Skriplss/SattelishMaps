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
     * Adds a raster layer to the map
     */
    addRasterLayer(id, url, options = {}) {
        if (!this.map || !this.map.getSource) {
            console.error('Map instance not ready');
            return;
        }

        this.removeLayer(id);

        console.log(`Adding raster layer: ${id}`);

        try {
            this.map.addSource(id, {
                type: 'raster',
                tiles: [url],
                tileSize: 256,
                attribution: 'Sentinel-2 Data'
            });

            // Ensure satellite image is below overlay layers
            let beforeLayerId = undefined;

            if (this.map.getLayer('world-gray-layer')) {
                beforeLayerId = 'world-gray-layer';
            } else if (this.map.getLayer('slovakia-border')) {
                beforeLayerId = 'slovakia-border';
            } else {
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
            console.log(`Layer ${id} added successfully`);

        } catch (error) {
            console.error(`Error adding layer ${id}:`, error);
        }
    }

    /**
     * Removes a layer and its source
     */
    removeLayer(id) {
        if (!this.map) return;

        if (this.map.getLayer(id)) {
            this.map.removeLayer(id);
            this.activeLayers.delete(id);
            console.log(`Layer ${id} removed`);
        }

        if (this.map.getSource(id)) {
            this.map.removeSource(id);
        }
    }

    /**
     * Updates opacity of an existing layer
     */
    setLayerOpacity(id, opacity) {
        if (this.map && this.map.getLayer(id)) {
            this.map.setPaintProperty(id, 'raster-opacity', opacity);
        }
    }

    clearAll() {
        this.activeLayers.forEach(id => this.removeLayer(id));
    }

    /**
     * Show a specific layer type using WMS tiles
     */
    async showLayer(layerType) {
        console.log(`Showing layer: ${layerType}`);

        try {
            const mapDateInput = document.getElementById('map-date');

            if (!mapDateInput || !mapDateInput.value) {
                console.error('No date selected');
                alert('Пожалуйста, выберите дату');
                return;
            }

            const selectedDate = mapDateInput.value;
            console.log(`Selected date: ${selectedDate}`);

            this.clearAll();

            const loader = document.getElementById('loader');
            if (loader) loader.classList.remove('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = 'wait';

            const API_BASE_URL = window.SatelliteAPI?.API_BASE_URL || 'http://localhost:8000';
            const tileUrl = `${API_BASE_URL}/api/wms/tile/{z}/{x}/{y}.png?date=${selectedDate}&index_type=${layerType.toUpperCase()}`;

            console.log(`Loading WMS tiles: ${tileUrl}`);

            this.addRasterLayer(layerType, tileUrl, { opacity: 0.8 });
            this.showLegend(layerType);

            if (loader) loader.classList.add('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = '';

            console.log(`WMS layer ${layerType} loaded successfully`);

        } catch (error) {
            console.error('Failed to show layer:', error);

            const loader = document.getElementById('loader');
            if (loader) loader.classList.add('hidden');
            if (window.satelliteMap) window.satelliteMap.map.getCanvas().style.cursor = '';

            alert(`Ошибка загрузки данных: ${error.message}`);
        }
    }

    /**
     * Add vector layer from region statistics GeoJSON
     */
    addVectorLayerFromRegionStats(id, geojson) {
        if (!this.map) return;
        this.removeLayer(id);

        try {
            this.map.addSource(id, {
                type: 'geojson',
                data: geojson
            });

            const indexType = geojson.features[0]?.properties?.index_type?.toLowerCase() || id;

            let fillColor = [
                'interpolate',
                ['linear'],
                ['get', 'mean'],
                -1, '#000000'
            ];

            if (indexType === 'ndvi') {
                fillColor.push(
                    -0.1, '#8B4513',
                    0, '#D2B48C',
                    0.2, '#FEE090',
                    0.4, '#91CF60',
                    0.6, '#41A636',
                    0.8, '#006400'
                );
            } else if (indexType === 'ndwi') {
                fillColor.push(
                    -0.5, '#8B4513',
                    -0.2, '#D2B48C',
                    0, '#87CEEB',
                    0.2, '#4169E1',
                    0.5, '#0000CD',
                    1.0, '#000080'
                );
            } else if (indexType === 'ndbi') {
                fillColor.push(
                    -0.5, '#0000CD',
                    -0.2, '#228B22',
                    0, '#D2B48C',
                    0.2, '#A0522D',
                    0.4, '#8B4513',
                    0.6, '#800000'
                );
            } else if (indexType === 'moisture') {
                fillColor.push(
                    -0.8, '#8B0000',
                    -0.6, '#CD5C5C',
                    -0.4, '#F08080',
                    -0.2, '#FFFF00',
                    0, '#90EE90',
                    0.2, '#00FFFF',
                    0.4, '#00008B'
                );
            }

            this.map.addLayer({
                id: id,
                type: 'fill',
                source: id,
                paint: {
                    'fill-color': fillColor,
                    'fill-opacity': 0.6
                }
            });

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

            this.showLegend(indexType);

            console.log(`Vector layer ${id} added with ${geojson.features.length} features`);

        } catch (e) {
            console.error('Vector layer error:', e);
        }
    }

    showLegend(layerType) {
        const legendContainer = document.getElementById('legend-container');
        if (!legendContainer) return;

        const legendHTML = this.getLegendHTML(layerType);
        if (legendHTML) {
            legendContainer.innerHTML = legendHTML;
            legendContainer.classList.remove('hidden');
        }
    }

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
