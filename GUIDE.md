# OSM Broker — Guida completa

Questa guida copre l'installazione locale, la configurazione, il deployment su Render e l'utilizzo dell'applicazione.

---

## Indice

1. [Requisiti](#1-requisiti)
2. [Struttura del progetto](#2-struttura-del-progetto)
3. [Sviluppo locale](#3-sviluppo-locale)
4. [Variabili d'ambiente](#4-variabili-dambiente)
5. [Build Docker](#5-build-docker)
6. [Deployment su Render](#6-deployment-su-render)
7. [Autenticazione OSM OAuth2](#7-autenticazione-osm-oauth2)
8. [Pipeline di esportazione](#8-pipeline-di-esportazione)
9. [Simbologia QGIS SwissMap](#9-simbologia-qgis-swissmap)
10. [Test](#10-test)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Requisiti

| Tool | Versione minima |
|---|---|
| Python | 3.11 |
| Node.js | 20 |
| Docker | 24 |
| Redis | 7 |
| GDAL/OGR | 3.8 (incluso nell'immagine Docker) |

---

## 2. Struttura del progetto

```
osm-broker/
├── backend/          FastAPI app + pipeline di conversione
│   ├── app/
│   │   ├── main.py          entry point ASGI
│   │   ├── config.py        impostazioni via pydantic-settings
│   │   ├── models.py        schema Pydantic dei job
│   │   ├── store.py         Redis job store
│   │   ├── auth.py          OAuth2 OSM + JWT
│   │   ├── hot_client.py    client HOT Raw Data API
│   │   ├── pipeline/        downloader · gdal_converter · duckdb_converter · packager
│   │   ├── routers/         /api/jobs · /api/auth
│   │   └── utils/geo.py     validazione geometria AOI
│   └── tests/
├── frontend/         React + MapLibre GL + Vite + TypeScript
│   └── src/
│       ├── components/      Map · AOIPanel · FormatSelector · Layout
│       ├── hooks/           useJob · useAuth
│       ├── services/api.ts  client Axios verso /api
│       └── types/index.ts   tipi condivisi
├── worker/           worker Redis BLPOP che esegue la pipeline
├── resources/
│   └── qstyles_swissmap/   file .qml per QGIS
├── Dockerfile        build monolite (frontend + backend nello stesso container)
├── render.yaml       Blueprint Render (4 servizi)
└── pyproject.toml    configurazione pytest
```

---

## 3. Sviluppo locale

### 3.1 Redis

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 3.2 Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # poi modifica i valori
uvicorn app.main:app --reload --port 8000
```

L'API sarà disponibile su `http://localhost:8000`.  
Documentazione interattiva: `http://localhost:8000/docs`

### 3.3 Worker

Apri un secondo terminale (con il virtualenv attivato):

```bash
# dalla root del repo
PYTHONPATH=backend python worker/worker.py
```

Il worker si mette in ascolto sulla coda Redis e processa i job uno alla volta (o in parallelo se `WORKER_CONCURRENCY > 1`).

### 3.4 Frontend

```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

Il proxy Vite (`vite.config.ts`) redirige `/api/*` verso `http://localhost:8000`, quindi frontend e backend comunicano senza CORS.

---

## 4. Variabili d'ambiente

Copia `backend/.env.example` in `backend/.env` e adatta i valori.

| Variabile | Default | Descrizione |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379` | URL di connessione Redis |
| `HOT_RAW_DATA_API_URL` | `https://api-prod.raw-data.hotosm.org/v1` | Endpoint HOT Raw Data API |
| `MAX_AREA_KM2` | `500` | Limite massimo AOI in km² |
| `OUTPUT_DIR` | `/tmp/osm_broker_jobs` | Directory temporanea per i file generati |
| `QML_DIR` | `resources/qstyles_swissmap` | Percorso dei file .qml |
| `AUTH_ENABLED` | `false` | Abilita autenticazione OSM OAuth2 |
| `OSM_OAUTH_CLIENT_ID` | — | Client ID OAuth2 OSM (solo se `AUTH_ENABLED=true`) |
| `OSM_OAUTH_CLIENT_SECRET` | — | Client Secret OAuth2 OSM |
| `JWT_SECRET_KEY` | — | Chiave HMAC per firmare i JWT |
| `JWT_EXPIRE_MINUTES` | `60` | Durata del token JWT in minuti |
| `DEBUG` | `false` | Modalità debug FastAPI |

### Frontend (build-time)

| Variabile | Default | Descrizione |
|---|---|---|
| `VITE_API_URL` | `/api` | URL base dell'API (usato da `services/api.ts`) |
| `VITE_AUTH_ENABLED` | `false` | Mostra/nasconde il pulsante login nella navbar |

---

## 5. Build Docker

### Monolite (frontend + backend)

```bash
docker build -t osm-broker .
docker run -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  osm-broker
```

### Solo backend

```bash
docker build -t osm-broker-api -f backend/Dockerfile .
```

### Solo worker

```bash
docker build -t osm-broker-worker -f worker/Dockerfile .
```

### Docker Compose (sviluppo)

```yaml
# docker-compose.yml (esempio)
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports: ["8000:8000"]
    environment:
      REDIS_URL: redis://redis:6379
    depends_on: [redis]

  worker:
    build:
      context: .
      dockerfile: worker/Dockerfile
    environment:
      REDIS_URL: redis://redis:6379
    depends_on: [redis]
```

```bash
docker compose up --build
```

---

## 6. Deployment su Render

### 6.1 Prima deploy (Blueprint)

1. Fai un fork del repo su GitHub (o lavora direttamente su `intelligeo/osm-broker`)
2. Su [render.com](https://render.com) → **New › Blueprint**
3. Connetti il repository e seleziona `render.yaml`
4. Render crea automaticamente i 4 servizi:

| Servizio | Tipo | Piano | Nota |
|---|---|---|---|
| `osm-broker` | Static Site | Free | frontend |
| `osm-broker-api` | Web Service (Docker) | Standard | `backend/Dockerfile` |
| `osm-broker-worker` | Background Worker (Docker) | Standard | `worker/Dockerfile` |
| `osm-broker-redis` | Redis | Free | persistenza job |

5. Imposta le variabili sensibili (se `AUTH_ENABLED=true`):
   - `OSM_OAUTH_CLIENT_ID`
   - `OSM_OAUTH_CLIENT_SECRET`
   - `JWT_SECRET_KEY` (oppure lascia `generateValue: true` nel yaml)

### 6.2 Aggiornamenti

Ogni push su `main` avvia il redeploy automatico di tutti i servizi.

### 6.3 URL di produzione

- Frontend: `https://osm-broker.onrender.com`
- API: `https://osm-broker-api.onrender.com/api`
- Docs: `https://osm-broker-api.onrender.com/docs`

---

## 7. Autenticazione OSM OAuth2

L'autenticazione è **opzionale** e disabilitata di default (`AUTH_ENABLED=false`).  
Quando abilitata, ogni job viene associato all'utente OSM che lo ha creato e solo lui può scaricarlo.

### Configurazione OAuth2 su OpenStreetMap

1. Accedi a [www.openstreetmap.org/oauth2/applications](https://www.openstreetmap.org/oauth2/applications)
2. Crea una nuova applicazione:
   - **Redirect URI**: `https://osm-broker-api.onrender.com/api/auth/callback`
   - **Scopes**: `read_prefs`
3. Copia Client ID e Client Secret nelle variabili d'ambiente

### Flusso

```
browser → GET /api/auth/login → redirect OSM → callback → JWT cookie → accesso API
```

---

## 8. Pipeline di esportazione

Il worker esegue questi step in sequenza per ogni job:

```
1. downloader.py
   └─ POST HOT Raw Data API con GeoJSON AOI
   └─ polling fino a completamento
   └─ download .gpkg in OUTPUT_DIR/{job_id}/

2. gdal_converter.py  (se formato ≠ gpkg)
   └─ ogr2ogr → .geojson / .gdb / passthrough per duckdb

3. duckdb_converter.py  (se formato = duckdb)
   └─ carica .gpkg in DuckDB
   └─ esporta .duckdb + .parquet per layer

4. packager.py
   └─ crea ZIP con struttura:
       data/        file dati (gpkg/geojson/gdb/duckdb/parquet)
       styles/      file .qml (se symbology=true)
       README.txt   licenza ODbL + crediti OSM
```

### Formati supportati

| Formato | Estensione | Note |
|---|---|---|
| GeoPackage | `.gpkg` | default, passthrough diretto da HOT |
| GeoJSON | `.geojson` | conversione via ogr2ogr |
| Esri FileGDB | `.gdb` | richiede driver FileGDB in GDAL |
| DuckDB | `.duckdb` + `.parquet` | uno file per layer OSM |

---

## 9. Simbologia QGIS SwissMap

I file `.qml` in `resources/qstyles_swissmap/` sono inclusi nello ZIP quando l'opzione **Swiss Map Style** è attiva nel pannello di configurazione.

Layer disponibili:

| File QML | Layer OSM |
|---|---|
| `airports.qml` | Aeroporti e aerodromi |
| `boundaries_adm0.qml` / `_adm1.qml` | Confini nazionali e regionali |
| `buildings.qml` | Edifici |
| `hillshade.qml` | Ombreggiatura rilievo |
| `landuse.qml` | Uso del suolo |
| `places.qml` | Luoghi abitati |
| `railways.qml` | Ferrovie |
| `roads.qml` | Strade |
| `water.qml` | Superfici d'acqua |
| `waterways.qml` | Corsi d'acqua |

### Applicare gli stili in QGIS

1. Apri il `.gpkg` in QGIS
2. Tasto destro sul layer → **Proprietà › Stile**
3. In basso → **Carica stile** → seleziona il `.qml` corrispondente
4. **OK**

---

## 10. Test

```bash
# dalla root del repo (con virtualenv attivato)
pytest

# con output verboso
pytest -v

# solo un file
pytest backend/tests/test_api.py
```

I test usano `httpx.AsyncClient` con un'app FastAPI in-process e un Redis mock (`fakeredis`).

---

## 11. Troubleshooting

### I pulsanti "Disegna poligono" e "Cancella" non funzionano

Assicurati che `vite.config.ts` contenga l'alias:

```ts
resolve: {
  alias: { 'mapbox-gl': 'maplibre-gl' }
}
```

`@mapbox/mapbox-gl-draw` importa internamente `mapbox-gl`; senza l'alias i click handler non vengono registrati.

### Il worker non processa i job

- Verifica che Redis sia raggiungibile: `redis-cli ping`
- Controlla che `PYTHONPATH=backend` sia impostato prima di avviare il worker
- Controlla i log: `docker logs osm-broker-worker`

### GDAL non trova il driver FileGDB

Il driver FileGDB non è incluso nella build open-source di GDAL. Usa l'immagine `ghcr.io/osgeo/gdal:ubuntu-small-*` che lo include, oppure installa `libgdal-dev` con i plugin enterprise.

### Il download da HOT Raw Data API è lento

L'API HOT ha una coda interna; per aree grandi il tempo di attesa può superare i 5 minuti. Il worker esegue polling ogni 10 secondi fino a completamento o timeout (configurabile in `hot_client.py`).

### Errore 403 su Render dopo un push

Verifica che il Personal Access Token GitHub abbia i scope `repo` e `workflow` abilitati.

---

> Per supporto: [ask@intelligeo.ch](mailto:ask@intelligeo.ch) — [INTELLIGEO.ch](https://www.intelligeo.ch)
