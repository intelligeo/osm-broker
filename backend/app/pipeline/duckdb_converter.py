"""
DuckDB / GeoParquet converter.

Flusso:
  GeoPackage sorgente
    └─▶ per ogni layer: legge con GDAL Python bindings (ogr)
            ↓
        Scrive in DuckDB come tabella spaziale via duckdb + spatial extension
            ↓
        Esporta anche un GeoParquet (.parquet) per ogni layer

Output: un singolo file .duckdb (con tutte le tabelle) +
        un set di file .parquet (uno per layer) — entrambi nello zip finale.
"""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)


def convert(src_gpkg: Path, output_dir: Path) -> list[Path]:
    """
    Converte `src_gpkg` in formato DuckDB + GeoParquet.

    Returns
    -------
    Lista di Path: [<job>.duckdb, layer_1.parquet, layer_2.parquet, ...]
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = output_dir / "osm_export.duckdb"
    outputs: list[Path] = [db_path]

    con = duckdb.connect(str(db_path))
    try:
        # Installa ed abilita l'estensione spaziale di DuckDB
        con.execute("INSTALL spatial; LOAD spatial;")

        layers = _list_layers_gdal(src_gpkg)
        if not layers:
            log.warning("No layers found in %s", src_gpkg)
            con.close()
            return outputs

        for layer in layers:
            safe = _safe(layer)
            parquet_path = output_dir / f"{safe}.parquet"

            log.info("DuckDB: importing layer %s", layer)

            # Legge il layer dal GeoPackage tramite l'estensione spatial di DuckDB
            # che supporta lettura diretta di GeoPackage via GDAL
            con.execute(f"""
                CREATE OR REPLACE TABLE {safe} AS
                SELECT * FROM ST_Read('{src_gpkg}', layer='{layer}');
            """)

            # Esporta in GeoParquet
            con.execute(f"""
                COPY (SELECT * FROM {safe})
                TO '{parquet_path}'
                (FORMAT PARQUET, COMPRESSION ZSTD);
            """)
            log.info("  → %s", parquet_path)
            outputs.append(parquet_path)

    finally:
        con.close()

    log.info("DuckDB: %d tables in %s", len(outputs) - 1, db_path)
    return outputs


def _list_layers_gdal(gpkg: Path) -> list[str]:
    """Elenca i layer usando le Python bindings GDAL (osgeo.ogr)."""
    try:
        from osgeo import ogr  # disponibile nell'immagine Docker GDAL
        ds = ogr.Open(str(gpkg))
        if ds is None:
            return []
        layers = [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
        ds = None
        return layers
    except ImportError:
        # Fallback: parsing stdout di ogrinfo
        import subprocess
        result = subprocess.run(
            ["ogrinfo", "-al", "-so", str(gpkg)],
            capture_output=True, text=True, check=False,
        )
        layers: list[str] = []
        for line in result.stdout.splitlines():
            if line.startswith("Layer name:"):
                layers.append(line.split(":", 1)[1].strip())
        return layers


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)
