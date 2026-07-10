# Deployment Guide

This guide describes how to deploy the application using Docker and Docker Compose.

## Prerequisites

*   Docker Engine 20.10+
*   Docker Compose v2+
*   Copernicus Data Space Ecosystem Account
*   Supabase Project

## Configuration

1.  **Clone the repository**.
2.  **Create Environment File**:
    Copy `.env.example` to `.env`:
    ```bash
    cp .env .env
    ```
3.  **Configure `.env`**:
    *   `SUPABASE_URL`: Your project URL.
    *   `SUPABASE_SERVICE_KEY`: Service role API key.
    *   `COPERNICUS_USERNAME`: Your email.
    *   `COPERNICUS_PASSWORD`: Your password.
    *   `SCHEDULER_ENABLED`: Set to `true` for automatic updates.

## Building and Running

### Development Mode
To run with live reloading (source code mounted):

```bash
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`.

### Database Setup
Ensure your Supabase project has the required schema. Run the SQL script located at:
`database/schemas/init.sql`
in your Supabase SQL Editor (see `database/README.md` for details).

## Development Mode (Hot Reload)

For local development use the dev compose file — code changes are picked up without rebuilds:

```bash
docker compose -f docker-compose.dev.yml up
```

- **Backend** (`http://localhost:8000`): uvicorn runs with `--reload`, restarting on every edit in `backend/`.
- **Frontend** (`http://localhost:3000`): Vite dev server with HMR — the browser updates on save.
- The scheduler is disabled by default in dev (`SCHEDULER_ENABLED=false`) to avoid burning Sentinel Hub quota; override in `.env` if needed.

## Manual Data Loading
Data is normally fetched automatically by the scheduler. To load data manually:

```bash
# Fetch recent statistics immediately
docker-compose exec backend python scripts/fetch_now.py

# Bulk-load 12 months of historical statistics
docker-compose exec backend python scripts/fetch_historical_stats.py

# Load raw pixel data for an area
docker-compose exec backend python -m scripts.fetch_pixel_data --bbox "19.5,48.5,19.7,48.7" --date "2024-12-05"
```

## Logs
To view application logs:
```bash
docker-compose logs -f backend
```
