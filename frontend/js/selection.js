class AreaSelector {
    constructor(map) {
        this.map = map;
        this.isActive = false;
        this.isDragging = false;
        this.selectedFeature = null; // 'nw', 'ne', 'se', 'sw' or null
        this.activeAreaId = null; // ID of the area currently being edited/dragged

        this.areas = []; // Array of { id, coordinates, marker }
        // coordinates: [minLng, minLat, maxLng, maxLat]

        // DOM Elements
        this.cursor = document.getElementById('area-selection-cursor');
        this.btn = document.getElementById('select-area-btn');

        this.init();
    }

    init() {
        this.map.on('load', () => {
            this.addSourcesAndLayers();
        });

        // Event Listeners
        if (this.btn) {
            console.log('AreaSelector: Button found, attaching listener');
            this.btn.addEventListener('click', (e) => {
                console.log('AreaSelector: Button clicked');
                e.stopPropagation();
                this.toggleMode();
            });
        } else {
            console.error('AreaSelector: Button NOT found');
        }

        // Mouse tracking for custom cursor
        document.addEventListener('mousemove', (e) => this.updateCursorPosition(e));

        // Map interactions
        this.map.on('click', (e) => this.handleMapClick(e));

        // Dragging handles
        this.map.on('mousedown', 'area-handles', (e) => this.onHandleMouseDown(e));
        this.map.on('mouseenter', 'area-handles', () => this.map.getCanvas().style.cursor = 'move');
        this.map.on('mouseleave', 'area-handles', () => this.map.getCanvas().style.cursor = '');

        // Global mouse events for dragging
        this.map.on('mousemove', (e) => this.onMapMouseMove(e));
        this.map.on('mouseup', () => this.onMapMouseUp());

        // Escape to cancel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.deactivate();
        });
    }

    addSourcesAndLayers() {
        // Source for the polygons
        this.map.addSource('area-polygons', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] }
        });

        // Source for handles (points)
        this.map.addSource('area-handles', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] }
        });

        // Polygon Fill
        this.map.addLayer({
            id: 'area-polygon-fill',
            type: 'fill',
            source: 'area-polygons',
            paint: {
                'fill-color': ['get', 'color'],
                'fill-opacity': 0.3
            }
        });

        // Polygon Outline
        this.map.addLayer({
            id: 'area-polygon-outline',
            type: 'line',
            source: 'area-polygons',
            paint: {
                'line-color': ['get', 'borderColor'],
                'line-width': 2,
                'line-dasharray': [2, 2]
            }
        });

        // Handles (Circles)
        this.map.addLayer({
            id: 'area-handles',
            type: 'circle',
            source: 'area-handles',
            paint: {
                'circle-radius': 6,
                'circle-color': '#fff',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#000'
            }
        });
    }

    toggleMode() {
        if (this.isActive) {
            this.deactivate();
        } else {
            this.activate();
        }
    }

    activate() {
        // Check limit
        if (this.areas.length >= 2) {
            // FIFO: Remove the first area to make room
            this.removeArea(this.areas[0].id);
        }

        this.isActive = true;
        if (this.cursor) this.cursor.classList.remove('hidden');
        document.body.classList.add('selection-mode');
    }

    deactivate() {
        this.isActive = false;
        if (this.cursor) this.cursor.classList.add('hidden');
        document.body.classList.remove('selection-mode');
    }

    updateCursorPosition(e) {
        if (this.isActive && this.cursor && !this.cursor.classList.contains('hidden')) {
            this.cursor.style.left = e.clientX + 'px';
            this.cursor.style.top = e.clientY + 'px';
        }
    }

    handleMapClick(e) {
        if (!this.isActive) return;

        // Create initial box matching the cursor size (100px x 100px)
        const centerPoint = e.point;
        const halfSize = 50;

        const nw = this.map.unproject([centerPoint.x - halfSize, centerPoint.y - halfSize]);
        const se = this.map.unproject([centerPoint.x + halfSize, centerPoint.y + halfSize]);

        const newArea = {
            id: Date.now().toString(),
            coordinates: [
                nw.lng, // minLng
                se.lat, // minLat
                se.lng, // maxLng
                nw.lat  // maxLat
            ],
            color: this.areas.length === 0 ? '#666666' : '#CA747D', // Different colors for areas? Or same? Let's use different for distinction if needed, but user asked for "2 squares".
            borderColor: '#333333'
        };

        // Add to state
        this.areas.push(newArea);

        // Create Marker (X button)
        this.createMarker(newArea);

        // Update Map
        this.updateGeoJSON();

        // Hide cursor, stop placing mode
        this.deactivate();

        // Update Stats
        this.updateStats();
    }

    createMarker(area) {
        const el = document.createElement('div');
        el.className = 'area-close-btn';
        el.innerHTML = '×';
        el.style.backgroundColor = 'white';
        el.style.color = 'black';
        el.style.width = '20px';
        el.style.height = '20px';
        el.style.borderRadius = '50%';
        el.style.textAlign = 'center';
        el.style.lineHeight = '20px';
        el.style.cursor = 'pointer';
        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
        el.style.fontWeight = 'bold';
        el.style.fontSize = '16px';

        el.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeArea(area.id);
        });

        // Position at NE corner with offset to avoid overlapping the resize handle
        const [minLng, minLat, maxLng, maxLat] = area.coordinates;

        const marker = new maptilersdk.Marker({
            element: el,
            offset: [15, -15] // Move 15px right and 15px up
        })
            .setLngLat([maxLng, maxLat])
            .addTo(this.map);

        area.marker = marker;
    }

    removeArea(id) {
        const index = this.areas.findIndex(a => a.id === id);
        if (index !== -1) {
            const area = this.areas[index];
            if (area.marker) area.marker.remove();
            this.areas.splice(index, 1);
            this.updateGeoJSON();
            this.updateStats();
        }
    }

    updateGeoJSON() {
        // Update Polygons
        const features = this.areas.map(area => {
            const [minLng, minLat, maxLng, maxLat] = area.coordinates;
            return {
                type: 'Feature',
                properties: {
                    id: area.id,
                    color: area.color,
                    borderColor: area.borderColor
                },
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [minLng, maxLat], // NW
                        [maxLng, maxLat], // NE
                        [maxLng, minLat], // SE
                        [minLng, minLat], // SW
                        [minLng, maxLat]  // Close loop
                    ]]
                }
            };
        });

        this.map.getSource('area-polygons').setData({
            type: 'FeatureCollection',
            features: features
        });

        // Update Handles (for all areas)
        const handleFeatures = [];
        this.areas.forEach(area => {
            const [minLng, minLat, maxLng, maxLat] = area.coordinates;
            handleFeatures.push(
                { type: 'Feature', properties: { id: 'nw', areaId: area.id }, geometry: { type: 'Point', coordinates: [minLng, maxLat] } },
                { type: 'Feature', properties: { id: 'ne', areaId: area.id }, geometry: { type: 'Point', coordinates: [maxLng, maxLat] } },
                { type: 'Feature', properties: { id: 'se', areaId: area.id }, geometry: { type: 'Point', coordinates: [maxLng, minLat] } },
                { type: 'Feature', properties: { id: 'sw', areaId: area.id }, geometry: { type: 'Point', coordinates: [minLng, minLat] } }
            );
        });

        this.map.getSource('area-handles').setData({
            type: 'FeatureCollection',
            features: handleFeatures
        });
    }

    onHandleMouseDown(e) {
        if (e.features.length > 0) {
            e.preventDefault();
            this.isDragging = true;
            this.selectedFeature = e.features[0].properties.id;
            this.activeAreaId = e.features[0].properties.areaId;
            this.map.dragPan.disable();
        }
    }

    onMapMouseMove(e) {
        if (!this.isDragging || !this.selectedFeature || !this.activeAreaId) return;

        const lng = e.lngLat.lng;
        const lat = e.lngLat.lat;

        const area = this.areas.find(a => a.id === this.activeAreaId);
        if (!area) return;

        let [minLng, minLat, maxLng, maxLat] = area.coordinates;

        // Update coordinates based on which handle is dragged
        switch (this.selectedFeature) {
            case 'nw': minLng = lng; maxLat = lat; break;
            case 'ne': maxLng = lng; maxLat = lat; break;
            case 'se': maxLng = lng; minLat = lat; break;
            case 'sw': minLng = lng; minLat = lat; break;
        }

        area.coordinates = [minLng, minLat, maxLng, maxLat];
        this.updateGeoJSON();

        // Update marker position (NE corner)
        if (area.marker) {
            area.marker.setLngLat([maxLng, maxLat]);
        }
    }

    onMapMouseUp() {
        if (this.isDragging) {
            this.isDragging = false;
            this.selectedFeature = null;
            this.activeAreaId = null;
            this.map.dragPan.enable();

            this.updateStats();
        }
    }

    updateStats() {
        if (window.statsPanel) {
            // Determine active layer from DOM
            const activeBtn = document.querySelector('.layer-btn.active');
            const activeLayer = activeBtn ? activeBtn.dataset.layer : 'ndvi';

            // Pass all areas to stats panel
            window.statsPanel.open(this.areas, activeLayer);
        }
    }

    clearSelection() {
        // Remove all markers
        this.areas.forEach(area => {
            if (area.marker) area.marker.remove();
        });
        this.areas = [];
        this.updateGeoJSON();
    }
}
