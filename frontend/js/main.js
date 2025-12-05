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
      satelliteMap = new SatelliteMap('map', MAPTILER_API_KEY);
      satelliteMap.init();
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
   const mapDate = document.getElementById('map-date');
   if (mapDate) {
      mapDate.addEventListener('change', (e) => {
         console.log('📅 Date changed:', e.target.value);
      });
   }
});

console.log('✅ Loaded');
