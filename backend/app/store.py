"""
Livello di persistenza: ogni Job è serializzato come JSON in Redis.
Key:   job:{job_id}
TTL:   settings.job_ttl_seconds  (24h di default)
"""
from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

from .config import get_settings
from .models import Job, OsmUser

log = logging.getLogger(__name__)


def _make_client() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


# Singleton lazy — creato al primo import, riusato per tutta la vita del processo
_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


# ── CRUD ──────────────────────────────────────────────────────────────────

def _key(job_id: str) -> str:
    return f"job:{job_id}"


async def save_job(job: Job) -> None:
    settings = get_settings()
    r = get_redis()
    await r.set(
        _key(job.id),
        job.model_dump_json(),
        ex=settings.job_ttl_seconds,
    )


async def load_job(job_id: str) -> Job | None:
    r = get_redis()
    raw = await r.get(_key(job_id))
    if raw is None:
        return None
    try:
        return Job.model_validate(json.loads(raw))
    except Exception:
        log.exception("Failed to deserialize job %s", job_id)
        return None


async def push_job_queue(job_id: str) -> None:
    """Aggiunge il job_id alla coda FIFO consumata dal worker."""
    r = get_redis()
    await r.rpush("osm_broker:queue", job_id)


async def ping_redis() -> bool:
    try:
        r = get_redis()
        return await r.ping()
    except Exception:
        return False


# ── User store ────────────────────────────────────────────────────────────

def _user_key(osm_id: int) -> str:
    return f"user:{osm_id}"


async def save_user(user: OsmUser, access_token: str) -> None:
    """Salva profilo OSM + token cifrato in Redis."""
    from .auth import encrypt_token  # import locale per evitare cicli
    settings = get_settings()
    r = get_redis()
    data = user.model_dump()
    data["_access_token"] = encrypt_token(access_token)
    await r.set(
        _user_key(user.osm_id),
        json.dumps(data),
        ex=settings.session_ttl_seconds,
    )


async def load_user(osm_id: int) -> tuple[OsmUser, str] | None:
    """Ritorna (OsmUser, access_token) o None se non trovato."""
    from .auth import decrypt_token
    r = get_redis()
    raw = await r.get(_user_key(osm_id))
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        token_enc = data.pop("_access_token", None)
        user = OsmUser.model_validate(data)
        token = decrypt_token(token_enc) if token_enc else ""
        return user, token
    except Exception:
        log.exception("Failed to deserialize user %s", osm_id)
        return None


async def delete_user(osm_id: int) -> None:
    r = get_redis()
    await r.delete(_user_key(osm_id))
