/*
   MAIN APP - Custom Layout
   Left sidebar + filters toggle + map
*/

const MAPTILER_API_KEY = 'zCLzX9B3EgED7gCQmdAo';
let satelliteMap = null;
let currentLang = 'SK';

// ============================================
// THEME
// ============================================
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

function updateThemeIcon(theme) {
   const icon = document.querySelector('.theme-icon');
   if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

updateThemeIcon(savedTheme);

// ============================================
// DATE/TIME DISPLAY
// ============================================
function updateSidebarDate() {
   const dateEl = document.getElementById('sidebar-date');
   if (dateEl) {
      const now = new Date();
      const formatted = now.toLocaleString('sk-SK', {
         day: '2-digit',
         month: '2-digit',
         year: 'numeric',
         hour: '2-digit',
         minute: '2-digit'
      });
      dateEl.textContent = formatted;
   }
}

// ============================================
// FILTERS PANEL
// ============================================
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
   const label = document.getElementById('lang-label');
   const flag = document.querySelector('.lang-flag');

   if (label) label.textContent = currentLang;
   if (flag) {
      flag.textContent = currentLang === 'SK' ? '🇸🇰' : '🇬🇧';
   }

   console.log('Language:', currentLang);
}

// ============================================
// INFO MODAL
// ============================================
function showInfo() {
   const modal = document.getElementById('info-modal');
   if (modal) modal.classList.remove('hidden');
}

function hideInfo() {
   const modal = document.getElementById('info-modal');
   if (modal) modal.classList.add('hidden');
}

// ============================================
// MAP INIT
// ============================================
function initApp() {
   console.log('🚀 SattelishMaps');

   try {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      satelliteMap = new SatelliteMap('map', MAPTILER_API_KEY);
      satelliteMap.init(currentTheme);

      // Инициализация менеджера слоев
      window.satelliteLayers = new SatelliteLayers(satelliteMap.map);

      // Загружаем тестовые данные после загрузки карты
      satelliteMap.map.on('load', async () => {
         console.log('📡 Loading initial satellite data...');
         try {
            // Имитируем поиск для текущей области
            const bounds = satelliteMap.getBounds();
            const data = await SatelliteAPI.fetchSatelliteData(bounds);

            if (data && data.length > 0) {
               const scene = data[0]; // Берем первый снимок
               console.log('📸 Displaying scene:', scene.id);

               // Добавляем слой RGB (Sentinel-2) c ID 'current-scene'
               // Но не показываем его сразу, чтобы карта была чистой
               // (пользователь сам включит NDVI/NDWI)
            }
         } catch (e) {
            console.error('Error loading satellite layers:', e);
         }
      });

      // CLICK EVENT FOR POPUP
      satelliteMap.map.on('click', (e) => {
         // Check if any satellite layer is active
         const activeBtn = document.querySelector('.layer-btn.active');
         if (!activeBtn) return;

         // Check if clicked inside Slovakia
         // Strategy: 'world-gray-layer' covers the whole world EXCEPT Slovakia (it's a hole).
         // So if we hit 'world-gray-layer', we are OUTSIDE.
         const outsideFeatures = satelliteMap.map.queryRenderedFeatures(e.point, {
            layers: ['world-gray-layer']
         });

         if (outsideFeatures.length > 0) {
            console.log('📍 Clicked outside Slovakia (world-gray-layer hit), ignoring.');
            return;
         }

         const layerType = activeBtn.dataset.layer; // 'ndvi' or 'ndwi'
         const { lng, lat } = e.lngLat;

         // Mock value generation based on layer type
         let value, color, description;

         if (layerType === 'ndvi') {
            // Generate random NDVI between -0.2 and 0.8
            value = (Math.random() * 1.0 - 0.2).toFixed(2);

            if (value < 0) { color = '#D73027'; description = 'Вода/Асфальт'; }
            else if (value < 0.2) { color = '#FC8D59'; description = 'Голий ґрунт'; }
            else if (value < 0.4) { color = '#FEE090'; description = 'Рідка зелень'; }
            else if (value < 0.6) { color = '#41A636'; description = 'Помірна зелень'; }
            else { color = '#168043'; description = 'Густий ліс'; }
         } else if (layerType === 'ndwi') {
            // Generate random NDWI between -0.3 and 0.8
            value = (Math.random() * 1.1 - 0.3).toFixed(2);

            if (value < 0) { color = '#00005C'; description = 'Сухий ґрунт'; }
            else if (value < 0.2) { color = '#0000CD'; description = 'Помірна волога'; }
            else if (value < 0.5) { color = '#4169E1'; description = 'Вологий ґрунт'; }
            else { color = '#87CEEB'; description = 'Вода'; }
         }

         if (value) {
            new maptilersdk.Popup()
               .setLngLat([lng, lat])
               .setHTML(`
                      <div style="text-align: center;">
                          <div style="font-weight: bold; margin-bottom: 4px;">${layerType.toUpperCase()}</div>
                          <div style="font-size: 1.2rem; font-weight: 800; color: ${color};">${value}</div>
                          <div style="font-size: 0.85rem; opacity: 0.8;">${description}</div>
                      </div>
                  `)
               .addTo(satelliteMap.map);
         }
      });

      console.log('✅ Ready');
      window.map = satelliteMap;
   } catch (error) {
      console.error('❌', error);
   }
}

// ============================================
// EVENTS
// ============================================
document.addEventListener('DOMContentLoaded', () => {
   console.log('📄 Loading...');

   initApp();
   updateSidebarDate();
   setInterval(updateSidebarDate, 60000);

   // Menu button (toggle filters)
   const menuBtn = document.getElementById('menu-btn');
   if (menuBtn) {
      menuBtn.addEventListener('click', toggleFilters);
   }

   // Language toggle
   const langBtn = document.getElementById('lang-btn');
   if (langBtn) {
      langBtn.addEventListener('click', toggleLanguage);
   }

   // Theme toggle
   const themeBtn = document.getElementById('theme-btn');
   if (themeBtn) {
      themeBtn.addEventListener('click', () => {
         const current = document.documentElement.getAttribute('data-theme');
         const newTheme = current === 'dark' ? 'light' : 'dark';
         document.documentElement.setAttribute('data-theme', newTheme);
         localStorage.setItem('theme', newTheme);
         updateThemeIcon(newTheme);

         // Меняем стиль карты
         if (satelliteMap) {
            satelliteMap.setMapStyle(newTheme);
         }
      });
   }

   // Info button
   const infoBtn = document.getElementById('info-btn');
   if (infoBtn) {
      infoBtn.addEventListener('click', showInfo);
   }

   // Close info modal
   const closeInfo = document.getElementById('close-info');
   if (closeInfo) {
      closeInfo.addEventListener('click', hideInfo);
   }

   // Cloud slider
   const cloudSlider = document.getElementById('cloud-slider');
   const cloudValue = document.getElementById('cloud-value');
   if (cloudSlider && cloudValue) {
      cloudSlider.addEventListener('input', (e) => {
         cloudValue.textContent = e.target.value + '%';
      });
   }

   // Date controls
   const dateFrom = document.getElementById('date-from');
   const dateTo = document.getElementById('date-to');

   // Helper to refresh data when filters change
   async function applyFilters() {
      console.log('📅 Date filter changed');
      const fromDate = dateFrom ? dateFrom.value : null;
      const toDate = dateTo ? dateTo.value : null;

      console.log(`  Range: ${fromDate} -> ${toDate}`);

      if (window.satelliteMap) {
         const bounds = window.satelliteMap.getBounds();
         // Call API with new dates
         await SatelliteAPI.fetchSatelliteData(bounds, { from: fromDate, to: toDate });

         // If a layer is currently active, "refresh" it to simulate new data
         const activeBtn = document.querySelector('.layer-btn.active');
         if (activeBtn) {
            console.log('🔄 Re-applying filter request for new date...');
            // In a real app, we would get a NEW tile URL here.
            // For now, we just log that we requested data for the specific date.
         }
      }
   }

   [dateFrom, dateTo].forEach(input => {
      if (input) {
         input.addEventListener('change', applyFilters);
      }
   });

   // Top header date (optional sync)
   const mapDate = document.getElementById('map-date');
   if (mapDate) {
      mapDate.addEventListener('change', (e) => {
         console.log('📅 Header Date changed:', e.target.value);
      });
   }

   // ===================================
   // LEGEND DATA
   // ===================================
   const LEGENDS = {
      ndvi: {
         title: 'NDVI (Vegetation Index)',
         items: [
            { color: '#D73027', label: '< 0: Вода, асфальт' },
            { color: '#FC8D59', label: '0 – 0.2: Голий ґрунт, забудова' },
            { color: '#FEE090', label: '0.2 – 0.4: Рідка рослинність' },
            { color: '#41A636', label: '0.4 – 0.6: Помірна рослинність' },
            { color: '#168043', label: '> 0.6: Густий ліс, парки' }
         ]
      },
      ndwi: {
         title: 'NDWI (Water Index)',
         items: [
            { color: '#00005C', label: '< 0: Сухий ґрунт' },
            { color: '#0000CD', label: '0 – 0.2: Помірна вологість' },
            { color: '#4169E1', label: '0.2 – 0.5: Вологий ґрунт' },
            { color: '#87CEEB', label: '> 0.5: Вода (озера, річки)' }
         ]
      }
   };

   function updateLegend(layerType) {
      const container = document.getElementById('legend-container');
      if (!container) return;

      if (!layerType || !LEGENDS[layerType]) {
         container.classList.add('hidden');
         return;
      }

      const data = LEGENDS[layerType];
      let html = `<div class="legend-title">${data.title}</div>`;

      data.items.forEach(item => {
         html += `
               <div class="legend-item">
                   <div class="legend-color" style="background: ${item.color}"></div>
                   <div class="legend-label">${item.label}</div>
               </div>
           `;
      });

      container.innerHTML = html;
      container.classList.remove('hidden');
   }

   // ===================================
   // LAYER SWITCHING (NDVI / NDWI)
   // ===================================
   const layerBtns = document.querySelectorAll('.layer-btn');

   layerBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
         const layerType = btn.dataset.layer; // 'ndvi' or 'ndwi'
         const isActive = btn.classList.contains('active');

         // 1. UI Update
         // Сбрасываем все кнопки
         layerBtns.forEach(b => b.classList.remove('active'));

         if (isActive) {
            // Если фильтр был активен - выключаем его (возврат к обычному виду)
            console.log('🔄 Filter disabled, returning to normal view');
            updateLegend(null); // Hide legend

            if (window.satelliteLayers) {
               window.satelliteLayers.removeLayer('current-scene');
            }
         } else {
            // Если фильтр не был активен - включаем его
            btn.classList.add('active');
            console.log('🔄 Enabling filter:', layerType);
            updateLegend(layerType); // Show legend

            // 2. Map Update
            if (window.satelliteLayers && window.satelliteMap) {
               try {
                  const bounds = window.satelliteMap.getBounds();
                  const data = await SatelliteAPI.fetchSatelliteData(bounds);

                  if (data && data.length > 0) {
                     const scene = data[0];
                     const url = scene.bands[layerType];

                     if (url) {
                        window.satelliteLayers.addRasterLayer(
                           'current-scene',
                           url,
                           { opacity: 0.8 } // Default opacity
                        );
                        console.log('✅ Filter ' + layerType + ' applied');
                     }
                  }
               } catch (e) {
                  console.error('❌ Error applying filter:', e);
               }
            }
         }
      });
   });
});

console.log('✅ Loaded verified 6 (Legend Added)');
