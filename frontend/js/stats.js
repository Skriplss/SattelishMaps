class StatsPanel {
    constructor() {
        this.panel = document.getElementById('stats-panel');
        this.closeBtn = document.getElementById('close-stats');
        this.chartCanvas = document.getElementById('ndvi-chart');
        this.aiTextBox = document.getElementById('ai-analysis-text');
        this.chart = null;
        this.currentAreas = []; // Array of area objects
        this.activeLayer = 'ndvi';

        // Export Elements
        this.exportBtn = document.getElementById('export-btn');
        this.exportDropdown = document.getElementById('export-dropdown');
        this.exportTextBtn = document.getElementById('export-text');
        this.exportChartBtn = document.getElementById('export-chart');

        this.init();
    }

    init() {
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        // Setup Chart
        this.initChart();

        // Export Listeners
        if (this.exportBtn) {
            this.exportBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleExportDropdown();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.exportDropdown && this.exportDropdown.classList.contains('open')) {
                if (!this.exportDropdown.contains(e.target) && e.target !== this.exportBtn) {
                    this.exportDropdown.classList.remove('open');
                }
            }
        });

        if (this.exportTextBtn) {
            this.exportTextBtn.addEventListener('click', () => this.exportText());
        }

        if (this.exportChartBtn) {
            this.exportChartBtn.addEventListener('click', () => this.exportChart());
        }
    }

    toggleExportDropdown() {
        if (this.exportDropdown) {
            this.exportDropdown.classList.toggle('open');
        }
    }

    exportText() {
        if (!this.aiTextBox) return;

        const text = this.aiTextBox.textContent.trim();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.toggleExportDropdown(); // Close after click
    }

    exportChart() {
        if (!this.chartCanvas) return;

        const url = this.chartCanvas.toDataURL('image/png');

        const a = document.createElement('a');
        a.href = url;
        a.download = `chart_${new Date().toISOString().slice(0, 10)}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        this.toggleExportDropdown(); // Close after click
    }

    initChart() {
        if (!this.chartCanvas) return;

        const ctx = this.chartCanvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [], // Will be set dynamically
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        min: -0.2,
                        max: 1.0
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                animation: {
                    duration: 800 // Smooth animation
                }
            }
        });
    }

    open(areas, activeLayer) {
        this.currentAreas = areas || [];
        this.activeLayer = activeLayer || 'ndvi';

        this.panel.classList.add('open');
        document.body.classList.add('stats-open');

        this.updateLanguage(window.languageManager ? window.languageManager.currentLang : 'sk');
    }

    close() {
        this.panel.classList.remove('open');
        document.body.classList.remove('stats-open');

        // We DO NOT clear selection here anymore, because user might want to keep areas selected
        // while closing the panel. Or maybe we should? 
        // User requested "X" buttons on areas, implying they manage areas manually.
        // So closing stats panel shouldn't necessarily delete areas.
    }

    updateLanguage(lang) {
        if (!this.chart) return;

        // Update Chart Labels
        this.chart.data.labels = translations[lang]['chart.months'];

        // Re-render chart with current data
        this.renderChart(lang);

        // Update AI Analysis
        this.updateAIAnalysis(lang);
    }

    async renderChart(lang) {
        if (!this.chart) return;

        console.log('📈 Rendering chart...');
        const datasets = [];
        const colors = ['#41A636', '#CA747D', '#5D9CEC', '#F0AD4E'];

        // Clear existing data while loading
        this.chart.data.labels = [];
        this.chart.data.datasets = [];
        this.chart.update();

        for (let index = 0; index < this.currentAreas.length; index++) {
            const area = this.currentAreas[index];
            const color = colors[index % colors.length];

            // Calculate center
            const center = this.getPolygonCenter(area.coordinates);

            // Try to identify region
            const regionName = this.identifyRegion(center.lat, center.lng);
            let data = [];
            let timestamps = [];

            if (regionName) {
                console.log(`📍 Area ${index + 1} identified as ${regionName}`);
                // Fetch real data
                try {
                    const history = await SatelliteAPI.fetchRegionHistory(regionName, this.activeLayer);
                    if (history && history.length > 0) {
                        data = history.map(h => h.mean); // Use mean value
                        timestamps = history.map(h => h.date);
                    }
                } catch (e) {
                    console.error('Failed to fetch history:', e);
                }
            }

            // Fallback to mock/simulated data if no real data found
            if (data.length === 0) {
                console.log(`⚠️ No real data for Area ${index + 1}, using simulation`);
                data = this.generateData(area.coordinates);
                // Generate dummy months
                timestamps = translations[lang]['chart.months'];
            }

            // Update labels if this is the first dataset (or if we have real dates now)
            // Ideally we should sync X-axis, but for now take the first valid one
            if (timestamps.length > 0 && (this.chart.data.labels.length === 0 || regionName)) {
                // If real data, format dates
                if (regionName) {
                    this.chart.data.labels = timestamps.map(t => new Date(t).toLocaleDateString(lang, { month: 'short', day: 'numeric' }));
                } else {
                    this.chart.data.labels = timestamps;
                }
            }

            datasets.push({
                label: `${translations[lang][`chart.${this.activeLayer}`]} - ${regionName || `Area ${index + 1}`}`,
                data: data,
                borderColor: color,
                backgroundColor: color + '33',
                borderWidth: 2,
                tension: 0.4,
                fill: false
            });
        }

        this.chart.data.datasets = datasets;
        this.chart.update();
    }

    getPolygonCenter(coords) {
        if (!coords || coords.length === 0) return { lat: 0, lng: 0 };
        // coords is array of [lng, lat] (GeoJSON) or {lat, lng} (Leaflet/Mapbox)
        // Assuming flat array [lng, lat] from earlier context, or check structure
        // In addSlovakiaMask it was [ [lng, lat], ... ]

        let sumLat = 0, sumLng = 0;
        let count = 0;

        // Handle nested arrays like [[lng, lat], [lng, lat]]
        // or Leaflet {lat, lng}
        const points = Array.isArray(coords[0]) ? coords : coords;

        points.forEach(p => {
            if (Array.isArray(p)) {
                sumLng += p[0];
                sumLat += p[1];
            } else {
                sumLat += p.lat;
                sumLng += p.lng;
            }
            count++;
        });

        return { lat: sumLat / count, lng: sumLng / count };
    }

    identifyRegion(lat, lng) {
        const regions = [
            { name: "Bratislava", lat: 48.1486, lng: 17.1077 },
            { name: "Kosice", lat: 48.7164, lng: 21.2611 },
            { name: "Zilina", lat: 49.2195, lng: 18.7408 },
            { name: "Banska Bystrica", lat: 48.7363, lng: 19.1462 },
            { name: "Presov", lat: 48.9973, lng: 21.2393 }
        ];

        for (const region of regions) {
            const dist = Math.sqrt(Math.pow(lat - region.lat, 2) + Math.pow(lng - region.lng, 2));
            // Approx distance in degrees. 0.2 deg ~ 20km
            if (dist < 0.25) {
                return region.name;
            }
        }
        return null;
    }

    generateData(coordinates) {
        // Simulate data based on coordinates hash
        // Modified to return 12 points
        const data = [];
        for (let i = 0; i < 12; i++) {
            const val = 0.3 + (Math.random() * 0.5);
            data.push(Math.max(0, Math.min(1, val)));
        }
        return data;
    }

    updateAIAnalysis(lang) {
        if (!this.aiTextBox) return;

        if (this.currentAreas.length === 0) {
            this.aiTextBox.textContent = translations[lang]['ai.no_data'];
            return;
        }

        // Simple logic for now
        if (this.currentAreas.length === 1) {
            if (this.activeLayer === 'ndvi') {
                this.aiTextBox.textContent = translations[lang]['ai.ndvi_only'];
            } else if (this.activeLayer === 'ndwi') {
                this.aiTextBox.textContent = translations[lang]['ai.ndwi_only'];
            } else if (this.activeLayer === 'ndbi') {
                this.aiTextBox.textContent = translations[lang]['ai.ndbi_only'];
            } else if (this.activeLayer === 'moisture') {
                this.aiTextBox.textContent = translations[lang]['ai.moisture_only'];
            }
        } else {
            // Comparison text
            this.aiTextBox.textContent = translations[lang]['ai.comparison'];
        }
    }
}
