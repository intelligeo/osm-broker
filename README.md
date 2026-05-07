# OSM Broker

> Web client moderno per l'esportazione di dati OpenStreetMap in formato GeoPackage, FileGDB, DuckDB e GeoJSON — con simbologia QGIS SwissMap inclusa.

Progetto sviluppato e mantenuto da **[INTELLIGEO.ch](https://www.intelligeo.ch)** — consulenza e sviluppo GIS/web.
Per supporto o informazioni: [ask@intelligeo.ch](mailto:ask@intelligeo.ch)

[![CI](https://github.com/intelligeo/osm-broker/actions/workflows/ci.yml/badge.svg)](https://github.com/intelligeo/osm-broker/actions/workflows/ci.yml)
[![Deploy](https://img.shields.io/badge/deploy-Render-46E3B7?logo=render)](https://osm-broker.onrender.com)

---

## Funzionalità

| Feature | Dettaglio |
|---|---|
| **Area di interesse** | Disegna un poligono sulla mappa (MapLibre GL JS + MapboxDraw) |
| **Formati di esportazione** | GeoPackage · GeoJSON · Esri FileGDB · DuckDB + GeoParquet |
| **Simbologia** | File `.qml` SwissMap per QGIS opzionalmente inclusi nello ZIP |
| **Fonte dati** | HOT Raw Data API — aggiornamento OSM giornaliero |
| **Limite area** | 500 km² (configurabile via `MAX_AREA_KM2`) |

---

## Architettura

```
browser
  └─ React + MapLibre GL JS (Vite)
        │  POST /api/jobs   GET /api/jobs/{id}
        ▼
   FastAPI (backend/)
        │  RPUSH osm_broker:queue
        ▼
   Redis
        │  BLPOP
        ▼
   Worker (worker/)
        ├─ HOT raw-data-api  → scarica .gpkg
        ├─ GDAL/OGR          → converte formato
        ├─ DuckDB            → esporta .duckdb + .parquet
        └─ packager          → assembla ZIP (data/ + styles/ + README)
```

---

## Sviluppo locale

### Requisiti

- Python 3.11+
- Node.js 20+
- Docker (per GDAL) oppure `gdal-bin` installato localmente
- Redis (via Docker: `docker run -p 6379:6379 redis:7-alpine`)

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # adatta i valori
uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
# dalla root del repo (necessario per PYTHONPATH)
PYTHONPATH=backend python worker/worker.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

### Test

```bash
pytest   # dalla root — pyproject.toml configura testpaths=backend/tests
```

---

## Deployment su Render

Il file `render.yaml` definisce 4 servizi:

| Servizio | Tipo | Piano |
|---|---|---|
| `osm-broker-frontend` | Static Site | Free |
| `osm-broker-api` | Web Service (Docker) | Standard |
| `osm-broker-worker` | Background Worker (Docker) | Standard |
| `osm-broker-redis` | Redis | Free |

### Prima deploy

1. Fork/push su GitHub
2. Su [render.com](https://render.com) → **New > Blueprint** → seleziona `render.yaml`
3. Imposta manualmente le variabili d'ambiente sensibili:
   - `JWT_SECRET_KEY` (già `generateValue: true`)
   - `OSM_OAUTH_CLIENT_ID` / `OSM_OAUTH_CLIENT_SECRET` (quando si abilita l'auth)

### Aggiornamenti

Ogni push su `main` avvia automaticamente il redeploy di tutti i servizi.

---

## Simbologia QGIS

I file `.qml` in `resources/qstyles_swissmap/` sono inclusi nello ZIP quando l'opzione **Swiss Map Style** è attiva:

`airports · boundaries · buildings · hillshade · landuse · places · railways · roads · water · waterways`

Per usarli in QGIS: *Layer > Proprietà > Stile > Carica stile* → seleziona il `.qml` corrispondente.

---

## Licenza dati

I dati esportati sono © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) sotto licenza **ODbL 1.0**.

## Licenza software

MIT — vedi [LICENSE](LICENSE)

---

> Sviluppato e mantenuto da [INTELLIGEO.ch](https://www.intelligeo.ch) — consulenza GIS, sviluppo web e soluzioni open data.
