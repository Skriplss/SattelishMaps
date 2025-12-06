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

    renderChart(lang) {
        if (!this.chart) return;

        const datasets = [];
        const colors = ['#41A636', '#CA747D']; // Area 1 (Green-ish), Area 2 (Red-ish)

        this.currentAreas.forEach((area, index) => {
            const data = this.generateData(area.coordinates);
            const color = colors[index % colors.length];

            datasets.push({
                label: `${translations[lang][`chart.${this.activeLayer}`]} - Area ${index + 1}`,
                data: data,
                borderColor: color,
                backgroundColor: color + '33', // Transparent fill
                borderWidth: 2,
                tension: 0.4,
                fill: false
            });
        });

        this.chart.data.datasets = datasets;
        this.chart.update();
    }

    generateData(coordinates) {
        // Simulate data based on coordinates hash
        const seed = coordinates.reduce((a, b) => a + b, 0);
        const data = [];
        for (let i = 0; i < 12; i++) {
            // Randomish but consistent for same area
            const val = 0.3 + (Math.sin(i * 0.5 + seed) * 0.2) + (Math.random() * 0.1);
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
