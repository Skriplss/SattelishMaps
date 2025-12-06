# Архітектура SattelishMaps

Огляд архітектури системи для моніторингу навколишнього середовища через супутникові дані.

## 📐 Загальна схема

```mermaid
graph TB
    subgraph "External Services"
        SH[Sentinel Hub API]
        SB[(Supabase PostgreSQL + PostGIS)]
    end
    
    subgraph "Backend FastAPI"
        API[REST API Endpoints]
        SCH[Scheduler APScheduler]
        SERV[Services Layer]
        UTILS[Utils Logger Validators]
    end
    
    subgraph "Frontend"
        MAP[MapLibre GL JS]
        UI[UI Components]
        FILTERS[Filters System]
    end
    
    SH -->|Satellite Data| SERV
    SERV -->|Store Statistics| SB
    SCH -->|Trigger Every 6h| SERV
    API -->|Query Data| SB
    UI -->|HTTP Requests| API
    API -->|JSON Response| UI
    MAP -->|Visualize| UI
    FILTERS -->|Filter Params| API
    
    style SH fill:#e1f5ff
    style SB fill:#d4edda
    style API fill:#fff3cd
    style MAP fill:#f8d7da
```

## 🏗️ Компоненти системи

### 1. Backend (FastAPI)
- **REST API** - Endpoints для отримання даних
- **Scheduler** - Автоматичне завантаження даних кожні 6 годин
- **Services** - Бізнес-логіка та інтеграції
- **Utils** - Логування, валідація, обробка помилок

### 2. Frontend (Vanilla JS)
- **MapLibre GL** - Інтерактивна карта
- **UI Components** - Фільтри, легенда, інформаційні панелі
- **API Integration** - Комунікація з backend

### 3. Database (Supabase)
- **PostgreSQL** - Реляційна БД
- **PostGIS** - Геопросторові розширення
- **Tables** - region_statistics для зберігання індексів

### 4. External Services
- **Sentinel Hub** - Джерело супутникових даних
- **Supabase** - Хостинг БД

## 📊 Потік даних

Детальний опис потоку даних: [Data Flow](data-flow.md)

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant SH as Sentinel Hub
    participant SERV as Services
    participant DB as Supabase
    participant API as REST API
    participant FE as Frontend
    
    SCH->>SERV: Trigger fetch (every 6h)
    SERV->>SH: Request statistics (NDVI, NDWI, NDBI, Moisture)
    SH-->>SERV: Return aggregated data
    SERV->>DB: Store in region_statistics
    
    FE->>API: GET /api/statistics/region
    API->>DB: Query data
    DB-->>API: Return results
    API-->>FE: JSON response
    FE->>FE: Visualize on map
```

## 🔑 Ключові рішення

Архітектурні рішення задокументовані у форматі ADR (Architecture Decision Records):

- [ADR-001: System Architecture](adr/001-system-architecture.md) - Вибір FastAPI + Supabase + Docker
- [ADR-002: Database Choice](adr/002-database-choice.md) - Чому Supabase/PostgreSQL/PostGIS
- [ADR-003: Frontend Framework](adr/003-frontend-framework.md) - Vanilla JS + MapLibre GL

## 🛠️ Технологічний стек

### Backend
| Технологія | Версія | Призначення |
|-----------|--------|-------------|
| Python | 3.11+ | Основна мова |
| FastAPI | 0.104+ | Web framework |
| APScheduler | 3.10+ | Автоматизація |
| Rasterio | 1.3+ | Обробка растрів |
| Shapely | 2.0+ | Геометрія |
| httpx | 0.25+ | HTTP клієнт |

### Frontend
| Технологія | Версія | Призначення |
|-----------|--------|-------------|
| MapLibre GL JS | 3.x | Інтерактивні карти |
| Vanilla JavaScript | ES6+ | Логіка |
| CSS3 | - | Стилізація |

### Infrastructure
| Технологія | Версія | Призначення |
|-----------|--------|-------------|
| Docker | 20.10+ | Контейнеризація |
| Docker Compose | 2.0+ | Оркестрація |
| Nginx | 1.24+ | Web сервер |
| PostgreSQL | 15+ | База даних |
| PostGIS | 3.3+ | Геопросторові функції |

## 📁 Структура проекту

```
SattelishMaps/
├── backend/
│   ├── api/                 # API endpoints
│   │   ├── satellite.py     # Satellite data endpoints
│   │   ├── statistics.py    # Statistics endpoints
│   │   └── indices.py       # Indices endpoints
│   ├── services/            # Business logic
│   │   ├── sentinelhub_service.py
│   │   └── supabase_service.py
│   ├── models/              # Pydantic models
│   ├── utils/               # Utilities
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── error_handlers.py
│   ├── config/              # Configuration
│   │   └── settings.py
│   ├── scheduler.py         # APScheduler
│   └── app.py              # FastAPI app
├── frontend/
│   ├── js/
│   │   ├── map.js          # Map component
│   │   ├── api.js          # API integration
│   │   ├── filters.js      # Filters logic
│   │   └── colormap.js     # Color mapping
│   ├── css/
│   │   └── styles.css
│   └── index.html
├── database/
│   └── schema.sql          # DB schema
├── docs/                   # Documentation
└── docker-compose.yml      # Docker config
```

## 🔐 Безпека

### Аутентифікація
- Supabase Row Level Security (RLS)
- API keys для Sentinel Hub

### CORS
- Налаштовані дозволені origins
- Credentials підтримка

### Secrets Management
- Environment variables
- `.env` файли (не в Git)
- Docker secrets для production

## 📈 Масштабованість

### Горизонтальне масштабування
- Backend: Можна запустити кілька інстансів за load balancer
- Frontend: Статичні файли через CDN

### Вертикальне масштабування
- Збільшення ресурсів контейнерів
- Оптимізація запитів до БД

### Кешування
- HTTP кешування для статичних даних
- Database query caching

## 🔄 CI/CD

Рекомендована pipeline:

```mermaid
graph LR
    A[Git Push] --> B[Lint & Format]
    B --> C[Type Check]
    C --> D[Tests]
    D --> E[Build Docker]
    E --> F[Deploy]
    
    style A fill:#e1f5ff
    style F fill:#d4edda
```

Детальніше: [Development Guide](../development/README.md)

## 📚 Додаткові ресурси

- [System Overview](system-overview.md) - Детальний огляд компонентів
- [Data Flow](data-flow.md) - Потік даних через систему
- [ADR Directory](adr/) - Всі архітектурні рішення

## Наступні кроки

- 📖 Вивчіть [API Documentation](../api/README.md)
- 🔧 Ознайомтеся з [Backend Structure](../backend/structure.md)
- 🎨 Перегляньте [Frontend Architecture](../frontend/README.md)
