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
`database/schemas/sentinel2_schema.sql`
in your Supabase SQL Editor.

## Manual Data Import
If API access is restricted, you can manually import Sentinel-2 data:

1.  Download `.SAFE` archives from [Copernicus Browser](https://browser.dataspace.copernicus.eu/).
2.  Place the unpacked `.SAFE` folders into `downloads/`.
3.  Run the import script:
    ```bash
    docker-compose exec backend python scripts/import_safe_data.py
    ```

## Logs
To view application logs:
```bash
docker-compose logs -f backend
```
