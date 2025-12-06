# ⚙️ Конфігурація

Повний посібник з налаштування змінних середовища та конфігурації SattelishMaps.

## Файли конфігурації

```
SattelishMaps/
├── .env                    # Головна конфігурація
├── backend/.env            # Backend специфічна конфігурація
└── docker-compose.yml      # Docker конфігурація
```

## Змінні середовища

### Головний файл .env

Створіть файл `.env` в корені проекту:

```bash
cp .env.example .env
```

#### Environment Settings

```env
# Середовище виконання
ENVIRONMENT=development  # development | production | staging
DEBUG=true              # true | false
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR | CRITICAL
```

**Опис:**
- `ENVIRONMENT` - визначає режим роботи
- `DEBUG` - увімкнути детальні логи та Swagger UI
- `LOG_LEVEL` - рівень логування

#### Server Settings

```env
# Налаштування сервера
HOST=0.0.0.0
PORT=8000
```

**Опис:**
- `HOST` - IP адреса для прослуховування (0.0.0.0 = всі інтерфейси)
- `PORT` - порт backend сервера

#### Supabase Configuration

```env
# Supabase налаштування
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Де взяти:**
1. Перейдіть на https://supabase.com/
2. Відкрийте ваш проект
3. Settings → API
4. Скопіюйте:
   - Project URL → `SUPABASE_URL`
   - `anon` `public` → `SUPABASE_ANON_KEY`
   - `service_role` → `SUPABASE_SERVICE_KEY`

> [!WARNING]
> `SUPABASE_SERVICE_KEY` має повний доступ до БД. Ніколи не публікуйте його!

#### Scheduler Configuration

```env
# Налаштування автоматичного scheduler
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=6
DEFAULT_SEARCH_BOUNDS=POLYGON((16 48, 22 48, 22 50, 16 50, 16 48))
DEFAULT_CLOUD_MAX=30.0
PROCESS_HISTORICAL_DATA=false
```

**Опис:**
- `SCHEDULER_ENABLED` - увімкнути/вимкнути автоматичне завантаження даних
- `SCHEDULER_INTERVAL_HOURS` - інтервал між запусками (години)
- `DEFAULT_SEARCH_BOUNDS` - географічна область пошуку (WKT Polygon)
- `DEFAULT_CLOUD_MAX` - максимальна хмарність (0-100%)
- `PROCESS_HISTORICAL_DATA` - завантажити історичні дані при старті

**Приклади регіонів:**

```env
# Словаччина (повністю)
DEFAULT_SEARCH_BOUNDS=POLYGON((16.8 47.7, 22.6 47.7, 22.6 49.6, 16.8 49.6, 16.8 47.7))

# Трнавський край
DEFAULT_SEARCH_BOUNDS=POLYGON((16.8 48.0, 18.2 48.0, 18.2 48.9, 16.8 48.9, 16.8 48.0))

# Братислава
DEFAULT_SEARCH_BOUNDS=POLYGON((16.9 48.0, 17.3 48.0, 17.3 48.3, 16.9 48.3, 16.9 48.0))
```

> [!TIP]
> Використовуйте https://geojson.io/ для створення полігонів

#### CORS Settings

```env
# CORS налаштування (через кому)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://your-domain.com
```

### Backend файл .env

Створіть файл `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

#### Sentinel Hub Credentials

```env
# Sentinel Hub OAuth
SH_CLIENT_ID=your_client_id_here
SH_CLIENT_SECRET=your_client_secret_here
```

**Де взяти:**
1. Зареєструйтеся на https://www.sentinel-hub.com/
2. Dashboard → User Settings → OAuth clients
3. Create new OAuth client
4. Скопіюйте Client ID та Client Secret

> [!IMPORTANT]
> Безкоштовний план дозволяє 30,000 запитів/місяць

## Docker Compose конфігурація

### Порти

За замовчуванням:
- Backend: `8000`
- Frontend: `3000`

Змінити порти в `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Зовнішній:Внутрішній
  
  frontend:
    ports:
      - "3001:80"
```

### Volumes

```yaml
volumes:
  - ./logs:/app/logs              # Логи
  - ./downloads:/app/downloads    # Завантажені файли
  - ./backend:/app                # Код backend (для hot-reload)
```

### Environment Variables Override

Можна перевизначити змінні в `docker-compose.yml`:

```yaml
environment:
  - SCHEDULER_ENABLED=false
  - LOG_LEVEL=DEBUG
```

## Production конфігурація

### Безпека

```env
# Production налаштування
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

### Secrets Management

> [!CAUTION]
> Ніколи не коммітьте `.env` файли в Git!

**Рекомендації:**
1. Використовуйте `.env.example` як шаблон
2. Зберігайте secrets у:
   - Docker Secrets
   - Kubernetes Secrets
   - AWS Secrets Manager
   - HashiCorp Vault

**Приклад з Docker Secrets:**

```yaml
# docker-compose.prod.yml
services:
  backend:
    secrets:
      - supabase_key
      - sentinel_secret

secrets:
  supabase_key:
    external: true
  sentinel_secret:
    external: true
```

### SSL/TLS

Для production додайте nginx з SSL:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

## Перевірка конфігурації

### Перевірити змінні середовища

```bash
# В Docker контейнері
docker-compose exec backend env | grep -E "SUPABASE|SCHEDULER"

# Локально
source .env
echo $SUPABASE_URL
```

### Тест підключення до Supabase

```bash
curl -X GET "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY"
```

### Тест Sentinel Hub

```python
# backend/test_sentinel.py
from services.sentinelhub_service import sentinelhub_service

# Спробувати отримати токен
token = sentinelhub_service._get_access_token()
print(f"Token отримано: {token[:20]}...")
```

## Конфігурація для різних середовищ

### Development

```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=1  # Частіше для тестування
```

### Staging

```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=6
```

### Production

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=6
PROCESS_HISTORICAL_DATA=false
```

## Troubleshooting

### Scheduler не запускається

```bash
# Перевірити логи
docker-compose logs -f backend | grep -i scheduler

# Перевірити змінну
docker-compose exec backend env | grep SCHEDULER_ENABLED
```

### Помилка підключення до Supabase

```bash
# Перевірити URL
curl $SUPABASE_URL/rest/v1/

# Перевірити ключ
echo $SUPABASE_ANON_KEY | wc -c  # Має бути > 100 символів
```

### Sentinel Hub 401 Unauthorized

```bash
# Перевірити credentials
cd backend
python -c "from services.sentinelhub_service import sentinelhub_service; print(sentinelhub_service._get_access_token())"
```

## Наступні кроки

✅ Конфігурація завершена! Тепер:

1. 🚀 Запустіть проект: [Швидкий старт](quick-start.md)
2. 📖 Вивчіть [API документацію](../api/README.md)
3. 🔧 Налаштуйте [Development середовище](../development/README.md)

## Додаткові ресурси

- [Supabase Documentation](https://supabase.com/docs)
- [Sentinel Hub API Docs](https://docs.sentinel-hub.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
