"""
Client per la raw-data-api di HOT (https://github.com/hotosm/raw-data-api).

Flusso (asincrono):
  1. POST /snapshot/  → riceve { task_id }
  2. GET  /tasks/status/{task_id} → polling finché status != PENDING/STARTED
  3. Ritorna l'URL del file o il GeoJSON inline

Documentazione: https://api-prod.raw-data.hotosm.org/v1/docs
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .config import get_settings

log = logging.getLogger(__name__)

# Intervallo di polling HOT (secondi)
_POLL_INTERVAL = 4
_MAX_POLLS     = 60   # 4 min max


class HotRawDataError(RuntimeError):
    pass


async def request_snapshot(
    geometry: dict[str, Any],
    export_format: str = "geojson",
) -> dict[str, Any]:
    """
    Avvia uno snapshot sulla raw-data-api HOT e attende il completamento.

    Params
    ------
    geometry     GeoJSON geometry dict (Polygon / MultiPolygon)
    export_format  "geojson" | "gpkg" | "fgdb" | "shp"
                   HOT supporta geojson e gpkg natively.
                   Per fgdb/duckdb il worker riceve il gpkg e lo converte localmente.

    Returns
    -------
    dict con chiave "download_url" o "geojson" (dipende dal formato)
    """
    settings = get_settings()

    # HOT raw-data-api vuole il file_type come parametro body
    hot_format = _map_format(export_format)

    payload: dict[str, Any] = {
        "geometry": geometry,
        "filters": {
            "tags": {
                "point": {},
                "line": {},
                "polygon": {},
                "all_geometry": {
                    "join_or": {
                        "osm_id": []   # vuoto = tutti gli oggetti nell'AOI
                    }
                }
            }
        },
        "geometryType": ["point", "line", "polygon"],
        "fileName": "osm_broker_export",
        "outputType": hot_format,
        "freeform": True,
    }

    async with httpx.AsyncClient(timeout=settings.hot_api_timeout) as client:
        # ── 1. Avvia il job ──────────────────────────────────────────
        log.info("Requesting HOT snapshot (format=%s)", hot_format)
        resp = await client.post(
            f"{settings.hot_raw_data_api_url}/snapshot/",
            json=payload,
        )
        if resp.status_code not in (200, 202):
            raise HotRawDataError(
                f"HOT API error {resp.status_code}: {resp.text[:400]}"
            )
        task_id: str = resp.json()["task_id"]
        log.info("HOT task_id=%s", task_id)

        # ── 2. Polling finché non è pronto ──────────────────────────
        for attempt in range(_MAX_POLLS):
            await asyncio.sleep(_POLL_INTERVAL)
            status_resp = await client.get(
                f"{settings.hot_raw_data_api_url}/tasks/status/{task_id}"
            )
            if status_resp.status_code != 200:
                raise HotRawDataError(
                    f"Status check failed {status_resp.status_code}"
                )
            data = status_resp.json()
            state: str = data.get("status", "PENDING")
            log.debug("HOT task %s → %s (attempt %d)", task_id, state, attempt + 1)

            if state == "SUCCESS":
                result: dict[str, Any] = data.get("result", {})
                return result

            if state in ("FAILURE", "REVOKED"):
                raise HotRawDataError(
                    f"HOT task failed: {data.get('result', 'unknown error')}"
                )
            # PENDING / STARTED → continue polling

        raise HotRawDataError("HOT snapshot timed out after polling limit")


def _map_format(export_format: str) -> str:
    """Mappa il formato interno sul tipo accettato da HOT raw-data-api."""
    mapping = {
        "gpkg":    "gpkg",
        "geojson": "geojson",
        # Per questi due scarichiamo prima il gpkg e convertiamo localmente
        "fgdb":    "gpkg",
        "duckdb":  "gpkg",
    }
    return mapping.get(export_format, "gpkg")
