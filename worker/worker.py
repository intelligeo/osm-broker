"""
OSM Broker — Background Worker (pipeline completa)

Loop BLPOP:
  1. Preleva job_id dalla coda Redis
  2. status → processing
  3. HOT raw-data-api snapshot → URL file gpkg
  4. Download gpkg in work_dir locale
  5. Conversione formato: gpkg / geojson / fgdb / duckdb
  6. ZIP + .qml SwissMap (se symbology=True)
  7. status → ready  (o failed + messaggio)
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# Permette import da backend/app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings                          # noqa: E402
from app.hot_client import HotRawDataError, request_snapshot  # noqa: E402
from app.models import JobStatus                             # noqa: E402
from app.pipeline import (                                   # noqa: E402
    download_file,
    duckdb_convert,
    gdal_convert,
    package,
)
from app.store import get_redis, load_job, save_job          # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("worker")

QUEUE_KEY = "osm_broker:queue"


# ── Pipeline ──────────────────────────────────────────────────────────────

async def process_job(job_id: str) -> None:
    settings = get_settings()
    job = await load_job(job_id)
    if job is None:
        log.warning("Job %s not found in Redis — skipping", job_id)
        return

    log.info(
        "▶ Job %s  format=%s  area=%.1f km²  symbology=%s",
        job_id, job.format, job.area_km2, job.symbology,
    )

    # Directory di lavoro temporanea (rimossa al termine)
    work_dir = Path(settings.output_dir) / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Status: processing ───────────────────────────────────────
        job.status = JobStatus.processing
        job.progress = 5
        job.touch()
        await save_job(job)

        # ─────────────────────────────────────────────────────────────
        # STEP 1 — HOT raw-data-api snapshot
        # Il job porta la geometry serializzata nel campo aoi (ma il Job
        # in Redis non la include per evitare duplicazione di dati grandi).
        # La geometry è passata dal router al momento della creazione del
        # job attraverso un secondo key Redis: "geo:{job_id}".
        # ─────────────────────────────────────────────────────────────
        geometry = await _load_geometry(job_id)
        if geometry is None:
            raise RuntimeError("AOI geometry not found in Redis (key geo:{job_id})")

        log.info("Step 1/4: Requesting HOT snapshot…")
        hot_result = await request_snapshot(geometry, job.format)
        download_url: str = hot_result.get("download_url") or hot_result.get("url") or ""
        if not download_url:
            raise RuntimeError(f"HOT API returned no download URL: {hot_result}")

        job.progress = 30
        await save_job(job)

        # ─────────────────────────────────────────────────────────────
        # STEP 2 — Download file sorgente (sempre gpkg da HOT)
        # ─────────────────────────────────────────────────────────────
        log.info("Step 2/4: Downloading source file…")
        src_gpkg = await download_file(
            url=download_url,
            dest_dir=str(work_dir / "source"),
            filename="source.gpkg",
        )

        job.progress = 55
        await save_job(job)

        # ─────────────────────────────────────────────────────────────
        # STEP 3 — Conversione formato
        # ─────────────────────────────────────────────────────────────
        log.info("Step 3/4: Converting to %s…", job.format)
        convert_dir = work_dir / "converted"
        data_files: list[Path]

        if job.format == "duckdb":
            data_files = duckdb_convert(src_gpkg, convert_dir)
        else:
            data_files = gdal_convert(src_gpkg, convert_dir, job.format)

        if not data_files:
            raise RuntimeError("Conversion produced no output files")

        job.progress = 80
        await save_job(job)

        # ─────────────────────────────────────────────────────────────
        # STEP 4 — Packaging ZIP + .qml
        # ─────────────────────────────────────────────────────────────
        log.info("Step 4/4: Packaging ZIP…")
        zip_path = package(
            data_files=data_files,
            job_id=job_id,
            export_format=job.format,
            area_km2=job.area_km2,
            output_dir=str(settings.output_dir),
            symbology=job.symbology,
            qml_dir=settings.qml_dir,
        )

        job.progress = 100
        job.status = JobStatus.ready
        job.output_path = str(zip_path)
        # URL pubblico costruito dal backend su /api/jobs/{id}/download
        job.download_url = f"/api/jobs/{job_id}/download"
        job.touch()
        await save_job(job)

        log.info("✔ Job %s → READY  (%s)", job_id, zip_path)

    except (HotRawDataError, RuntimeError, Exception) as exc:
        log.exception("✖ Job %s FAILED: %s", job_id, exc)
        job.status = JobStatus.failed
        job.error_message = _friendly_error(exc)
        job.touch()
        await save_job(job)

    finally:
        # Pulisce i file intermedi, mantiene solo il ZIP finale
        _cleanup(work_dir)


async def _load_geometry(job_id: str) -> dict | None:
    """Carica la geometry AOI salvata con key 'geo:{job_id}' in Redis."""
    import json
    r = get_redis()
    raw = await r.get(f"geo:{job_id}")
    if raw is None:
        return None
    return json.loads(raw)


def _cleanup(work_dir: Path) -> None:
    """Rimuove la directory di lavoro temporanea."""
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass


def _friendly_error(exc: Exception) -> str:
    """Produce un messaggio utente leggibile dall'eccezione."""
    msg = str(exc)
    if "timeout" in msg.lower():
        return "L'area richiesta è troppo complessa o grande. Prova a ridurre l'AOI."
    if "ogr2ogr" in msg.lower() or "gdal" in msg.lower():
        return f"Errore di conversione GDAL: {msg[:200]}"
    if "Connection" in msg or "redis" in msg.lower():
        return "Errore di connessione interna. Riprova tra qualche istante."
    return msg[:300]


# ── Main loop ─────────────────────────────────────────────────────────────

async def run_worker(concurrency: int = 2) -> None:
    settings = get_settings()
    log.info("Worker avviato. Redis: %s  concurrency: %d", settings.redis_url, concurrency)

    r = get_redis()
    semaphore = asyncio.Semaphore(concurrency)

    async def handle(job_id: str) -> None:
        async with semaphore:
            await process_job(job_id)

    log.info("In ascolto su coda: %s", QUEUE_KEY)
    while True:
        item = await r.blpop(QUEUE_KEY, timeout=0)
        if item is None:
            continue
        _, job_id = item
        asyncio.create_task(handle(job_id))


if __name__ == "__main__":
    settings = get_settings()
    concurrency = int(os.environ.get("WORKER_CONCURRENCY", "2"))
    asyncio.run(run_worker(concurrency))
