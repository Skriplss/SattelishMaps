# Database

Единственный источник правды по схеме — `schemas/init.sql`.

## Создание новой базы (Supabase)

1. Зайди на [supabase.com/dashboard](https://supabase.com/dashboard) → **New project**.
   Выбери регион поближе (eu-central), задай пароль БД.
2. Дождись создания проекта, открой **SQL Editor**.
3. Вставь содержимое `database/schemas/init.sql` целиком и нажми **Run**.
4. Открой **Project Settings → API** и перепиши в корневой `.env`:
   - `SUPABASE_URL` — Project URL
   - `SUPABASE_ANON_KEY` — anon public key
   - `SUPABASE_SERVICE_KEY` — service_role key (секрет!)
5. Перезапусти бэкенд.

Альтернатива через psql (connection string из Project Settings → Database):

```bash
psql "postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres" \
  -v ON_ERROR_STOP=1 -f database/schemas/init.sql
```

## Что внутри

| Таблица | Назначение | Масштабирование |
|---|---|---|
| `region_statistics` | Агрегированная статистика: одна строка на регион+дату+индекс («длинный» формат) | UNIQUE(region, date, index), составные btree-индексы |
| `pixel_data` | Сырые значения индексов по пикселям | Партиционирована по месяцам; PK (date, lon, lat); GIST по генерируемой geometry-колонке |
| `tile_cache` | Отрендеренные PNG-тайлы (base64) | Составной PK (z,x,y,date,index); `cleanup_tile_cache()` для эвикции |

RPC-функции: `get_area_pixel_stats` (+медиана), `get_area_pixel_timeseries`,
`get_area_pixel_histogram`, `get_area_pixel_change` (change detection),
`get_pixel_grid` (сетка значений для рендера тайлов), `get_region_stats_geojson`,
`get_cached_tile`, `ensure_pixel_data_partition`, `cleanup_tile_cache`.

RLS включён на всех таблицах **без** публичных политик: весь доступ идёт через
бэкенд с service_role-ключом. Если понадобится читать из фронтенда напрямую —
добавь SELECT-политики.

## Обслуживание

Периодически чисти кэш тайлов (например, из бэкенда или через pg_cron):

```sql
SELECT cleanup_tile_cache(30); -- удалить тайлы, не читавшиеся 30 дней
```
