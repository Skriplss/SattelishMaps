# Pixel Data Management

## Обзор

Система позволяет получать сырые значения индексов (NDVI, NDWI, NDBI, MOISTURE) из Sentinel Hub и сохранять их в базу данных с геопозицией каждого пикселя.

## Как это работает

### 1. Запрос к Sentinel Hub

Вместо PNG картинки, мы запрашиваем TIFF файлы с реальными значениями:

```python
# Старый способ (картинка)
response_format = "image/png"  # RGB цвета
output = { bands: 4 }  # RGBA

# Новый способ (сырые данные)
response_format = "image/tiff"  # Float32 значения
output = { bands: 1, sampleType: "FLOAT32" }  # Реальные числа от -1 до 1
```

### 2. Что мы получаем

```json
{
  "values": [
    [0.65, 0.72, 0.68, ...],  // Строка 1
    [0.71, 0.69, 0.73, ...],  // Строка 2
    ...
  ],
  "mask": [
    [1, 1, 1, ...],  // 1 = валидные данные, 0 = облака/нет данных
    [1, 1, 0, ...],
    ...
  ],
  "bbox": [19.5, 48.5, 19.7, 48.7],
  "width": 100,
  "height": 100
}
```

### 3. Сохранение в БД

Для каждого пикселя вычисляем координаты и сохраняем:

```sql
INSERT INTO pixel_data (location, date, ndvi, ndwi, ndbi, moisture)
VALUES (
  ST_Point(19.523, 48.612),  -- Координаты пикселя
  '2024-12-05',
  0.65,  -- NDVI значение
  0.23,  -- NDWI значение
  -0.15, -- NDBI значение
  0.42   -- MOISTURE значение
);
```

## API Endpoints

### POST /api/tiles/fetch-pixels

Загрузить пиксельные данные для области.

**Параметры:**
- `min_lat`, `max_lat`, `min_lon`, `max_lon` - границы области
- `date` - дата в формате YYYY-MM-DD
- `resolution` - размер сетки (по умолчанию 100x100)

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/api/tiles/fetch-pixels?min_lat=48.5&max_lat=48.7&min_lon=19.5&max_lon=19.7&date=2024-12-05&resolution=100"
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "success": true,
    "pixels_stored": 8543,
    "date": "2024-12-05",
    "bbox": [19.5, 48.5, 19.7, 48.7],
    "resolution": "100x100",
    "indices": ["NDVI", "NDWI", "NDBI", "MOISTURE"]
  }
}
```

### GET /api/tiles/area/stats

Получить статистику для выделенной области (использует сохраненные пиксели).

**Параметры:**
- `min_lat`, `max_lat`, `min_lon`, `max_lon` - границы области
- `date` - дата
- `index_type` - тип индекса (NDVI, NDWI, NDBI, MOISTURE)

**Пример:**
```bash
curl "http://localhost:8000/api/tiles/area/stats?min_lat=48.5&max_lat=48.6&min_lon=19.5&max_lon=19.6&date=2024-12-05&index_type=NDVI"
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "mean": 0.6523,
    "min": 0.2145,
    "max": 0.8912,
    "std": 0.1234,
    "pixel_count": 2341,
    "area": {
      "min_lon": 19.5,
      "min_lat": 48.5,
      "max_lon": 19.6,
      "max_lat": 48.6
    }
  }
}
```

### GET /api/tiles/area/timeseries

Агрегаты по дням для выделенной области за период (для графиков).

**Параметры:** `min_lat`, `max_lat`, `min_lon`, `max_lon`, `index_type`, `date_from`, `date_to`

```bash
curl "http://localhost:8000/api/tiles/area/timeseries?min_lat=48.5&max_lat=48.6&min_lon=19.5&max_lon=19.6&index_type=NDVI&date_from=2024-10-01&date_to=2024-12-31"
```

Ответ: массив `{date, mean, min, max, pixel_count}`.

### GET /api/tiles/area/histogram

Распределение значений индекса по корзинам для выделенной области.

**Параметры:** `min_lat`, `max_lat`, `min_lon`, `max_lon`, `date`, `index_type`, `bins` (по умолчанию 20)

```bash
curl "http://localhost:8000/api/tiles/area/histogram?min_lat=48.5&max_lat=48.6&min_lon=19.5&max_lon=19.6&date=2024-12-05&index_type=NDVI&bins=20"
```

Ответ: массив `{range_min, range_max, count}`.

### GET /api/tiles/area/change

Change detection: сравнение значений индекса между двумя датами.

**Параметры:** `min_lat`, `max_lat`, `min_lon`, `max_lon`, `date_a`, `date_b`, `index_type`, `threshold` (по умолчанию 0.05)

```bash
curl "http://localhost:8000/api/tiles/area/change?min_lat=48.5&max_lat=48.6&min_lon=19.5&max_lon=19.6&date_a=2024-11-05&date_b=2024-12-05&index_type=NDVI"
```

Ответ: `{mean_a, mean_b, mean_diff, improved_count, declined_count, stable_count, pixel_count}`.

> Пиксели сопоставляются по точным координатам — загружай обе даты
> с одинаковым bbox и resolution, иначе пары не совпадут.

### GET /api/tiles/pixel/{z}/{x}/{y}.png

Рендер тайла карты **напрямую из pixel_data** — без запроса к Sentinel Hub
и без расхода квоты. Цветовые шкалы совпадают с evalscript'ами. Там, где
пиксельных данных нет, тайл прозрачный.

**Параметры:** `date`, `index_type`

```bash
curl "http://localhost:8000/api/tiles/pixel/12/2280/1420.png?date=2024-12-05&index_type=NDVI" -o tile.png
```

Чтобы карта фронтенда использовала пиксельный рендер в горячем пути
(`/wms/tile` сначала пробует pixel_data, потом Sentinel Hub), включи
`PREFER_PIXEL_TILES=true` в `.env`. Учитывай: при зумах глубже разрешения
загруженной сетки тайлы будут «пиксельными» (nearest-neighbor).

## Использование через скрипт

```bash
# Перейти в директорию backend
cd backend

# Загрузить данные для области
python -m scripts.fetch_pixel_data \
  --bbox "19.5,48.5,19.7,48.7" \
  --date "2024-12-05" \
  --resolution 100
```

## Workflow

### 1. Первоначальная загрузка данных

```bash
# Загрузить данные для всей Словакии (можно разбить на регионы)
python -m scripts.fetch_pixel_data \
  --bbox "16.8,47.7,22.6,49.6" \
  --date "2024-12-05" \
  --resolution 200
```

### 2. Использование в приложении

Когда пользователь выделяет область на карте:

1. Frontend отправляет запрос к `/api/tiles/area/stats`
2. Backend ищет пиксели в этой области в БД
3. Если данных нет - можно автоматически загрузить через `/api/tiles/fetch-pixels`
4. Возвращает статистику и показывает график

### 3. Автоматическое обновление

Можно добавить в scheduler регулярную загрузку данных:

```python
# В scheduler.py
@scheduler.scheduled_job('cron', hour=2, minute=0)
async def fetch_daily_pixels():
    """Загружать пиксельные данные каждый день в 2:00"""
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    # Загрузить для всех регионов
    for region in REGIONS:
        await tile_cache_service.fetch_and_store_pixel_data(
            min_lon=region['min_lon'],
            min_lat=region['min_lat'],
            max_lon=region['max_lon'],
            max_lat=region['max_lat'],
            date=today,
            resolution=100
        )
```

## Оптимизация

### Resolution (разрешение)

- `resolution=50` - быстро, но низкая точность (2500 пикселей)
- `resolution=100` - баланс (10000 пикселей) ✅ рекомендуется
- `resolution=200` - высокая точность, медленно (40000 пикселей)
- `resolution=500` - максимум (250000 пикселей)

### Batch Processing

Для больших областей лучше разбить на части:

```python
# Вместо одного большого запроса
bbox = [16.8, 47.7, 22.6, 49.6]  # Вся Словакия

# Разбить на сетку 4x4
for lat in range(4):
    for lon in range(4):
        sub_bbox = calculate_sub_bbox(bbox, lat, lon, 4, 4)
        await fetch_and_store_pixel_data(*sub_bbox, date, resolution=100)
```

## Структура БД

Актуальная схема — в `database/schemas/init.sql`. Ключевые моменты:

```sql
-- Таблица pixel_data: партиционирована по месяцам
CREATE TABLE pixel_data (
    date        DATE NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    lat         DOUBLE PRECISION NOT NULL,
    ndvi        REAL,   -- -1.0 до 1.0
    ndwi        REAL,
    ndbi        REAL,
    moisture    REAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    geom        GEOMETRY(POINT, 4326) GENERATED ALWAYS AS
                    (ST_SetSRID(ST_MakePoint(lon, lat), 4326)) STORED,
    PRIMARY KEY (date, lon, lat)
) PARTITION BY RANGE (date);

-- GIST-индекс объявлен на родителе и наследуется всеми партициями
CREATE INDEX idx_pixel_data_geom ON pixel_data USING GIST (geom);
```

Партиции создаются автоматически: перед вставкой бэкенд вызывает RPC
`ensure_pixel_data_partition(date)`. Запросы по области используют
партиционный прунинг по `date` + GIST по `geom`.

Дополнительные RPC для анализа:
- `get_area_pixel_stats(...)` — mean/min/max/std/**median**/count по bbox и дате
- `get_area_pixel_timeseries(...)` — агрегаты по дням за период (для графиков)
- `get_area_pixel_histogram(...)` — распределение значений по корзинам

## Troubleshooting

### Ошибка: "No valid pixel data found"

Возможные причины:
- Слишком много облаков в выбранную дату
- Нет данных Sentinel-2 для этой области/даты
- Попробуйте другую дату или увеличьте `maxCloudCoverage`

### Медленная загрузка

- Уменьшите `resolution`
- Разбейте область на меньшие части
- Проверьте лимиты Sentinel Hub API

### Ошибка памяти

- Уменьшите `resolution`
- Уменьшите размер области
- Увеличьте `batch_size` в коде (по умолчанию 1000)
