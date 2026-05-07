"""
Auth middleware — stub preparato per OAuth2 (OSM login / JWT).

Quando AUTH_ENABLED=false (default) tutti gli endpoint sono aperti.
Quando AUTH_ENABLED=true il middleware verifica il Bearer JWT.

Per attivare OAuth2 completo (Passo futuro):
  1. Imposta AUTH_ENABLED=true, OSM_OAUTH_CLIENT_ID e OSM_OAUTH_CLIENT_SECRET
  2. Implementa /api/auth/login e /api/auth/callback (già previsti come placeholder)
  3. Genera il JWT dopo la callback OSM e salvalo nel client (localStorage)
"""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings

log = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict | None:
    """
    Dependency FastAPI.

    - AUTH_ENABLED=false → ritorna None (utente anonimo, accesso libero)
    - AUTH_ENABLED=true  → valida il JWT e ritorna il payload decodificato
    """
    settings = get_settings()

    if not settings.auth_enabled:
        return None   # accesso libero

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        import jwt  # python-jose o PyJWT
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload  # type: ignore[return-value]
    except Exception as exc:
        log.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# Shorthand per endpoint che richiedono auth opzionale
OptionalUser = Depends(require_auth)
