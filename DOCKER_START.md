# 🚀 Швидкий запуск через Docker

## Чому Docker?

Docker ізолює всі залежності проекту і не конфліктує з іншими Python пакетами у вашій системі (jupyterlab, langchain, anthropic тощо).

## Передумови

```bash
# Перевірте, що Docker встановлено
docker --version
docker-compose --version
```

Якщо не встановлено: https://docs.docker.com/get-docker/

## Крок 1: Налаштування

```bash
# Перейдіть в директорію проекту
cd /home/dmytro/Repository/V-Axis/Hackaton-MTF-2025/SattelishMaps

# Скопіюйте приклад .env
cp .env.example .env

# Відредагуйте .env та додайте ваші credentials
nano .env
```

**Обов'язково додайте:**
- `SUPABASE_URL` - URL вашого Supabase проекту
- `SUPABASE_SERVICE_KEY` - Service role key з Supabase
- `COPERNICUS_USERNAME` - Ваш логін Copernicus
- `COPERNICUS_PASSWORD` - Ваш пароль Copernicus

## Крок 2: Налаштування бази даних

1. Відкрийте Supabase Dashboard
2. SQL Editor → New Query
3. Скопіюйте вміст `database/schemas/sentinel2_schema.sql`
4. Виконайте SQL скрипт
5. Перевірте, що таблиці створені

## Крок 3: Запуск

```bash
# Збудувати Docker образ
docker-compose build

# Запустити контейнер
docker-compose up -d

# Переглянути логи
docker-compose logs -f backend
```

## Крок 4: Перевірка

```bash
# Перевірити health
curl http://localhost:8000/health

# Перевірити scheduler
curl http://localhost:8000/api/scheduler/status

# Відкрити API документацію
xdg-open http://localhost:8000/docs  # Linux
# або відкрийте в браузері: http://localhost:8000/docs
```

## Корисні команди

```bash
# Переглянути логи
docker-compose logs -f backend

# Фільтрувати логи scheduler
docker-compose logs -f backend | grep scheduler

# Зупинити
docker-compose down

# Перезапустити
docker-compose restart

# Зупинити та видалити контейнери
docker-compose down -v

# Перебудувати після змін в коді
docker-compose up -d --build
```

## Troubleshooting

### Порт 8000 зайнятий

```bash
# Знайти процес
sudo lsof -i :8000

# Або змінити порт в docker-compose.yml
ports:
  - "8001:8000"  # Зовнішній порт 8001
```

### Помилки при build

```bash
# Очистити Docker cache
docker system prune -a

# Перебудувати з нуля
docker-compose build --no-cache
```

### Scheduler не працює

```bash
# Перевірити логи
docker-compose logs backend | grep -i error

# Перевірити .env
docker-compose exec backend env | grep SCHEDULER

# Перезапустити
docker-compose restart backend
```

## Альтернатива: Локальний запуск (якщо потрібно)

Якщо все ж таки хочете запустити локально без Docker:

```bash
# Встановити python3-venv (Ubuntu/Debian)
sudo apt install python3.12-venv

# Створити віртуальне середовище
python3 -m venv .venv

# Активувати
source .venv/bin/activate

# Встановити залежності
pip install -r requirements.txt

# Запустити
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Примітка:** Локальний запуск може мати конфлікти з іншими пакетами (jupyterlab, langchain тощо). Docker рекомендується.

## Наступні кроки

1. ✅ Запустити через Docker
2. ✅ Перевірити scheduler status
3. ✅ Переглянути API docs
4. 🔄 Почекати першого запуску scheduler (або примусово викликати через API)
5. 📊 Перевірити дані в Supabase

## Моніторинг

```bash
# Реал-тайм логи
docker-compose logs -f backend

# Статус scheduler
watch -n 5 'curl -s http://localhost:8000/api/scheduler/status | jq'

# Перевірити дані в Supabase
# Відкрийте Supabase Dashboard → Table Editor → satellite_images
```

Готово! 🎉
