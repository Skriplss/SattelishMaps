# Backend Setup & Configuration

## Environment Variables

Create a `.env` file in the **repository root** (`cp .env.example .env`).

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `development` / `production` | `development` |
| `DEBUG` | Enables `/docs`, verbose errors | `true` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| **Database** | | |
| `SUPABASE_URL` | Supabase project URL | *required* |
| `SUPABASE_ANON_KEY` | Public anon key | *required* |
| `SUPABASE_SERVICE_KEY` | Service role key (bypasses RLS — keep secret) | *required* |
| **Sentinel Hub** | | |
| `SH_CLIENT_ID` | OAuth client id | *required* |
| `SH_CLIENT_SECRET` | OAuth client secret | *required* |
| **Scheduler** | | |
| `SCHEDULER_ENABLED` | Background jobs on/off | `true` |
| `SCHEDULER_INTERVAL_HOURS` | Stats fetch cadence | `4` |
| `DEFAULT_SEARCH_BOUNDS` | AOI polygon (WKT) | Trnava |
| `DEFAULT_REGION_NAME` | Region name written to DB | `Trnava` |
| `PROCESS_HISTORICAL_DATA` | Fetch on startup | `false` |
| **Coverage & tiles** | | |
| `COVERAGE_BBOX` | Served area, `min_lon,min_lat,max_lon,max_lat` | Slovakia |
| `PREFER_PIXEL_TILES` | Render map tiles from `pixel_data` before calling Sentinel Hub | `false` |

Database schema setup: see [../../database/README.md](../../database/README.md).

## Local Development (Python)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Server: `http://localhost:8000`, docs: `http://localhost:8000/docs`.

## Docker Development (recommended)

```bash
docker compose -f docker-compose.dev.yml up --build
```

Hot-reload for both backend (`uvicorn --reload`) and frontend (Vite HMR).
See [../deployment/docker-setup.md](../deployment/docker-setup.md).

## Verifying

```bash
curl http://localhost:8000/health
# {"status":"ok","database":"ok",...}  — "degraded" means Supabase is unreachable
```
