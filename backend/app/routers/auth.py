"""
Router /api/auth  — placeholder per OAuth2 OSM.

Quando AUTH_ENABLED=false tutti gli endpoint ritornano 501 Not Implemented
con un messaggio esplicativo.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _check_enabled() -> None:
    if not get_settings().auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this instance.",
        )


@router.get("/login", summary="Redirect to OSM OAuth2 login")
async def login() -> RedirectResponse:
    _check_enabled()
    settings = get_settings()
    osm_auth_url = (
        "https://www.openstreetmap.org/oauth2/authorize"
        f"?client_id={settings.osm_oauth_client_id}"
        "&response_type=code"
        f"&redirect_uri={settings.osm_oauth_callback_url}"
        "&scope=read_prefs"
    )
    return RedirectResponse(osm_auth_url)


@router.get("/callback", summary="OSM OAuth2 callback — exchanges code for JWT")
async def callback(code: str) -> dict:
    _check_enabled()
    # TODO (Passo futuro):
    #   1. scambiare `code` con access_token su OSM
    #   2. leggere profilo utente da OSM API
    #   3. generare JWT firmato e ritornarlo al client
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth2 callback not yet implemented.",
    )


@router.get("/me", summary="Return current authenticated user info")
async def me() -> dict:
    _check_enabled()
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented.",
    )
