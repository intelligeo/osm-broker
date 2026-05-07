# OSM Broker

> Web client moderno per l'esportazione di dati OpenStreetMap in formato GeoPackage, FileGDB, DuckDB e GeoJSON — con simbologia QGIS SwissMap inclusa.

Progetto sviluppato e mantenuto da **[INTELLIGEO.ch](https://www.intelligeo.ch)** — consulenza e sviluppo GIS/web.  
Per supporto o informazioni: [ask@intelligeo.ch](mailto:ask@intelligeo.ch)

[![CI](https://github.com/intelligeo/osm-broker/actions/workflows/ci.yml/badge.svg)](https://github.com/intelligeo/osm-broker/actions/workflows/ci.yml)
[![Deploy](https://img.shields.io/badge/deploy-Render-46E3B7?logo=render)](https://osm-broker.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Funzionalità

| Feature | Dettaglio |
|---|---|
| **Area di interesse** | Disegna un poligono sulla mappa (MapLibre GL JS + MapboxDraw) |
| **Formati di esportazione** | GeoPackage · GeoJSON · Esri FileGDB · DuckDB + GeoParquet |
| **Simbologia** | File `.qml` SwissMap per QGIS opzionalmente inclusi nello ZIP |
| **Fonte dati** | HOT Raw Data API — aggiornamento OSM giornaliero |
| **Limite area** | 500 km² (configurabile via `MAX_AREA_KM2`) |
| **Autenticazione** | OAuth2 OpenStreetMap (opzionale, abilitabile via `AUTH_ENABLED`) |

---

## Architettura

```
browser
  └─ React + MapLibre GL JS (Vite + TypeScript)
        │  POST /api/jobs   GET /api/jobs/{id}
        ▼
   FastAPI  (backend/)
        │  RPUSH osm_broker:queue
        ▼
   Redis
        │  BLPOP
        ▼
   Worker  (worker/)
        ├─ HOT raw-data-api  → scarica .gpkg
        ├─ GDAL/OGR          → converte formato
        ├─ DuckDB            → esporta .duckdb + .parquet
        └─ packager          → assembla ZIP (data/ + styles/ + README)
```

---

## Quick start — sviluppo locale

```bash
# Redis
docker run -d -p 6379:6379 redis:7-alpine

# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Worker (altra shell)
PYTHONPATH=backend python worker/worker.py

# Frontend
cd frontend && npm install && npm run dev   # → http://localhost:5173
```

Per la guida completa (Docker, variabili d'ambiente, deployment su Render, simbologia QGIS) consulta [GUIDE.md](GUIDE.md).

---

## Deployment su Render

Il file `render.yaml` definisce 4 servizi (`osm-broker`, `osm-broker-api`, `osm-broker-worker`, `osm-broker-redis`).  
Ogni push su `main` avvia automaticamente il redeploy di tutti i servizi.

1. Fork/push su GitHub
2. [render.com](https://render.com) → **New › Blueprint** → seleziona `render.yaml`
3. Imposta `JWT_SECRET_KEY` (o lascia `generateValue: true`) e, se abiliti l'auth, `OSM_OAUTH_CLIENT_ID` / `OSM_OAUTH_CLIENT_SECRET`

---

## Licenza dati

I dati esportati sono © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) sotto licenza **ODbL 1.0**.

## Licenza software

MIT — vedi [LICENSE](LICENSE)

---

> Sviluppato e mantenuto da [INTELLIGEO.ch](https://www.intelligeo.ch) — consulenza GIS, sviluppo web e soluzioni open data.
