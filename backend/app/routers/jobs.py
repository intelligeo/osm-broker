"""
Router /api/jobs

POST   /api/jobs                   — crea un job, lo mette in coda
GET    /api/jobs/{id}              — polling stato
GET    /api/jobs/{id}/download     — scarica lo ZIP (solo se status=ready)
"""
from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..auth import OptionalUser
from ..config import get_settings
from ..models import ExportRequest, Job, JobStatus
from ..store import get_redis, load_job, push_job_queue, save_job
from ..utils.geo import compute_area_km2

log = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])
limiter = Limiter(key_func=get_remote_address)


# ── POST /jobs ─────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new export job",
    description=(
        "Valida l'AOI (massimo `MAX_AREA_KM2` km²), crea un Job in Redis "
        "e lo inserisce nella coda FIFO consumata dal worker. "
        "Ritorna immediatamente con status **pending**.\n\n"
        "**Rate limit**: 10 richieste ogni 60 secondi per IP."
    ),
)
@limiter.limit("10/minute")
async def create_job(
    request: Request,
    req: ExportRequest,
    _user: dict | None = OptionalUser,
) -> Job:
    settings = get_settings()

    # ── Validazione area ─────────────────────────────────────────────
    area_km2 = compute_area_km2(req.aoi.geometry.model_dump())
    if area_km2 > settings.max_area_km2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"AOI area {area_km2:.1f} km² exceeds the maximum "
                f"allowed {settings.max_area_km2} km²."
            ),
        )

    # ── Crea il Job ──────────────────────────────────────────────────
    osm_id: int | None = int(_user["sub"]) if _user else None
    job = Job(
        format=req.format,
        symbology=req.symbology,
        area_km2=round(area_km2, 2),
        status=JobStatus.pending,
        requested_by=osm_id,
    )
    await save_job(job)

    # ── Salva geometry AOI in Redis (consumata dal worker) ───────────
    r = get_redis()
    await r.set(
        f"geo:{job.id}",
        json.dumps(req.aoi.geometry.model_dump()),
        ex=settings.job_ttl_seconds,
    )

    # ── Mette il job_id nella coda FIFO ─────────────────────────────
    await push_job_queue(job.id)

    log.info(
        "Job %s queued (format=%s, area=%.1f km²)",
        job.id, req.format, area_km2,
    )
    return job


# ── GET /jobs/{id} ─────────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    response_model=Job,
    summary="Poll job status",
    description=(
        "Ritorna lo stato corrente del job. Eseguire il polling ogni 3–5 secondi "
        "finché `status` non è `ready` o `failed`. "
        "Il job scade dopo 24 ore dalla creazione."
    ),
)
async def get_job(
    job_id: str,
    _user: dict | None = OptionalUser,
) -> Job:
    job = await load_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id!r} not found (may have expired)",
        )
    return job


# ── GET /jobs/{id}/download ────────────────────────────────────────────────

@router.get(
    "/{job_id}/download",
    summary="Download the export ZIP",
    description=(
        "Scarica il file ZIP contenente i geodati nel formato richiesto "
        "e, opzionalmente, i file `.qml` di simbologia SwissMap per QGIS. "
        "Disponibile solo quando `status == ready`."
    ),
    responses={
        200: {"description": "File ZIP scaricabile", "content": {"application/zip": {}}},
        404: {"description": "Job non trovato"},
        409: {"description": "Job non ancora completato"},
        410: {"description": "File di output non più disponibile"},
    },
)
async def download_job(
    job_id: str,
    _user: dict | None = OptionalUser,
) -> FileResponse:
    job = await load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ownership check: se authè attiva solo il proprietario (o admin) può scaricare
    settings = get_settings()
    if settings.auth_enabled and job.requested_by is not None:
        current_id = int(_user["sub"]) if _user else None
        if current_id != job.requested_by:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to download this job.",
            )

    if job.status != JobStatus.ready:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is not ready (current status: {job.status})",
        )
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Output file no longer available",
        )
    filename = f"osm_broker_{job.id[:8]}_{job.format}.zip"
    return FileResponse(
        path=job.output_path,
        media_type="application/zip",
        filename=filename,
    )