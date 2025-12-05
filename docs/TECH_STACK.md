# 🛠 Технический стек проекта

## Frontend

### Карты
- **MapTiler** - https://www.maptiler.com
  - Современная библиотека для работы с картами
  - Поддержка спутниковых слоев
  - Хорошая производительность
  - API ключ нужно получить на сайте (бесплатный тариф доступен)

### Основные технологии
- **HTML5** - структура страницы
- **CSS3** - стилизация
- **JavaScript (ES6+)** - логика приложения
- **MapTiler SDK** - визуализация карт

### Дополнительные библиотеки
- **Chart.js** - графики и диаграммы для статистики
- **Axios** - HTTP запросы к backend

## Backend

### Основной стек
- **Python 3.10+**
- **Flask** или **FastAPI** - веб-фреймворк
- **sentinelsat** - библиотека для работы с Copernicus API

### База данных
- **Supabase** - Backend-as-a-Service
  - PostgreSQL база данных
  - Встроенная аутентификация
  - Realtime subscriptions
  - Storage для файлов
  - Auto-generated REST API

### Обработка данных
- **NumPy** - математические операции
- **Pandas** - работа с табличными данными
- **Rasterio** - обработка растровых изображений (спутниковые снимки)

## API и сервисы

### Copernicus Open Access Hub
- **URL**: https://scihub.copernicus.eu/dhus
- **Данные**: Sentinel-2.5 спутниковые снимки
- **Аутентификация**: Нужна регистрация для получения логина/пароля
- **Формат данных**: GeoTIFF, JPEG2000

### MapTiler
- **URL**: https://www.maptiler.com
- **API Key**: Получить на сайте (Free tier: 100,000 запросов/месяц)
- **Документация**: https://docs.maptiler.com/

## Структура данных

### Спутниковые снимки
```json
{
  "id": "S2A_MSIL2A_20231205...",
  "date": "2023-12-05",
  "coordinates": {
    "lat": 50.0,
    "lng": 14.0
  },
  "cloud_coverage": 15.5,
  "bands": {
    "red": "B04",
    "green": "B03",
    "blue": "B02",
    "nir": "B08"
  }
}
```

### Статистика
```json
{
  "area_id": "region_001",
  "ndvi_mean": 0.65,
  "ndvi_std": 0.12,
  "vegetation_index": "healthy",
  "change_detection": {
    "previous_month": -0.05,
    "trend": "decreasing"
  }
}
```

## Инструменты разработки

### Обязательно
- **Git** - система контроля версий
- **Python 3.10+** - для backend
- **Node.js** (опционально) - для сборки frontend
- **PostgreSQL** или **MongoDB** - база данных

### Рекомендуется
- **VS Code** - редактор кода
- **Postman** - тестирование API
- **Docker** - контейнеризация (если успеем)

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Copernicus API
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password

# MapTiler
MAPTILER_API_KEY=your_api_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here
```

## Полезные команды

### Backend
```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
python app.py
```

### Frontend
```bash
# Простой HTTP сервер для разработки
python -m http.server 8000

# Или с Node.js
npx http-server -p 8000
```

## Ссылки на документацию

- [MapTiler SDK](https://docs.maptiler.com/sdk-js/)
- [Copernicus API](https://scihub.copernicus.eu/userguide/)
- [sentinelsat](https://sentinelsat.readthedocs.io/)
- [Flask](https://flask.palletsprojects.com/)
- [PostgreSQL + PostGIS](https://postgis.net/documentation/)
- [Chart.js](https://www.chartjs.org/docs/)
