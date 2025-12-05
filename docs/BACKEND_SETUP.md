# 🚀 Backend Setup & Running Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in the root directory (copy from `.env.example`):

```env
# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Copernicus (Optional for MVP)
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password

# MapTiler
MAPTILER_API_KEY=your_api_key

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Run Backend

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

> **Note**: Backend работает с данными **Sentinel-5P** (атмосферные показатели):
> - **NO₂** - діоксид азоту (транспорт/промисловість)
> - **O₃** - озон (поверхневий озон)
> - **SO₂** - сірчистий газ (промислові викиди)
> - **AER_AI** - аерозольний індекс (дим, пил, PM2.5)
> - **CO** - чадний газ (пожежі, транспорт)

### 4. Test Backend

Open your browser and visit:
- **Health Check**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/docs
- **Alternative Docs**: http://localhost:5000/redoc

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - API info

### Satellite Data
- `GET /api/satellite-data` - List images with filters
  - Query params: `date_from`, `date_to`, `cloud_max`, `platform`, `page`, `limit`
- `GET /api/satellite-data/{id}` - Get single image
- `POST /api/satellite-data/search` - Search Copernicus
- `POST /api/satellite-data` - Create image record
- `DELETE /api/satellite-data/{id}` - Delete image
- `GET /api/satellite-data/bounds/search` - Get images in bounding box

### Statistics
- `GET /api/statistics/{image_id}` - Get image statistics
- `GET /api/statistics/timeseries/{area_name}` - Time series data
- `GET /api/statistics/area/summary` - Area summary statistics

## Example Requests

### Get Satellite Images
```bash
curl "http://localhost:5000/api/satellite-data?limit=5&cloud_max=20"
```

### Search Copernicus
```bash
curl -X POST http://localhost:5000/api/satellite-data/search \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2023-01-01",
    "date_to": "2023-12-31",
    "bounds": {
      "min_lat": 48.0,
      "max_lat": 52.0,
      "min_lon": 12.0,
      "max_lon": 16.0
    },
    "cloud_max": 30
  }'
```

### Get Images in Bounds
```bash
curl "http://localhost:5000/api/satellite-data/bounds/search?min_lat=48&max_lat=52&min_lon=12&max_lon=16&cloud_max=20"
```

## Features

✅ **FastAPI** - Modern async Python framework
✅ **Pydantic Validation** - Request/response validation
✅ **Error Handling** - Centralized exception handling
✅ **Logging** - Structured logging with levels
✅ **CORS** - Configured for frontend access
✅ **Auto Documentation** - Swagger UI at `/docs`
✅ **Pagination** - Built-in pagination support
✅ **Retry Logic** - Exponential backoff for external APIs
✅ **Type Hints** - Full type annotations

## Architecture

```
backend/
├── app.py                    # Main FastAPI application
├── requirements.txt          # Python dependencies
├── run.bat / run.sh         # Run scripts
│
├── api/                     # API endpoints
│   ├── satellite.py         # Satellite data endpoints
│   └── statistics.py        # Statistics endpoints
│
├── models/                  # Pydantic models
│   ├── satellite_image.py   # Satellite image schemas
│   └── statistics.py        # Statistics schemas
│
├── services/                # Business logic
│   ├── supabase_service.py  # Database operations
│   └── copernicus_service.py # Copernicus API client
│
├── utils/                   # Utilities
│   ├── validators.py        # Request validators
│   ├── error_handlers.py    # Exception handlers
│   ├── response_formatter.py # Response formatting
│   └── logger.py            # Logging setup
│
└── config/                  # Configuration
    └── settings.py          # Environment settings
```

## Development

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and small

### Adding New Endpoint

1. Create route in `api/` directory
2. Define Pydantic models in `models/`
3. Add business logic in `services/`
4. Register router in `app.py`

Example:
```python
# api/my_endpoint.py
from fastapi import APIRouter
from utils.response_formatter import success_response

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return success_response(data={"message": "Hello"})

# app.py
from api import my_endpoint
app.include_router(my_endpoint.router, prefix="/api", tags=["My Feature"])
```

### Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests (when created)
pytest
```

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Supabase Connection Error
- Check `.env` file has correct SUPABASE_URL and keys
- Verify Supabase project is active
- Check network connection

### Copernicus API Error
- Copernicus credentials are optional for MVP
- If not configured, search will return empty results
- Register at https://scihub.copernicus.eu/

### Port Already in Use
```bash
# Change port in run script or use:
uvicorn app:app --reload --port 8000
```

## Production Deployment (Docker)

Coming soon - Docker configuration will be added later for deployment.

## Logs

Logs are written to:
- **Console**: All environments
- **File**: `logs/app.log` (production only)

Log levels: DEBUG, INFO, WARNING, ERROR

## Performance

- **GZIP Compression**: Enabled for responses > 1KB
- **Connection Pooling**: Supabase client reuses connections
- **Async Operations**: FastAPI handles requests asynchronously
- **Retry Logic**: Copernicus API has exponential backoff

## Security

- **CORS**: Configured for specific origins
- **Environment Variables**: Sensitive data in `.env`
- **Input Validation**: Pydantic validates all inputs
- **Error Messages**: Don't expose internal details in production

---

**Ready to code! 🚀**

For questions, check the main project README or ask in the team chat.
