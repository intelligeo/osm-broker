"""
Packager — assembla il file ZIP finale contenente:
  - geodati convertiti (gpkg / geojson / fgdb / duckdb + parquet)
  - file .qml SwissMap (uno per layer) se symbology=True
  - README.txt con istruzioni d'uso

Struttura ZIP risultante:
  osm_export_<job_id[:8]>/
    ├── README.txt
    ├── data/
    │   ├── roads.gpkg          (o .geojson / .gdb / .duckdb)
    │   ├── buildings.gpkg
    │   └── ...
    └── styles/                 (solo se symbology=True)
        ├── roads.qml
        ├── buildings.qml
        └── ...
"""
from __future__ import annotations

import logging
import os
import textwrap
import zipfile
from pathlib import Path

log = logging.getLogger(__name__)


def package(
    data_files: list[Path],
    job_id: str,
    export_format: str,
    area_km2: float,
    output_dir: str,
    symbology: bool = True,
    qml_dir: str | None = None,
) -> Path:
    """
    Crea il ZIP finale.

    Params
    ------
    data_files     Lista di file/cartelle da includere in data/
    job_id         UUID del job
    export_format  Stringa formato (gpkg, geojson, fgdb, duckdb)
    area_km2       Area AOI in km²
    output_dir     Directory dove salvare il ZIP
    symbology      Se True, include i file .qml
    qml_dir        Path alla cartella dei .qml; usa il default di config se None

    Returns
    -------
    Path del file ZIP creato
    """
    from ..config import get_settings
    settings = get_settings()

    if qml_dir is None:
        qml_dir = settings.qml_dir

    os.makedirs(output_dir, exist_ok=True)
    zip_name = f"osm_broker_{job_id[:8]}_{export_format}.zip"
    zip_path = Path(output_dir) / zip_name

    top = f"osm_export_{job_id[:8]}"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:

        # ── README ──────────────────────────────────────────────────
        readme = _make_readme(job_id, export_format, area_km2, symbology)
        zf.writestr(f"{top}/README.txt", readme)

        # ── Geodati ─────────────────────────────────────────────────
        for item in data_files:
            item = Path(item)
            if item.is_dir():
                # FileGDB è una cartella — va zippata ricorsivamente
                _add_dir(zf, item, arcname=f"{top}/data/{item.name}")
            elif item.is_file():
                zf.write(item, arcname=f"{top}/data/{item.name}")
            else:
                log.warning("Skipping non-existent path: %s", item)

        # ── Simbologia .qml ─────────────────────────────────────────
        if symbology:
            qml_path = Path(qml_dir)
            qml_files = sorted(qml_path.glob("*.qml")) if qml_path.exists() else []
            if not qml_files:
                log.warning("No .qml files found in %s", qml_dir)
            for qml in qml_files:
                zf.write(qml, arcname=f"{top}/styles/{qml.name}")
            log.info("Added %d .qml style files", len(qml_files))

    size_mb = zip_path.stat().st_size / 1e6
    log.info("ZIP created: %s (%.2f MB)", zip_path, size_mb)
    return zip_path


def _add_dir(zf: zipfile.ZipFile, dir_path: Path, arcname: str) -> None:
    """Aggiunge una directory intera allo ZIP mantenendo la struttura."""
    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            full = Path(root) / fname
            rel = full.relative_to(dir_path.parent)
            zf.write(full, arcname=str(rel).replace("\\", "/"))


def _make_readme(job_id: str, fmt: str, area_km2: float, symbology: bool) -> str:
    fmt_notes = {
        "gpkg":    "GeoPackage — apri direttamente in QGIS o ArcGIS Pro.",
        "geojson": "GeoJSON — caricabile in QGIS, ArcGIS, MapLibre e qualsiasi GIS moderno.",
        "fgdb":    "Esri File Geodatabase — apri in ArcGIS Pro / ArcMap.",
        "duckdb":  (
            "DuckDB con estensione spatial + GeoParquet.\n"
            "  QGIS: Layer > Add Layer > Add Vector Layer > Protocol: DuckDB\n"
            "  Python: import duckdb; con=duckdb.connect('osm_export.duckdb'); "
            "con.execute('LOAD spatial; SELECT * FROM roads LIMIT 5').fetchdf()"
        ),
    }
    styles_note = (
        "  QGIS: trascina il .qml sul layer caricato oppure\n"
        "         Layer > Properties > Symbology > Load Style > styles/<layer>.qml"
        if symbology else
        "  Simbologia non inclusa in questo export."
    )

    return textwrap.dedent(f"""\
        ╔══════════════════════════════════════════════════════╗
        ║           OSM Broker — Export Package                ║
        ╚══════════════════════════════════════════════════════╝

        Job ID     : {job_id}
        Format     : {fmt.upper()}
        Area       : {area_km2:.2f} km²
        Source     : OpenStreetMap contributors (ODbL)
        Generated  : via https://osm-broker.onrender.com

        ── Formato ──────────────────────────────────────────────
        {fmt_notes.get(fmt, '')}

        ── Stili QGIS ───────────────────────────────────────────
        {styles_note}

        ── Contenuto archivio ───────────────────────────────────
          data/      → file geodati
          styles/    → file .qml SwissMap-OSM (QGIS)
          README.txt → questo file

        ── Licenza dati ─────────────────────────────────────────
        © OpenStreetMap contributors — Open Database License (ODbL)
        https://www.openstreetmap.org/copyright
    """)
