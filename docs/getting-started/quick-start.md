# 🚀 Швидкий старт

Запустіть SattelishMaps за 5 хвилин використовуючи Docker Compose.

## Передумови

- ✅ Docker Desktop встановлено ([завантажити](https://www.docker.com/products/docker-desktop))
- ✅ Docker Compose доступний (зазвичай входить до Docker Desktop)
- ✅ Облікові дані Sentinel Hub ([зареєструватися](https://www.sentinel-hub.com/))
- ✅ Проект Supabase ([створити](https://supabase.com/))

## Крок 1: Клонування репозиторію

```bash
git clone https://github.com/Skriplss/SattelishMaps.git
cd SattelishMaps
```

## Крок 2: Налаштування змінних середовища

### Створити файл .env

```bash
cp .env.example .env
```

### Відредагувати .env

Відкрийте `.env` у текстовому редакторі та заповніть:

```env
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Sentinel Hub (backend/.env)
SH_CLIENT_ID=your_sentinel_hub_client_id
SH_CLIENT_SECRET=your_sentinel_hub_client_secret

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=6
DEFAULT_SEARCH_BOUNDS=POLYGON((16 48, 22 48, 22 50, 16 50, 16 48))
DEFAULT_CLOUD_MAX=30.0
```

### Де взяти credentials?

#### Supabase
1. Перейдіть на [supabase.com](https://supabase.com/)
2. Створіть новий проект
3. Перейдіть в **Settings** → **API**
4. Скопіюйте:
   - `URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_ANON_KEY`
   - `service_role` → `SUPABASE_SERVICE_KEY`

#### Sentinel Hub
1. Зареєструйтеся на [sentinel-hub.com](https://www.sentinel-hub.com/)
2. Створіть OAuth Client в Dashboard
3. Скопіюйте Client ID та Client Secret
4. Додайте їх у `backend/.env`:
   ```bash
   echo 'SH_CLIENT_ID="your_client_id"' > backend/.env
   echo 'SH_CLIENT_SECRET="your_secret"' >> backend/.env
   ```

## Крок 3: Налаштування бази даних

### Створити таблиці в Supabase

1. Відкрийте **SQL Editor** у вашому Supabase проекті
2. Виконайте скрипт з `database/schema.sql`:

```sql
-- Увімкнути PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Таблиця для статистики регіонів
CREATE TABLE IF NOT EXISTS region_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_name TEXT NOT NULL,
    date DATE NOT NULL,
    bbox GEOMETRY(POLYGON, 4326),
    
    -- NDVI статистика
    ndvi_mean DOUBLE PRECISION,
    ndvi_min DOUBLE PRECISION,
    ndvi_max DOUBLE PRECISION,
    ndvi_std DOUBLE PRECISION,
    ndvi_sample_count INTEGER,
    
    -- NDWI статистика
    ndwi_mean DOUBLE PRECISION,
    ndwi_min DOUBLE PRECISION,
    ndwi_max DOUBLE PRECISION,
    ndwi_std DOUBLE PRECISION,
    ndwi_sample_count INTEGER,
    
    -- NDBI статистика
    ndbi_mean DOUBLE PRECISION,
    ndbi_min DOUBLE PRECISION,
    ndbi_max DOUBLE PRECISION,
    
    -- Moisture статистика
    moisture_mean DOUBLE PRECISION,
    moisture_min DOUBLE PRECISION,
    moisture_max DOUBLE PRECISION,
    
    provider TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(region_name, date)
);

-- Індекси для швидкого пошуку
CREATE INDEX idx_region_date ON region_statistics(region_name, date);
CREATE INDEX idx_date ON region_statistics(date);
CREATE INDEX idx_bbox ON region_statistics USING GIST(bbox);
```

## Крок 4: Запуск сервісів

```bash
docker-compose up -d
```

Ця команда:
- 🐳 Завантажить необхідні Docker образи
- 🔨 Побудує backend та frontend контейнери
- 🚀 Запустить сервіси у фоновому режимі

### Перевірка статусу

```bash
# Переглянути запущені контейнери
docker-compose ps

# Переглянути логи
docker-compose logs -f backend
```

## Крок 5: Перевірка роботи

### Backend API

Відкрийте у браузері: http://localhost:8000/docs

Ви побачите Swagger UI з документацією API.

**Тестовий запит:**
```bash
curl http://localhost:8000/health
```

Очікувана відповідь:
```json
{
  "status": "ok",
  "message": "SattelishMaps Backend is running",
  "version": "1.0.0",
  "environment": "development"
}
```

### Frontend

Відкрийте у браузері: http://localhost:3000

Ви побачите інтерактивну карту з фільтрами.

### Scheduler

Перевірте статус автоматичного scheduler:

```bash
curl http://localhost:8000/api/scheduler/status
```

## Крок 6: Перший запит даних

### Отримати статистику для регіону

```bash
curl -X GET "http://localhost:8000/api/statistics/region?region_name=Trnava&date_from=2024-01-01&date_to=2024-12-31"
```

### Отримати дані NDVI

```bash
curl -X GET "http://localhost:8000/api/indices/ndvi?region_name=Trnava&limit=10"
```

## Корисні команди

```bash
# Зупинити сервіси
docker-compose down

# Перезапустити з перебудовою
docker-compose up --build -d

# Переглянути логи конкретного сервісу
docker-compose logs -f backend
docker-compose logs -f frontend

# Увійти в контейнер backend
docker-compose exec backend bash

# Очистити все (включно з volumes)
docker-compose down -v
```

## Наступні кроки

✅ Проект запущено! Тепер ви можете:

1. 📖 Вивчити [API документацію](../api/README.md)
2. 🗺️ Ознайомитися з [Посібником користувача](../guides/using-map.md)
3. 🔧 Налаштувати [Development середовище](../development/README.md)
4. 🏗️ Зрозуміти [Архітектуру системи](../architecture/README.md)

## Проблеми?

Якщо щось не працює:

1. Перевірте логи: `docker-compose logs -f`
2. Перевірте що всі credentials правильні у `.env`
3. Переконайтеся що порти 8000 та 3000 вільні
4. Перегляньте [Troubleshooting Guide](../development/troubleshooting.md)
5. Створіть [GitHub Issue](https://github.com/Skriplss/SattelishMaps/issues)

---

**Вітаємо! 🎉 Ви успішно запустили SattelishMaps!**
