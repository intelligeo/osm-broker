"""
OSM Broker FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .config import get_settings
from .routers import auth, jobs
from .store import ping_redis

settings = get_settings()

# Limiter condiviso — importato dai router
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])


def create_app() -> FastAPI:
    app = FastAPI(
        title="OSM Broker",
        summary="Clip, convert and download OpenStreetMap data with QGIS symbology.",
        description=(
            "OSM Broker consente di selezionare un'area di interesse geografica, "
            "scaricare i dati OSM tramite HOT Raw Data API e riceverli via ZIP "
            "in formato GeoPackage, GeoJSON, FileGDB o DuckDB — con simbologia "
            "QGIS SwissMap opzionale.\n\n"
            "**Fonte dati**: © OpenStreetMap contributors (ODbL 1.0)  \n"
            "**Sorgente**: [HOT Raw Data API](https://api-prod.raw-data.hotosm.org/v1)"
        ),
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        contact={"name": "INTELLIGEO.ch", "url": "https://www.intelligeo.ch", "email": "ask@intelligeo.ch"},
        openapi_tags=[
            {"name": "jobs",  "description": "Crea e monitora job di esportazione."},
            {"name": "auth",  "description": "OAuth2 OpenStreetMap (attivato quando `AUTH_ENABLED=true`)."},
            {"name": "meta",  "description": "Health-check e informazioni sull'istanza."},
        ],
    )

    # ── Rate limiting ──────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [
            "https://osm-broker.onrender.com",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────
    app.include_router(jobs.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")

    # ── Health & meta ─────────────────────────────────────────────
    @app.get("/api/health", tags=["meta"], summary="Stato dell'istanza e di Redis")
    async def health() -> dict:
        redis_ok = await ping_redis()
        return {
            "status": "ok" if redis_ok else "degraded",
            "redis": redis_ok,
            "version": settings.app_version,
        }

    @app.get("/api/version", tags=["meta"], summary="Versione e configurazione pubblica")
    def version() -> dict:
        return {
            "version": settings.app_version,
            "auth_enabled": settings.auth_enabled,
            "max_area_km2": settings.max_area_km2,
        }

    return app


app = create_app()
