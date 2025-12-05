/*
   MAP CLASS - Denis's satellite map
   Adapted to work without ES6 modules
*/

class SatelliteMap {
    constructor(containerId, apiKey) {
        this.containerId = containerId;
        this.apiKey = apiKey;
        this.map = null;
        this.currentZoom = 7;
        this.currentCenter = [19.6987, 48.6692]; // Bratislava, Slovakia
        this.layers = [];
    }

    init() {
        try {
            console.log('🗺️ Initializing map...');

            // Slovakia bounds: [west, south, east, north]
            const slovakiaBounds = [
                [16.8, 47.7],  // Southwest coordinates
                [22.6, 49.6]   // Northeast coordinates
            ];

            this.map = new maptilersdk.Map({
                container: this.containerId,
                apiKey: this.apiKey,
                style: maptilersdk.MapStyle.SATELLITE,
                center: this.currentCenter,
                zoom: this.currentZoom,
                maxBounds: slovakiaBounds, // Restrict map to Slovakia
                minZoom: 6,
                maxZoom: 18
            });

            this.map.on('load', () => {
                console.log('✅ Map loaded successfully!');
                this.setupControls();
                this.setupEventListeners();
            });

            this.map.on('error', (e) => {
                console.error('❌ Map error:', e);
            });

        } catch (error) {
            console.error('❌ Error initializing map:', error);
        }
    }

    setupControls() {
        console.log('🎮 Setting up controls...');

        const zoomInBtn = document.getElementById('zoom-in');
        const zoomOutBtn = document.getElementById('zoom-out');

        zoomInBtn.addEventListener('click', () => {
            this.zoomIn();
        });

        zoomOutBtn.addEventListener('click', () => {
            this.zoomOut();
        });
    }

    setupEventListeners() {
        console.log('👂 Setting up event listeners...');

        this.map.on('click', (e) => {
            console.log('📍 Map click:', e.lngLat);
        });

        this.map.on('zoom', () => {
            this.currentZoom = this.map.getZoom();
            console.log('🔍 Current zoom:', this.currentZoom.toFixed(2));
        });

        this.map.on('move', () => {
            this.currentCenter = this.map.getCenter();
        });
    }

    zoomIn() {
        console.log('➕ Zoom in');
        this.map.zoomIn();
    }

    zoomOut() {
        console.log('➖ Zoom out');
        this.map.zoomOut();
    }

    flyTo(coordinates, zoom = 12) {
        console.log('✈️ Flying to:', coordinates);
        this.map.flyTo({
            center: coordinates,
            zoom: zoom,
            duration: 2000
        });
    }

    getBounds() {
        const bounds = this.map.getBounds();
        console.log('📐 Map bounds:', bounds);
        return bounds;
    }

    showLoader() {
        const loader = document.getElementById('loader');
        loader.classList.remove('hidden');
    }

    hideLoader() {
        const loader = document.getElementById('loader');
        loader.classList.add('hidden');
    }
}
