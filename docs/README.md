# SattelishMaps Documentation

Satellite imagery analysis platform for Slovakia: NDVI / NDWI / NDBI / Moisture
indices from Sentinel-2, rendered on an interactive map with per-pixel analytics.

## Structure

```
docs/
├── architecture/
│   ├── overview.md          ← system architecture, data flows (diagrams)
│   └── decisions/           ← ADRs (Architecture Decision Records)
├── backend/
│   ├── README.md            ← backend structure & components
│   ├── setup.md             ← env vars, local & Docker runs
│   ├── api.md               ← REST API reference
│   ├── services.md          ← service layer, tile & pixel pipelines (diagrams)
│   ├── scheduler.md         ← background jobs
│   └── pixel-data.md        ← pixel data deep-dive (RU)
├── database/
│   └── schema.md            ← ER diagram, partitioning, RPC reference
├── frontend/
│   ├── architecture.md      ← components, state, data flow (diagrams)
│   └── features.md          ← user-facing feature guide
└── deployment/
    ├── docker-setup.md      ← Docker dev & production setup
    └── production.md        ← server deployment, reverse proxy, SSL
```

## Where to start

| I want to… | Read |
|---|---|
| Understand the system at a glance | [architecture/overview.md](architecture/overview.md) |
| Run the project | [deployment/docker-setup.md](deployment/docker-setup.md) |
| Create / recreate the database | [../database/README.md](../database/README.md) |
| Call the API | [backend/api.md](backend/api.md) |
| Understand tile serving & pixel pipelines | [backend/services.md](backend/services.md) |
| Work on the UI | [frontend/architecture.md](frontend/architecture.md) |
| Know why the stack looks like this | [architecture/decisions/](architecture/decisions/) |
