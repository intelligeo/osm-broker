"""
Downloader — scarica il file prodotto dalla HOT raw-data-api
(o qualsiasi URL HTTP) in una directory di lavoro locale.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import httpx

from ..config import get_settings

log = logging.getLogger(__name__)


async def download_file(url: str, dest_dir: str, filename: str | None = None) -> Path:
    """
    Scarica `url` in `dest_dir`.

    Params
    ------
    url       URL del file da scaricare
    dest_dir  Directory di destinazione (creata se necessario)
    filename  Nome file opzionale; se None viene derivato dall'URL

    Returns
    -------
    Path del file scaricato
    """
    settings = get_settings()
    os.makedirs(dest_dir, exist_ok=True)

    if filename is None:
        filename = _derive_filename(url)

    dest = Path(dest_dir) / filename

    log.info("Downloading %s → %s", url, dest)

    async with httpx.AsyncClient(timeout=settings.hot_api_timeout, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=65_536):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        log.debug("  %.1f MB / %.1f MB (%d%%)",
                                  downloaded / 1e6, total / 1e6, pct)

    log.info("Downloaded %.2f MB → %s", dest.stat().st_size / 1e6, dest)
    return dest


def _derive_filename(url: str) -> str:
    """Ricava un nome file dall'URL, con fallback su hash."""
    path_part = url.split("?")[0].rstrip("/").split("/")[-1]
    if "." in path_part:
        return path_part
    short = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"download_{short}.bin"
