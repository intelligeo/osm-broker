"""
Auth middleware — OAuth2 OSM + JWT di sessione interno.

Quando AUTH_ENABLED=false (default) tutti gli endpoint sono aperti.
Quando AUTH_ENABLED=true:
  - Il frontend ottiene un OSM access_token via osm-auth (PKCE singlepage).
  - Lo invia a POST /api/auth/exchange.
  - Il backend verifica il token con OSM, crea un session JWT interno e lo ritorna.
  - Ogni chiamata API successiva porta Authorization: Bearer <session_jwt>.
  - Il session JWT contiene { sub: "<osm_id>", name: "<display_name>", ... }.

Cifratura token OSM (at-rest in Redis):
  Fernet symmetric encryption; chiave derivata da JWT_SECRET_KEY.
"""
from __future__ import annotations

import base64
import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings

log = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


# ── Cifratura token OSM ──────────────────────────────────────────────────

def _get_fernet():
    """Crea un oggetto Fernet usando la JWT_SECRET_KEY come seme."""
    from cryptography.fernet import Fernet
    import hashlib
    settings = get_settings()
    key_bytes = hashlib.sha256(settings.jwt_secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_token(token: str) -> str:
    """Cifra il token OSM prima di salvarlo in Redis."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decifra il token OSM recuperato da Redis."""
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ── Session JWT ───────────────────────────────────────────────────────────────

def create_session_jwt(osm_id: int, display_name: str) -> str:
    """Emette un JWT di sessione con scadenza configurata."""
    import jwt
    from datetime import datetime, timedelta, timezone
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(osm_id),
        "name": display_name,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_session_jwt(token: str) -> dict:
    """Valida e decodifica il session JWT. Solleva eccezione se non valido."""
    import jwt
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# ── FastAPI dependency ─────────────────────────────────────────────────────────

async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict | None:
    """
    Dependency FastAPI.

    - AUTH_ENABLED=false → ritorna None (utente anonimo, accesso libero)
    - AUTH_ENABLED=true  → valida il session JWT e ritorna il payload
                           { sub: osm_id_str, name: display_name, ... }
    """
    settings = get_settings()

    if not settings.auth_enabled:
        return None

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with your OSM account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_session_jwt(credentials.credentials)
        return payload
    except Exception as exc:
        log.warning("Session JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# Shorthand per endpoint che richiedono auth opzionale
OptionalUser = Depends(require_auth)
