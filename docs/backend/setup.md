# Backend Setup & Configuration

## Environment Variables

Create a `.env` file in the root directory.

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Execution environment (`development`, `production`) | `production` |
| `DEBUG` | Enable debug logs | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| **Database** | | |
| `SUPABASE_URL` | Connection URL for Supabase/Postgres | *Required* |
| `SUPABASE_ANON_KEY` | Public anonymous key | *Required* |
| `SUPABASE_SERVICE_KEY` | Private service role key | *Required* |
| **Sentinel Hub** | | |
| `SH_CLIENT_ID` | OAuth Client ID | *Required* |
| `SH_CLIENT_SECRET` | OAuth Client Secret | *Required* |
| **Scheduler** | | |
| `SCHEDULER_ENABLED` | Enable background tasks | `true` |
| `SCHEDULER_INTERVAL_HOURS` | Frequency of data fetch | `6` |
| `PROCESS_HISTORICAL_DATA` | Fetch past data on startup | `false` |

## Local Development (Python)

1. **Install Dependencies**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Server will be available at `http://localhost:8000`.

## Docker Development

1. **Build and Run**
   ```bash
   docker-compose up backend
   ```
   This uses the `Dockerfile` in the root (context `.`) or `backend/Dockerfile` depending on configuration.
