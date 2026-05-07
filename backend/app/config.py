import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────
    app_name: str = "OSM Broker API"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Redis ────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    job_ttl_seconds: int = 3600 * 24   # 24h — poi Redis pulisce da solo

    # ── Export limits ────────────────────────────────────────────────
    max_area_km2: float = 500.0

    # ── HOT raw-data-api ─────────────────────────────────────────────
    hot_raw_data_api_url: str = "https://api-prod.raw-data.hotosm.org/v1"
    hot_api_timeout: int = 120         # secondi — le export HOT possono essere lente

    # ── Auth ──────────────────────────────────────────────────────────
    auth_enabled: bool = False

    # Session JWT (firmato dal backend, inviato al client)
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # OSM OAuth2 — public client (no client_secret richiesto per PKCE)
    osm_oauth_client_id: str = ""
    # Callback backend (/api/auth/callback) — riceve il code da OSM
    osm_oauth_callback_url: str = "https://osm-broker.onrender.com/api/auth/callback"
    # Endpoint OSM
    osm_base_url: str = "https://www.openstreetmap.org"
    osm_api_url: str = "https://api.openstreetmap.org"

    # URL frontend a cui redirigere dopo callback con ?token=...
    frontend_url: str = "https://osm-broker.onrender.com"

    # TTL sessione utente in Redis (secondi)
    session_ttl_seconds: int = 3600   # 1h

    # ── Files ────────────────────────────────────────────────────────
    # Path alla cartella dei .qml da allegare allo ZIP
    qml_dir: str = os.path.join(
        os.path.dirname(__file__), "..", "..", "resources", "qstyles_swissmap"
    )
    output_dir: str = "/tmp/osm_broker_jobs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
