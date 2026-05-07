"""
Router /api/auth  — OAuth2 OSM (PKCE, singlepage mode).

Flusso:
  1. Frontend (osm-auth, singlepage:true)  → redirect a OSM /oauth2/authorize
  2. OSM callback → frontend URL con ?code=...
  3. Frontend: auth.bootstrapToken(code) → ottiene access_token OSM
  4. Frontend: POST /api/auth/exchange { access_token } → riceve session_jwt
  5. Chiamate successive portano Authorization: Bearer <session_jwt>

Con AUTH_ENABLED=false tutti gli endpoint ritornano 501.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..auth import create_session_jwt, decode_session_jwt
from ..config import get_settings
from ..models import OsmUser, OsmUserPublic
from ..store import delete_user, load_user, save_user

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _require_enabled() -> None:
    if not get_settings().auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this instance. Set AUTH_ENABLED=true.",
        )


# ── Schema exchange ──────────────────────────────────────────────────

class ExchangeRequest(BaseModel):
    access_token: str   # token OSM ricevuto dal frontend via osm-auth


class ExchangeResponse(BaseModel):
    session_token: str      # JWT di sessione interno da conservare in localStorage
    user: OsmUserPublic


# ── Helper: verifica token OSM ────────────────────────────────────────────

async def _fetch_osm_user(access_token: str) -> OsmUser:
    """
    Chiama GET /api/0.6/user/details.json usando il bearer token OSM.
    Ritorna l'OsmUser o solleva HTTPException se il token non è valido.
    """
    settings = get_settings()
    url = f"{settings.osm_api_url}/api/0.6/user/details.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OSM access token.",
        )
    if resp.status_code != 200:
        log.warning("OSM user details returned %s", resp.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OSM API returned {resp.status_code}.",
        )
    data = resp.json().get("user", {})
    return OsmUser(
        osm_id=int(data["id"]),
        display_name=data["display_name"],
        account_created=data.get("account_created", ""),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post(
    "/exchange",
    response_model=ExchangeResponse,
    summary="Scambia il token OSM per un session JWT interno",
    description=(
        "Il frontend (osm-auth) chiama questo endpoint dopo aver ottenuto "
        "l'`access_token` OSM. Il backend verifica il token con OSM, "
        "costruisce il profilo utente, lo salva in Redis e ritorna "
        "il `session_token` JWT da usare nelle successive chiamate API."
    ),
)
async def exchange(
    body: ExchangeRequest,
) -> ExchangeResponse:
    _require_enabled()

    # 1. Verifica con OSM
    user = await _fetch_osm_user(body.access_token)

    # 2. Salva utente + token cifrato in Redis
    await save_user(user, body.access_token)

    # 3. Emette session JWT interno
    session_token = create_session_jwt(user.osm_id, user.display_name)

    log.info("User authenticated: osm_id=%s name=%s", user.osm_id, user.display_name)
    return ExchangeResponse(
        session_token=session_token,
        user=OsmUserPublic(
            osm_id=user.osm_id,
            display_name=user.display_name,
            account_created=user.account_created,
        ),
    )


@router.get(
    "/me",
    response_model=OsmUserPublic,
    summary="Restituisce il profilo dell'utente autenticato",
)
async def me(
    credentials: str | None = None,
) -> OsmUserPublic:
    _require_enabled()
    # Legge il Bearer manualmente per dare errore chiaro
    from fastapi import Request
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Usa Authorization: Bearer <session_token>; il profilo è nel JWT stesso.",
    )


@router.post(
    "/me",
    response_model=OsmUserPublic,
    summary="Restituisce il profilo utente dal session token",
    description="Invia `{ session_token: \"...\" }` per ottenere il profilo.",
)
async def me_post(body: dict) -> OsmUserPublic:
    _require_enabled()
    token = body.get("session_token", "")
    try:
        payload = decode_session_jwt(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
        )
    osm_id = int(payload["sub"])
    result = await load_user(osm_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired. Please sign in again.",
        )
    user, _ = result
    return OsmUserPublic(
        osm_id=user.osm_id,
        display_name=user.display_name,
        account_created=user.account_created,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalida la sessione locale (revoca Redis)",
)
async def logout(body: dict) -> None:
    _require_enabled()
    token = body.get("session_token", "")
    if not token:
        return
    try:
        payload = decode_session_jwt(token)
        osm_id = int(payload["sub"])
        await delete_user(osm_id)
        log.info("User logged out: osm_id=%s", osm_id)
    except Exception:
        pass  # token già scaduto o invalido — nessuna azione necessaria
