# 🗄️ Supabase Setup Guide

## Что такое Supabase?

Supabase - это open-source альтернатива Firebase. Он дает нам:
- ✅ PostgreSQL база данных (с PostGIS для геоданных)
- ✅ Auto-generated REST API
- ✅ Realtime subscriptions
- ✅ Аутентификация (если понадобится)
- ✅ Storage для файлов
- ✅ Бесплатный тариф для хакатона

## Шаг 1: Создание проекта

1. Зайдите на https://supabase.com
2. Нажмите "Start your project"
3. Войдите через GitHub (быстрее всего)
4. Нажмите "New Project"
5. Заполните:
   - **Name**: `sattelish-maps`
   - **Database Password**: придумайте надежный пароль (сохраните!)
   - **Region**: выберите ближайший (Europe West)
   - **Pricing Plan**: Free
6. Нажмите "Create new project"
7. Подождите 2-3 минуты пока проект создается

## Шаг 2: Получение API ключей

1. В левом меню выберите **Settings** (⚙️)
2. Выберите **API**
3. Скопируйте:
   - **Project URL** (например: `https://abcdefgh.supabase.co`)
   - **anon public** ключ (для frontend)
   - **service_role** ключ (для backend, СЕКРЕТНЫЙ!)

## Шаг 3: Создание таблиц

### Вариант 1: Через SQL Editor (рекомендуется)

1. В левом меню выберите **SQL Editor**
2. Нажмите **New query**
3. Вставьте следующий SQL:

```sql
-- Включаем расширение PostGIS для работы с геоданными
CREATE EXTENSION IF NOT EXISTS postgis;

-- Таблица спутниковых снимков
CREATE TABLE satellite_images (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_id TEXT UNIQUE NOT NULL,
    acquisition_date TIMESTAMP NOT NULL,
    cloud_coverage DECIMAL(5,2),
    location GEOGRAPHY(POINT, 4326),
    bounds GEOGRAPHY(POLYGON, 4326),
    thumbnail_url TEXT,
    download_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица статистики
CREATE TABLE statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    image_id UUID REFERENCES satellite_images(id),
    ndvi_mean DECIMAL(5,4),
    ndvi_std DECIMAL(5,4),
    vegetation_index TEXT,
    change_detection JSONB,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX idx_satellite_date ON satellite_images(acquisition_date);
CREATE INDEX idx_satellite_location ON satellite_images USING GIST(location);
CREATE INDEX idx_satellite_cloud ON satellite_images(cloud_coverage);

-- Включаем Row Level Security (опционально)
ALTER TABLE satellite_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE statistics ENABLE ROW LEVEL SECURITY;

-- Политика: все могут читать (для хакатона)
CREATE POLICY "Public read access" ON satellite_images FOR SELECT USING (true);
CREATE POLICY "Public read access" ON statistics FOR SELECT USING (true);
```

4. Нажмите **Run** (или Ctrl+Enter)
5. Должно появиться "Success. No rows returned"

### Вариант 2: Через Table Editor

1. В левом меню выберите **Table Editor**
2. Нажмите **Create a new table**
3. Создайте таблицы вручную (дольше, но нагляднее)

## Шаг 4: Настройка .env файла

Создайте файл `.env` в корне проекта:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Copernicus
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password

# MapTiler
MAPTILER_API_KEY=your_maptiler_key
```

## Шаг 5: Установка клиента Supabase

### Python (Backend)

```bash
pip install supabase
```

### JavaScript (Frontend)

```html
<!-- Добавьте в index.html -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

## Примеры использования

### Python (Backend)

```python
from supabase import create_client, Client
import os

# Инициализация
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Вставка данных
data = supabase.table('satellite_images').insert({
    "product_id": "S2A_MSIL2A_20231205...",
    "acquisition_date": "2023-12-05T10:30:00",
    "cloud_coverage": 15.5,
    "location": "POINT(14.0 50.0)"
}).execute()

# Получение данных
response = supabase.table('satellite_images')\
    .select("*")\
    .lt('cloud_coverage', 30)\
    .order('acquisition_date', desc=True)\
    .limit(10)\
    .execute()

print(response.data)
```

### JavaScript (Frontend)

```javascript
// Инициализация
const supabaseUrl = 'https://your-project.supabase.co'
const supabaseKey = 'your_anon_key'
const supabase = window.supabase.createClient(supabaseUrl, supabaseKey)

// Получение данных
async function getSatelliteImages() {
    const { data, error } = await supabase
        .from('satellite_images')
        .select('*')
        .lt('cloud_coverage', 30)
        .order('acquisition_date', { ascending: false })
        .limit(10)
    
    if (error) console.error(error)
    else console.log(data)
}

// Realtime подписка (опционально)
const channel = supabase
    .channel('satellite_changes')
    .on('postgres_changes', 
        { event: '*', schema: 'public', table: 'satellite_images' },
        (payload) => {
            console.log('Change received!', payload)
        }
    )
    .subscribe()
```

## Полезные функции

### Поиск по координатам (PostGIS)

```sql
-- Найти все снимки в радиусе 50км от точки
SELECT * FROM satellite_images
WHERE ST_DWithin(
    location,
    ST_GeogFromText('POINT(14.0 50.0)'),
    50000  -- метры
);
```

### Фильтрация по дате и облачности

```python
response = supabase.table('satellite_images')\
    .select("*")\
    .gte('acquisition_date', '2023-01-01')\
    .lte('acquisition_date', '2023-12-31')\
    .lt('cloud_coverage', 20)\
    .execute()
```

## Просмотр данных

1. В левом меню выберите **Table Editor**
2. Выберите таблицу `satellite_images` или `statistics`
3. Можете добавлять/редактировать/удалять данные вручную

## Storage для изображений (опционально)

Если нужно хранить спутниковые снимки:

1. В левом меню выберите **Storage**
2. Нажмите **Create a new bucket**
3. Название: `satellite-images`
4. Public bucket: ✅ (для хакатона)
5. Нажмите **Create bucket**

### Загрузка файла (Python)

```python
with open('image.tif', 'rb') as f:
    supabase.storage.from_('satellite-images').upload(
        'path/to/image.tif',
        f
    )
```

## Мониторинг

1. **Database** → **Tables** - просмотр данных
2. **Database** → **Logs** - логи запросов
3. **Settings** → **API** - документация API

## Лимиты бесплатного тарифа

- ✅ 500 MB database space (достаточно для хакатона)
- ✅ 1 GB file storage
- ✅ 2 GB bandwidth
- ✅ 50,000 monthly active users
- ✅ Unlimited API requests

## Troubleshooting

### Ошибка подключения
- Проверьте что URL и ключи правильные
- Проверьте что проект активен (зеленый индикатор)

### Ошибка "relation does not exist"
- Таблицы не созданы, выполните SQL из Шага 3

### Ошибка "permission denied"
- Проверьте Row Level Security политики
- Для хакатона можете отключить RLS (не рекомендуется для продакшена)

## Полезные ссылки

- [Supabase Documentation](https://supabase.com/docs)
- [Python Client](https://supabase.com/docs/reference/python/introduction)
- [JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [PostGIS Functions](https://postgis.net/docs/reference.html)

---

**Готово! Теперь у вас есть полноценная база данных с API! 🎉**
