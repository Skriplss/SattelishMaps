/* main.js */

// Global state
const MAPTILER_API_KEY = 'zCLzX9B3EgED7gCQmdAo'; // TODO: Replace with your API key

// Language Manager
class LanguageManager {
   constructor() {
      this.currentLang = 'sk'; // Default
      this.langBtn = document.getElementById('lang-btn');
      this.init();
   }

   init() {
      if (this.langBtn) {
         // Remove old listener if possible, but easier to just clone node or assume new listener overrides
         // Actually, we are replacing the init code, so old listener won't be attached if we do it right.
         // But wait, initEventListeners is called in DOMContentLoaded.
         // We need to make sure we don't attach the old listener.
         this.langBtn.replaceWith(this.langBtn.cloneNode(true));
         this.langBtn = document.getElementById('lang-btn'); // Re-select
         this.langBtn.addEventListener('click', () => this.toggleLanguage());
      }
      this.updateUI();
   }

   toggleLanguage() {
      this.currentLang = this.currentLang === 'sk' ? 'en' : 'sk';
      this.updateUI();

      // Notify other components
      if (window.statsPanel) {
         window.statsPanel.updateLanguage(this.currentLang);
      }
   }

   updateUI() {
      // Update Button
      const icon = this.langBtn.querySelector('.icon');
      const label = this.langBtn.querySelector('.label');

      if (this.currentLang === 'sk') {
         icon.textContent = '🇸🇰';
         // label is updated via data-i18n below
      } else {
         icon.textContent = '🇺🇸'; // US Flag for English
      }

      // Update all text elements
      document.querySelectorAll('[data-i18n]').forEach(element => {
         const key = element.getAttribute('data-i18n');
         if (translations[this.currentLang][key]) {
            element.textContent = translations[this.currentLang][key];
         }
      });
   }
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
   // Set default dates to TODAY
   const today = new Date().toISOString().split('T')[0];

   const mapDate = document.getElementById('map-date');
   if (mapDate) mapDate.value = today;

   const dateTo = document.getElementById('date-to');
   if (dateTo) dateTo.value = today;

   initApp();
   initEventListeners();

   // Initialize Language Manager LAST to override any defaults
   window.languageManager = new LanguageManager();
});

function initApp() {
   console.log('🚀 SattelishMaps');

   try {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      // Assuming SatelliteMap is defined elsewhere or we just use maplibregl directly as in previous steps
      // But wait, the previous main.js had SatelliteMap usage. 
      // I should preserve the map initialization logic.
      // Let's use the simple maplibregl init from my previous attempt if SatelliteMap is not available,
      // OR keep the existing one if it works.
      // The existing main.js uses `SatelliteMap` class. I should probably keep it if it exists.
      // However, I don't see SatelliteMap class definition in the file I viewed. It might be in another file.
      // Let's assume it's global.

      if (typeof SatelliteMap !== 'undefined') {
         window.satelliteMap = new SatelliteMap('map', MAPTILER_API_KEY);
         window.satelliteMap.init(currentTheme);
         window.satelliteLayers = new SatelliteLayers(window.satelliteMap.map);
      } else {
         // Fallback if SatelliteMap is not defined (e.g. if I missed including it)
         const map = new maplibregl.Map({
            container: 'map',
            style: 'https://api.maptiler.com/maps/dataviz-dark/style.json?key=zCLzX9B3EgED7gCQmdAo',
            center: [19.699, 48.669],
            zoom: 8
         });
         window.satelliteMap = { map: map }; // Mock for compatibility
      }

      console.log('✅ Ready');

   } catch (error) {
      console.error('❌ Init error:', error);
   }
}

function initEventListeners() {
   // Sidebar Menu
   const menuBtn = document.getElementById('menu-btn');
   if (menuBtn) {
      menuBtn.addEventListener('click', toggleFilters);
   }

   // Language Toggle - Handled by LanguageManager now
   // const langBtn = document.getElementById('lang-btn');
   // if (langBtn) {
   //    langBtn.addEventListener('click', toggleLanguage);
   // }

   // Theme Toggle
   const themeBtn = document.getElementById('theme-btn');
   if (themeBtn) {
      themeBtn.addEventListener('click', () => {
         // const newTheme = satelliteMap.toggleTheme(); // Assuming this works
         const currentTheme = document.documentElement.getAttribute('data-theme');
         const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
         document.documentElement.setAttribute('data-theme', newTheme);

         const icon = themeBtn.querySelector('.icon');
         if (icon) icon.textContent = newTheme === 'dark' ? '🌙' : '☀️';
      });
   }

   // Info Modal
   const infoBtn = document.getElementById('info-btn');
   const closeInfoBtn = document.getElementById('close-info');
   if (infoBtn) infoBtn.addEventListener('click', showInfo);
   if (closeInfoBtn) closeInfoBtn.addEventListener('click', hideInfo);

   // Calendar Inputs
   const dateFrom = document.getElementById('date-from');
   const dateTo = document.getElementById('date-to');
   if (dateFrom && dateTo) {
      dateFrom.addEventListener('change', applyFilters);
      dateFrom.addEventListener('change', applyFilters);
      dateTo.addEventListener('change', applyFilters);
   }

   // Map Date Input (Timeline)
   const mapDate = document.getElementById('map-date');
   const dtNavBtns = document.querySelectorAll('.dt-nav');

   if (mapDate) {
      mapDate.addEventListener('change', applyFilters);

      // Previous Day
      if (dtNavBtns[0]) {
         dtNavBtns[0].addEventListener('click', () => {
            const currentDate = new Date(mapDate.value || new Date());
            currentDate.setDate(currentDate.getDate() - 1);
            mapDate.value = currentDate.toISOString().split('T')[0];
            applyFilters();
         });
      }

      // Next Day
      if (dtNavBtns[1]) {
         dtNavBtns[1].addEventListener('click', () => {
            const currentDate = new Date(mapDate.value || new Date());
            currentDate.setDate(currentDate.getDate() + 1);
            mapDate.value = currentDate.toISOString().split('T')[0];
            applyFilters();
         });
      }
   }

   // Apply Filters Button
   const applyBtn = document.querySelector('.apply-filters-btn');
   if (applyBtn) {
      applyBtn.addEventListener('click', applyFilters);
   }

   // Layer Toggles
   const layerBtns = document.querySelectorAll('.layer-btn');
   layerBtns.forEach(btn => {
      btn.addEventListener('click', async (e) => {
         const isAlreadyActive = e.target.classList.contains('active');
         layerBtns.forEach(b => b.classList.remove('active'));

         if (!isAlreadyActive) {
            e.target.classList.add('active');
            // Show Area Selection Button
            const selectAreaBtn = document.getElementById('select-area-btn');
            if (selectAreaBtn) selectAreaBtn.classList.remove('hidden');
         } else {
            // Hide Area Selection Button
            const selectAreaBtn = document.getElementById('select-area-btn');
            if (selectAreaBtn) selectAreaBtn.classList.add('hidden');
         }
      });
   });

   // Map Clicks for Popup & Area Selection
   // Wait for map to be ready
   // Map Clicks for Popup & Area Selection
   // Wait for map to be ready
   // Map Clicks for Popup & Area Selection
   // Wait for map to be ready using polling
   const checkMapInterval = setInterval(() => {
      console.log('Checking map readiness for AreaSelector...');
      if (window.satelliteMap && window.satelliteMap.map) {
         console.log('Map ready. Initializing AreaSelector and StatsPanel.');
         clearInterval(checkMapInterval);

         window.areaSelector = new AreaSelector(window.satelliteMap.map);
         window.statsPanel = new StatsPanel();

         window.satelliteMap.map.on('click', (e) => {
            // Check if click is on world-gray-layer (outside Slovakia)
            const grayFeatures = window.satelliteMap.map.queryRenderedFeatures(e.point, {
               layers: ['world-gray-layer']
            });

            if (grayFeatures.length > 0) {
               console.log('Clicked outside Slovakia');
               return; // Do nothing
            }

            // If inside Slovakia (didn't hit gray mask)
            // Show popup with REAL info ONLY if not interacting with area selector
            // (AreaSelector handles its own clicks, but we need to make sure we don't show popup when selecting)
            // Simple check: if area selector is active (placing mode), don't show popup
            if (window.areaSelector && window.areaSelector.isActive) return;

            const activeBtn = document.querySelector('.layer-btn.active');
            if (activeBtn) {
               const type = activeBtn.getAttribute('data-layer');
               const scene = window.satelliteLayers?.currentScene;

               let htmlContent = '';

               if (scene) {
                  // Real Data Header
                  const date = new Date(scene.acquisition_date).toLocaleDateString();
                  const clouds = scene.cloud_coverage ? scene.cloud_coverage.toFixed(1) + '%' : 'N/A';
                  const id = scene.product_id || scene.title || 'Unknown ID';

                  // Color for header based on type
                  let color = type === 'ndvi' ? '#41A636' : '#4169E1';

                  htmlContent = `
                            <div style="font-family: sans-serif; padding: 5px; min-width: 200px;">
                                <h4 style="margin: 0 0 8px; border-bottom: 2px solid ${color}; padding-bottom: 3px;">${type.toUpperCase()} Layer</h4>
                                <div style="font-size: 0.9em; line-height: 1.4;">
                                    <p style="margin: 0;"><strong>Date:</strong> ${date}</p>
                                    <p style="margin: 0;"><strong>Clouds:</strong> ${clouds}</p>
                                    <p style="margin: 0;"><strong>Scene ID:</strong> <span style="font-size:0.8em; color:#666;">${id.substring(0, 20)}...</span></p>
                                </div>
                                <p style="margin: 8px 0 0; font-size: 0.8em; color: #999;">
                                Lat: ${e.lngLat.lat.toFixed(4)}, Lng: ${e.lngLat.lng.toFixed(4)}
                                </p>
                            </div>
                        `;
               } else {
                  // No Data State
                  htmlContent = `
                            <div style="font-family: sans-serif; padding: 5px;">
                                <p style="margin: 0; color: #666;">No satellite data loaded for this date.</p>
                            </div>
                        `;
               }

               new maptilersdk.Popup()
                  .setLngLat(e.lngLat)
                  .setHTML(htmlContent)
                  .addTo(window.satelliteMap.map);
            }
         });
      }
   }, 500); // Check every 500ms

   // Area Selection Button Logic is handled in selection.js
}

function toggleFilters() {
   const dropdown = document.querySelector('.filters-dropdown');
   const menuBtn = document.getElementById('menu-btn');
   if (dropdown) dropdown.classList.toggle('active');
   if (menuBtn) menuBtn.classList.toggle('active');
}

function closeFilters() {
   const panel = document.getElementById('filters-panel');
   const menuBtn = document.getElementById('menu-btn');
   panel.classList.remove('active');
   menuBtn.classList.remove('active');
}

function showInfo() {
   const modal = document.getElementById('info-modal');
   if (modal) modal.classList.remove('hidden');
}

function hideInfo() {
   const modal = document.getElementById('info-modal');
   if (modal) modal.classList.add('hidden');
}

function applyFilters() {
   // Placeholder
}
