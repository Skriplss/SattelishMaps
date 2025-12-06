/* main.js */

// Global state
const MAPTILER_API_KEY = 'zCLzX9B3EgED7gCQmdAo'; // TODO: Replace with your API key
let currentLang = 'SK'; // 'SK' or 'EN'

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
});

function initApp() {
   console.log('🚀 SattelishMaps');

   try {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      satelliteMap = new SatelliteMap('map', MAPTILER_API_KEY);
      satelliteMap.init(currentTheme);

      // Инициализация менеджера слоев
      window.satelliteLayers = new SatelliteLayers(satelliteMap.map);

      // Загружаем тестовые данные после загрузки карты
      // satelliteMap.map.on('load', async () => {
      //    console.log('📡 Loading initial satellite data...');
      //    try {
      //       // Имитируем поиск для текущей области
      //       const bounds = satelliteMap.getBounds();
      //       const data = await SatelliteAPI.fetchSatelliteData(bounds);

      //       if (data && data.length > 0) {
      //          const scene = data[0]; // Берем первый снимок
      //          console.log('📸 Displaying scene:', scene.id);

      //          // Добавляем слой RGB (Sentinel-2) c ID 'current-scene'
      //          // Но не показываем его сразу, чтобы карта была чистой
      //          // (пользователь сам включит NDVI/NDWI)
      //       }
      //    } catch (e) {
      //       console.error('Error loading satellite layers:', e);
      //    }
      // });

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

   // Language Toggle
   const langBtn = document.getElementById('lang-btn');
   if (langBtn) {
      langBtn.addEventListener('click', toggleLanguage);
   }

   // Theme Toggle
   const themeBtn = document.getElementById('theme-btn');
   if (themeBtn) {
      themeBtn.addEventListener('click', () => {
         const newTheme = satelliteMap.toggleTheme();
         // Update icon if needed
         const icon = themeBtn.querySelector('.icon');
         if (icon) icon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
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

   // Layer Toggles - using the specific logic from before
   const layerBtns = document.querySelectorAll('.layer-btn');
   layerBtns.forEach(btn => {
      btn.addEventListener('click', async (e) => {
         const isAlreadyActive = e.target.classList.contains('active');

         // 1. Deactivate all buttons first
         layerBtns.forEach(b => b.classList.remove('active'));

         // 2. If it was NOT active, activate it and show layer
         if (!isAlreadyActive) {
            e.target.classList.add('active');

            const layerType = e.target.getAttribute('data-layer'); // 'ndvi' or 'ndwi'
            console.log('Layer selected:', layerType);

            if (window.satelliteLayers) {
               await window.satelliteLayers.showLayer(layerType);

               const legendContainer = document.getElementById('legend-container');
               if (legendContainer) {
                  legendContainer.classList.remove('hidden');
                  legendContainer.innerHTML = window.satelliteLayers.getLegendHTML(layerType);
               }
            }
         } else {
            // 3. If it WAS active, we just deactivated it above (toggle off)
            console.log('Layer de-selected');
            if (window.satelliteLayers) {
               window.satelliteLayers.clearAll(); // Remove layer
            }
            const legendContainer = document.getElementById('legend-container');
            if (legendContainer) {
               legendContainer.classList.add('hidden'); // Hide legend
            }
         }
      });
   });

   // Map Clicks for Popup
   const mapContainer = document.getElementById('map');
   // Assuming map instance is global or accessible via satelliteMap.map
   // But we need to wait for map init. It's done in initApp.
   // We can attach listener to map object if available, or wait.
   // Ideally properly structured code would handle this inside Map class or here after init.
   // For now, let's assume satelliteMap.map is available after a slight delay or we attach it inside initApp.
   // Actually, better to attach it here if satelliteMap is global.
   // Map Clicks for Popup
   if (window.satelliteMap && window.satelliteMap.map) {
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
         // Show popup with REAL info
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
}

function toggleFilters() {
   const panel = document.getElementById('filters-panel');
   const menuBtn = document.getElementById('menu-btn');
   panel.classList.toggle('active');
   menuBtn.classList.toggle('active');
}

function closeFilters() {
   const panel = document.getElementById('filters-panel');
   const menuBtn = document.getElementById('menu-btn');
   panel.classList.remove('active');
   menuBtn.classList.remove('active');
}

// ============================================
// LANGUAGE TOGGLE
// ============================================
function toggleLanguage() {
   currentLang = currentLang === 'SK' ? 'EN' : 'SK';

   const flagSK = "assets/images/sk-flag.png";
   const flagGB = "data:image/png;base64,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";

   const label = document.getElementById('lang-label');
   const flag = document.querySelector('.lang-flag');

   if (flag) {
      // Flag icon (Left) -> Image
      let img = flag.querySelector('img');
      if (!img) {
         img = document.createElement('img');
         img.style.height = '20px';
         flag.textContent = '';
         flag.appendChild(img);
      }
      img.src = currentLang === 'SK' ? flagSK : flagGB;
   }

   if (label) {
      // Label (Right) -> Text
      label.textContent = currentLang === 'SK' ? 'SK' : 'ENG';
   }

   console.log('Language:', currentLang);
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
   const dateFrom = document.getElementById('date-from').value;
   const dateTo = document.getElementById('date-to').value;

   console.log('Applying filters:', { dateFrom, dateTo });

   // In real app, we would fetch new data here
   const bounds = window.satelliteMap.getBounds();
   console.log('Current Map Bounds:', bounds);

   // Simulate refresh
   const activeLayerBtn = document.querySelector('.layer-btn.active');
   if (activeLayerBtn && window.satelliteLayers) {
      const layerType = activeLayerBtn.getAttribute('data-layer');
      window.satelliteLayers.showLayer(layerType);
   }
}
