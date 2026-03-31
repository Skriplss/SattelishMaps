# SattelishMaps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

## Key Features

-  **Automated Data Acquisition**: Integration with Sentinel Hub API for fetching up-to-date satellite imagery.
-  **Index Calculation**: On-the-fly generation of NDVI (Vegetation), NDWI (Water), NDBI (Built-up), and Moisture indices.
-  **Interactive Mapping**: High-performance visualization using MapLibre GL JS.
-  **Scheduler**: Background tasks for periodic data updates without manual intervention.
-  **Geospatial Database**: Powered by Supabase (PostgreSQL + PostGIS) for robust vector data handling.
-  **Dockerized**: Fully containerized for consistent deployment.

## Technology Stack

- **Backend**: FastAPI, APScheduler, Shapely, Sentinel Hub API
- **Frontend**: React, TypeScript, MapLibre GL JS, TailwindCSS
- **Database**: PostgreSQL with PostGIS (via Supabase)
- **Infrastructure**: Docker & Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Sentinel Hub Account (Client ID & Secret)
- Supabase Project (DB Connection String)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Skriplss/SattelishMaps.git
   cd SattelishMaps
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API Docs: http://localhost:8000/docs

## Documentation

- **[Backend Guide](docs/backend/README.md)**: API architecture, services, and scheduler details.
- **[Architecture Decisions](docs/architecture/decisions/)**: ADRs recording key technical choices.
- **[Deployment](docs/deployment/production.md)**: Production setup guide.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Skriplss** - [GitHub](https://github.com/Skriplss)
- **WraithCipher** - [GitHub](https://github.com/WraithCipher)
- **Dxfluxite** - [GitHub](https://github.com/Dxfluxite)
- **r0sEm** - [GitHub](https://github.com/r0sEm)
