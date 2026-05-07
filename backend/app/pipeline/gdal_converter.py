"""
Converter GDAL/OGR — trasforma un GeoPackage sorgente nel formato finale.

Formati supportati:
  gpkg    → nessuna conversione (già pronto)
  geojson → ogr2ogr GeoJSON
  fgdb    → ogr2ogr OpenFileGDB  (driver OpenFileGDB incluso in GDAL 3.6+)
  duckdb  → gestito da duckdb_converter.py

Restituisce un dict  { layer_name: Path }
dove ogni Path è il file/cartella prodotto.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

# Mapping formato → driver OGR
_OGR_DRIVER = {
    "gpkg":    "GPKG",
    "geojson": "GeoJSON",
    "fgdb":    "OpenFileGDB",
}

# Estensione output per ogni driver
_EXT = {
    "GPKG":        ".gpkg",
    "GeoJSON":     ".geojson",
    "OpenFileGDB": ".gdb",
}


def convert(src_gpkg: Path, output_dir: Path, target_format: str) -> list[Path]:
    """
    Converte `src_gpkg` nel formato `target_format` dentro `output_dir`.

    Per il formato gpkg: copia direttamente senza re-conversione.
    Per fgdb: produce una cartella .gdb per ogni layer.
    Per geojson: un file .geojson per layer.

    Returns
    -------
    Lista di Path prodotti (file o cartelle).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if target_format == "gpkg":
        out = output_dir / src_gpkg.name
        shutil.copy2(src_gpkg, out)
        log.info("gpkg: copied %s → %s", src_gpkg, out)
        return [out]

    if target_format == "duckdb":
        # delegato a duckdb_converter
        raise ValueError("DuckDB conversion must use duckdb_converter.convert()")

    driver = _OGR_DRIVER.get(target_format)
    if driver is None:
        raise ValueError(f"Unsupported target format: {target_format!r}")

    # Elenca i layer nel GeoPackage sorgente
    layers = _list_layers(src_gpkg)
    if not layers:
        log.warning("No layers found in %s", src_gpkg)
        return []

    outputs: list[Path] = []
    ext = _EXT[driver]

    for layer in layers:
        safe_name = _safe(layer)

        if driver == "OpenFileGDB":
            # FileGDB è una *cartella* — una per layer per semplicità
            out_path = output_dir / f"{safe_name}{ext}"
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path = output_dir / f"{safe_name}{ext}"

        log.info("ogr2ogr: layer=%s driver=%s → %s", layer, driver, out_path)
        _ogr2ogr(src_gpkg, out_path, layer, driver)
        outputs.append(out_path)

    return outputs


def _list_layers(gpkg: Path) -> list[str]:
    """Usa ogrinfo per elencare i layer nel GeoPackage."""
    result = subprocess.run(
        ["ogrinfo", "-al", "-so", str(gpkg)],
        capture_output=True, text=True, check=False,
    )
    layers: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("Layer name:"):
            layers.append(line.split(":", 1)[1].strip())
    return layers


def _ogr2ogr(src: Path, dst: Path | str, layer: str, driver: str) -> None:
    """Esegue ogr2ogr. Lancia subprocess.CalledProcessError se fallisce."""
    cmd = [
        "ogr2ogr",
        "-f", driver,
        str(dst),
        str(src),
        layer,
        "-overwrite",
        "-lco", "ENCODING=UTF-8",
    ]
    # FileGDB extra options
    if driver == "OpenFileGDB":
        cmd += ["-lco", "FEATURE_DATASET=OSM", "-nlt", "PROMOTE_TO_MULTI"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"ogr2ogr failed for layer {layer!r}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def _safe(name: str) -> str:
    """Sostituisce caratteri non ammessi nel nome file."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
