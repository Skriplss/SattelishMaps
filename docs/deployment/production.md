# Production Deployment Guide

This guide covers deploying SattelishMaps to a Linux server using Docker.

## Prerequisites
- A Linux server (Ubuntu 22.04 LTS recommended)
- Docker Engine & Docker Compose v2+
- Domain name (optional but recommended)
- Sentinel Hub credentials

## 1. Server Setup

Clone the repository to `/opt/sattelishmaps` (or your preferred location).
```bash
git clone https://github.com/Skriplss/SattelishMaps.git /opt/sattelishmaps
cd /opt/sattelishmaps
```

## 2. Configuration

Create the production `.env` file.
```bash
cp .env.example .env
nano .env
```
Ensure you set:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `SUPABASE_*` keys
- `SH_CLIENT_*` keys

## 3. Deployment

Run the containers in detached mode.
```bash
docker-compose up -d --build
```

## 4. Reverse Proxy & SSL (Recommended)

In a production environment, you should run the application behind a reverse proxy like Nginx or Traefik to handle SSL termination.

### Nginx Example
```nginx
server {
    listen 80;
    server_name maps.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

## 5. Maintenance

### Updating
```bash
git pull origin main
docker-compose up -d --build
```

### Logs
```bash
docker-compose logs -f backend
```
