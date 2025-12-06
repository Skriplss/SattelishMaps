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
        this.slovakiaData = null; // Кэшируем данные Словакии
    }

    init(theme = 'light') {
        try {
            console.log('🗺️ Initializing map...');

            // Всегда используем светлый стиль для самой карты
            const mapStyle = 'https://api.maptiler.com/maps/dataviz-light/style.json?key=' + this.apiKey;

            this.map = new maptilersdk.Map({
                container: this.containerId,
                apiKey: this.apiKey,
                style: mapStyle,
                center: this.currentCenter,
                zoom: this.currentZoom,
                minZoom: 2,
                maxZoom: 18,
                pitch: 0,        // Только вид сверху
                maxPitch: 0,     // Запрет наклона карты
                bearing: 0       // Север всегда сверху
            });

            this.map.on('load', () => {
                console.log('✅ Map loaded successfully!');
                this.addSlovakiaMask(theme);  // Передаем тему
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

    setMapStyle(theme) {
        if (!this.map) return;

        // Проверяем наличие слоя перед обновлением
        if (!this.map.getLayer('world-gray-layer')) {
            console.warn('⚠️ Layer world-gray-layer not found, retrying initialization...');
            this.addSlovakiaMask(theme);
            return;
        }

        console.log('🎨 Updating map theme visuals to:', theme);

        // Мы больше не меняем базовый стиль карты (всегда light),
        // но меняем затемнение окружающего мира для комфорта глаз
        const grayOpacity = theme === 'dark' ? 0.85 : 0.7;

        this.map.setPaintProperty(
            'world-gray-layer',
            'fill-opacity',
            grayOpacity
        );

        console.log('✅ Map visuals updated (opacity:', grayOpacity + ')');
    }

    async addSlovakiaMask(theme = 'light') {
        console.log('🎭 Adding color scheme... Theme:', theme);

        const worldPolygon = [
            [-180, -90],
            [180, -90],
            [180, 90],
            [-180, 90],
            [-180, -90]
        ];

        // Задаем параметры визуализации
        const grayOpacity = theme === 'dark' ? 0.85 : 0.7;
        const borderColor = '#000000'; // Всегда черная граница на светлой карте

        console.log('📊 Gray opacity:', grayOpacity);

        try {
            let slovakia = this.slovakiaData;

            if (!slovakia) {
                console.log('🌐 Fetching Slovakia borders...');
                const response = await fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson');
                const countriesData = await response.json();
                console.log('✅ GeoJSON loaded, features count:', countriesData.features.length);

                slovakia = countriesData.features.find(
                    feature => feature.properties.ADMIN === 'Slovakia' ||
                        feature.properties.name === 'Slovakia' ||
                        feature.properties.ISO_A3 === 'SVK'
                );

                this.slovakiaData = slovakia;
                console.log('💾 Slovakia data cached');
            } else {
                console.log('💾 Using cached Slovakia data');
            }

            if (slovakia) {
                console.log('✅ Slovakia found');

                const slovakiaCoords = slovakia.geometry.coordinates;
                console.log('📍 Slovakia coordinates count:', slovakiaCoords.length);

                console.log('🧹 Cleaning up old layers...');

                if (this.map.getLayer('world-gray-layer')) this.map.removeLayer('world-gray-layer');
                if (this.map.getSource('world-gray')) this.map.removeSource('world-gray');

                if (this.map.getLayer('slovakia-border')) this.map.removeLayer('slovakia-border');
                if (this.map.getSource('slovakia-border-source')) this.map.removeSource('slovakia-border-source');

                console.log('➕ Adding new layers...');

                this.map.addSource('world-gray', {
                    type: 'geojson',
                    data: {
                        type: 'Feature',
                        geometry: {
                            type: 'Polygon',
                            coordinates: [worldPolygon, ...slovakiaCoords]
                        }
                    }
                });

                this.map.addLayer({
                    id: 'world-gray-layer',
                    type: 'fill',
                    source: 'world-gray',
                    paint: {
                        'fill-color': '#808080',
                        'fill-opacity': grayOpacity
                    }
                });

                this.map.addSource('slovakia-border-source', {
                    type: 'geojson',
                    data: slovakia
                });

                this.map.addLayer({
                    id: 'slovakia-border',
                    type: 'line',
                    source: 'slovakia-border-source',
                    paint: {
                        'line-color': borderColor,
                        'line-width': 2.5,
                        'line-opacity': 0.9
                    }
                });



                console.log('✅ Real Slovakia borders loaded successfully!');
            } else {
                console.warn('⚠️ Slovakia not found in GeoJSON');
            }
        } catch (error) {
            console.error('❌ Error loading Slovakia borders:', error);
        }
    }
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        console.log('🌓 Toggling theme to:', newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);

        // User requested to darken the area around Slovakia in dark theme
        this.setMapStyle(newTheme);

        return newTheme;
    }
}
