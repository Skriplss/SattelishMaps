# SattelishMaps 🛰️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

**SattelishMaps** - це система для автоматичного отримання та аналізу супутникових знімків Sentinel-2 з розрахунком екологічних індексів (NDVI, NDWI, NDBI, вологість) для моніторингу навколишнього середовища.

## ✨ Основні можливості

- 🛰️ **Автоматичне отримання даних** - Інтеграція з Sentinel Hub API для завантаження актуальних супутникових знімків
- 📊 **Розрахунок індексів** - NDVI (рослинність), NDWI (вода), NDBI (забудова), Moisture (вологість)
- 🗺️ **Інтерактивна карта** - Візуалізація даних на базі MapLibre GL JS
- 🔄 **Автоматичний scheduler** - Періодичне оновлення даних без ручного втручання
- 🗄️ **Геопросторова БД** - PostgreSQL + PostGIS для зберігання та аналізу геоданих
- 🚀 **REST API** - FastAPI з автоматичною документацією (Swagger/ReDoc)
- 🐳 **Docker** - Повна контейнеризація для легкого розгортання

## 🏗️ Технологічний стек

### Backend
- **FastAPI** - Сучасний веб-фреймворк для API
- **Python 3.11+** - Основна мова програмування
- **APScheduler** - Автоматизація завдань
- **Rasterio** - Обробка геопросторових растрових даних
- **Shapely** - Геометричні операції

### Frontend
- **Vanilla JavaScript** - Без важких фреймворків
- **MapLibre GL JS** - Інтерактивні карти
- **CSS3** - Сучасна стилізація

### Database
- **Supabase** - PostgreSQL з PostGIS
- **PostGIS** - Геопросторові розширення

### Infrastructure
- **Docker & Docker Compose** - Контейнеризація
- **Nginx** - Веб-сервер для frontend

## 📚 Документація

### Початок роботи
- [🚀 Швидкий старт](docs/getting-started/quick-start.md) - Запуск за 5 хвилин
- [💿 Встановлення](docs/getting-started/installation.md) - Детальна інструкція
- [⚙️ Конфігурація](docs/getting-started/configuration.md) - Налаштування середовища

### Архітектура
- [📐 Огляд системи](docs/architecture/README.md) - Загальна архітектура
- [🔄 Потік даних](docs/architecture/data-flow.md) - Як працює система
- [📋 ADR](docs/architecture/adr/) - Архітектурні рішення

### API
- [📡 Огляд API](docs/api/README.md) - Загальна інформація
- [🛰️ Satellite Endpoints](docs/api/satellite.md) - Робота зі знімками
- [📊 Statistics Endpoints](docs/api/statistics.md) - Статистика регіонів
- [📈 Indices Endpoints](docs/api/indices.md) - Екологічні індекси
- [💡 Приклади](docs/api/examples.md) - Практичні приклади

### Backend
- [🔧 Структура](docs/backend/structure.md) - Організація коду
- [⏰ Scheduler](docs/backend/scheduler.md) - Автоматизація
- [🔌 Сервіси](docs/backend/services.md) - Інтеграції
- [🛠️ Утиліти](docs/backend/utils.md) - Допоміжні модулі

### Frontend
- [🎨 Огляд](docs/frontend/README.md) - Архітектура frontend
- [🗺️ Компонент карти](docs/frontend/map-component.md) - MapLibre GL
- [🔗 API інтеграція](docs/frontend/api-integration.md) - Робота з backend
- [🎚️ Фільтри](docs/frontend/filters.md) - Система фільтрації

### База даних
- [🗄️ Схема БД](docs/database/schema.md) - Структура таблиць
- [🔄 Міграції](docs/database/migrations.md) - Версіонування
- [🌍 PostGIS](docs/database/postgis.md) - Геопросторові функції

### Розгортання
- [🐳 Docker](docs/deployment/docker.md) - Локальне розгортання
- [🚀 Production](docs/deployment/production.md) - Продакшн
- [📊 Моніторинг](docs/deployment/monitoring.md) - Логи та метрики

### Розробка
- [🔀 Git Workflow](docs/development/git-workflow.md) - Conventional Commits
- [✨ Code Style](docs/development/code-style.md) - Ruff, Mypy
- [🧪 Тестування](docs/development/testing.md) - Pytest
- [🤝 Contributing](docs/development/contributing.md) - Як допомогти

### Посібники
- [📖 Використання карти](docs/guides/using-map.md) - Інструкція користувача
- [🎚️ Робота з фільтрами](docs/guides/filters-guide.md) - Фільтрація даних
- [📊 Інтерпретація даних](docs/guides/data-interpretation.md) - Розуміння індексів

## 🚀 Швидкий старт

### Вимоги
- Docker & Docker Compose
- Облікові дані Sentinel Hub (безкоштовна реєстрація)
- Проект Supabase (безкоштовний тарифний план)

### Запуск

1. **Клонувати репозиторій**
   ```bash
   git clone https://github.com/Skriplss/SattelishMaps.git
   cd SattelishMaps
   ```

2. **Налаштувати змінні середовища**
   ```bash
   cp .env.example .env
   # Відредагувати .env з вашими credentials
   ```

3. **Запустити сервіси**
   ```bash
   docker-compose up -d
   ```

4. **Перевірити роботу**
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - Health check: http://localhost:8000/health

## 📁 Структура проекту

```
SattelishMaps/
├── backend/              # FastAPI backend
│   ├── api/             # API endpoints
│   ├── services/        # Бізнес-логіка
│   ├── models/          # Pydantic моделі
│   ├── utils/           # Утиліти
│   ├── config/          # Конфігурація
│   └── scheduler.py     # Автоматизація
├── frontend/            # Vanilla JS frontend
│   ├── js/             # JavaScript модулі
│   ├── css/            # Стилі
│   └── index.html      # Головна сторінка
├── docs/               # Документація
├── database/           # SQL скрипти
├── docker-compose.yml  # Docker конфігурація
└── requirements.txt    # Python залежності
```

## 🔧 Основні команди

```bash
# Запуск в development режимі
docker-compose up

# Запуск в фоновому режимі
docker-compose up -d

# Перегляд логів
docker-compose logs -f backend

# Зупинка сервісів
docker-compose down

# Перебудова образів
docker-compose up --build
```

## 📊 Приклад використання API

```bash
# Отримати статистику для регіону
curl -X GET "http://localhost:8000/api/statistics/region?region_name=Trnava&date_from=2024-01-01&date_to=2024-12-31"

# Отримати дані NDVI
curl -X GET "http://localhost:8000/api/indices/ndvi?region_name=Trnava&limit=10"

# Перевірити статус scheduler
curl -X GET "http://localhost:8000/api/scheduler/status"
```

## 🤝 Внесок у проект

Ми вітаємо внески! Будь ласка, ознайомтеся з [Contributing Guide](docs/development/contributing.md) та [Git Workflow](docs/development/git-workflow.md).

### Процес
1. Fork репозиторію
2. Створити feature branch (`git checkout -b feat/amazing-feature`)
3. Commit зміни (`git commit -m 'feat: add amazing feature'`)
4. Push в branch (`git push origin feat/amazing-feature`)
5. Відкрити Pull Request

## 📝 Ліцензія

Цей проект ліцензовано під MIT License - дивіться [LICENSE](LICENSE) для деталей.

## 👥 Автори

- **Skriplss** - [GitHub](https://github.com/Skriplss)

## 🙏 Подяки

- [Sentinel Hub](https://www.sentinel-hub.com/) - За доступ до супутникових даних
- [Supabase](https://supabase.com/) - За чудову БД платформу
- [MapLibre GL JS](https://maplibre.org/) - За інтерактивні карти

## 📞 Контакти

- GitHub Issues: [Створити issue](https://github.com/Skriplss/SattelishMaps/issues)
- Email: sabitov04@gmail.com

---

**Зроблено з ❤️ для моніторингу навколишнього середовища**