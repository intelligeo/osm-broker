"""
Modelli Pydantic condivisi tra API layer e worker.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────

class ExportFormat(str, Enum):
    gpkg    = "gpkg"       # GeoPackage (OGC)
    geojson = "geojson"    # GeoJSON
    fgdb    = "fgdb"       # Esri File Geodatabase via GDAL/OpenFileGDB
    duckdb  = "duckdb"     # DuckDB + GeoParquet


class JobStatus(str, Enum):
    idle       = "idle"
    pending    = "pending"
    processing = "processing"
    ready      = "ready"
    failed     = "failed"


# ── AOI ───────────────────────────────────────────────────────────────────

class AOIGeometry(BaseModel):
    type: str
    coordinates: list[Any]

    @field_validator("type")
    @classmethod
    def validate_geom_type(cls, v: str) -> str:
        if v not in ("Polygon", "MultiPolygon"):
            raise ValueError("Only Polygon or MultiPolygon AOIs are supported")
        return v


class AOIFeature(BaseModel):
    type: str = "Feature"
    geometry: AOIGeometry
    properties: dict[str, Any] = Field(default_factory=dict)


# ── Request / Response ────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    aoi: AOIFeature
    format: ExportFormat = ExportFormat.gpkg
    symbology: bool = True


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.pending
    format: ExportFormat = ExportFormat.gpkg
    symbology: bool = True
    area_km2: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    download_url: str | None = None
    error_message: str | None = None
    progress: int | None = None      # 0–100

    # Campi interni — non esposti nelle risposte pubbliche
    output_path: str | None = None   # path ZIP sul server

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    model_config = {"use_enum_values": True}
