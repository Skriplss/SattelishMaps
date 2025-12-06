/*
   API MODULE - Denis's satellite data API
   
   ЧТО ТАКОЕ API?
   API (Application Programming Interface) - это способ общения между программами.
   В нашем случае - это способ получить данные от сервера (backend).
   
   ЧТО ТАКОЕ MOCK-ДАННЫЕ?
   Mock (фейковые) данные - это тестовые данные, которые имитируют реальные.
   Мы используем их пока backend не готов.
   
   КАК ЭТО РАБОТАЕТ?
   1. Карта запрашивает данные: "Дай мне спутниковые снимки для этой области"
   2. API возвращает данные (пока mock, потом будет от сервера)
   3. Карта отображает эти данные
*/

// ============================================
// КОНФИГУРАЦИЯ
// ============================================

// URL backend API (пока не используется, но будет нужен позже)
const API_BASE_URL = 'http://localhost:5000/api';

// Используем ли mock-данные (true = да, false = реальный API)
const USE_MOCK_DATA = true;

const MOCK_SATELLITE_DATA = [
    {
        id: 'S2B_MSIL2A_20231030_T34UDV',
        date: '2023-10-30',
        cloudCoverage: 12.5,
        platform: 'Sentinel-2',
        previewUrl: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        coordinates: { lat: 48.1486, lng: 17.1077 },
        bands: {
            rgb: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            nir: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            ndvi: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            ndwi: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        }
    }
];
const MOCK_STATISTICS = {
    averageNO2: 0.00015,
    averageCO: 0.032,
    airQualityIndex: 'Good', // Индекс качества воздуха
    lastUpdate: '2024-12-05',
    maxConcentration: {
        pollutant: 'NO2',
        value: 0.00045,
        location: 'Bratislava'
    }
};

// ============================================
// API ФУНКЦИИ
// ============================================

/*
   ФУНКЦИЯ: fetchSatelliteData
   
   Что делает: Получает спутниковые данные для заданной области и даты
   
   Параметры:
   - bounds: границы области {north, south, east, west}
   - dateRange: диапазон дат {from: '2024-01-01', to: '2024-12-31'}
   - maxCloudCoverage: максимальная облачность (0-100)
   
   Возвращает: Promise с массивом спутниковых данных
   
   Что такое Promise?
   - Это "обещание" что данные придут в будущем
   - Используется для асинхронных операций (когда нужно подождать)
   - Используем await чтобы дождаться результата
*/
async function fetchSatelliteData(bounds, dateRange = {}, maxCloudCoverage = 100) {
    console.log('📡 Fetching satellite data...');
    console.log('  Bounds:', bounds);
    console.log('  Date range:', dateRange);
    console.log('  Max cloud coverage:', maxCloudCoverage);

    if (USE_MOCK_DATA) {
        // Имитируем задержку сети (как будто данные идут от сервера)
        await delay(1000); // Ждем 1 секунду

        // Фильтруем mock-данные по облачности
        const filtered = MOCK_SATELLITE_DATA.filter(
            item => item.cloudCoverage <= maxCloudCoverage
        );

        console.log(`✅ Found ${filtered.length} satellite images`);
        return filtered;
    } else {
        // Реальный запрос к backend (когда будет готов)
        try {
            const response = await fetch(`${API_BASE_URL}/satellite-data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    bounds,
                    dateRange,
                    maxCloudCoverage
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Received data from backend:', data);
            return data;
        } catch (error) {
            console.error('❌ Error fetching satellite data:', error);
            throw error;
        }
    }
}

/*
   ФУНКЦИЯ: fetchStatistics
   
   Что делает: Получает статистику для заданной области
   
   Параметры:
   - bounds: границы области
   
   Возвращает: Promise с объектом статистики
*/
async function fetchStatistics(bounds) {
    console.log('📊 Fetching statistics...');
    console.log('  Bounds:', bounds);

    if (USE_MOCK_DATA) {
        await delay(500);
        console.log('✅ Statistics ready');
        return MOCK_STATISTICS;
    } else {
        try {
            const response = await fetch(`${API_BASE_URL}/statistics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ bounds })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Received statistics from backend:', data);
            return data;
        } catch (error) {
            console.error('❌ Error fetching statistics:', error);
            throw error;
        }
    }
}

/*
   ФУНКЦИЯ: searchByCoordinates
   
   Что делает: Ищет спутниковые данные для конкретной точки
   
   Параметры:
   - lat: широта
   - lng: долгота
   - radius: радиус поиска в км (по умолчанию 10км)
   
   Возвращает: Promise с массивом данных
*/
async function searchByCoordinates(lat, lng, radius = 10) {
    console.log(`🔍 Searching near coordinates: ${lat}, ${lng} (radius: ${radius}km)`);

    if (USE_MOCK_DATA) {
        await delay(800);

        // Простая фильтрация по расстоянию (упрощенная)
        const filtered = MOCK_SATELLITE_DATA.filter(item => {
            const distance = calculateDistance(
                lat, lng,
                item.coordinates.lat, item.coordinates.lng
            );
            return distance <= radius;
        });

        console.log(`✅ Found ${filtered.length} images near location`);
        return filtered;
    } else {
        try {
            const response = await fetch(`${API_BASE_URL}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lat, lng, radius })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('❌ Error searching by coordinates:', error);
            throw error;
        }
    }
}

// ============================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ============================================

/*
   ФУНКЦИЯ: delay
   
   Что делает: Создает задержку (имитирует ожидание ответа от сервера)
   
   Параметры:
   - ms: миллисекунды задержки
   
   Возвращает: Promise который разрешается через указанное время
*/
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/*
   ФУНКЦИЯ: calculateDistance
   
   Что делает: Вычисляет расстояние между двумя точками на Земле
   
   Использует формулу Haversine (стандартная формула для расчета расстояний на сфере)
   
   Параметры:
   - lat1, lng1: координаты первой точки
   - lat2, lng2: координаты второй точки
   
   Возвращает: расстояние в километрах
*/
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Радиус Земли в км
    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);

    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;

    return distance;
}

/*
   ФУНКЦИЯ: toRad
   
   Что делает: Конвертирует градусы в радианы
   (нужно для математических функций)
*/
function toRad(degrees) {
    return degrees * (Math.PI / 180);
}

// ============================================
// ЭКСПОРТ (делаем функции доступными для других файлов)
// ============================================

// Для использования в других файлах:
// const api = SatelliteAPI;
// const data = await api.fetchSatelliteData(bounds);

const SatelliteAPI = {
    fetchSatelliteData,
    fetchStatistics,
    searchByCoordinates,
    USE_MOCK_DATA,
    MOCK_SATELLITE_DATA,
    MOCK_STATISTICS
};

// Делаем доступным глобально для тестирования в консоли
window.SatelliteAPI = SatelliteAPI;

console.log('✅ API module loaded');
console.log('💡 Try in console: await SatelliteAPI.fetchSatelliteData({})');
