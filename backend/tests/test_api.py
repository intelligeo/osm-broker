"""
Test suite per il backend OSM Broker.
Eseguire con: pytest backend/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import zipfile

from app.main import app
from app.utils.geo import compute_area_km2

client = TestClient(app)


# ── Geo utils ─────────────────────────────────────────────────────────────

def test_area_square_degree():
    """Un quadrato ~1°×1° attorno a Zurigo ≈ 7700 km²."""
    geom = {
        "type": "Polygon",
        "coordinates": [[
            [8.0, 47.0], [9.0, 47.0], [9.0, 48.0], [8.0, 48.0], [8.0, 47.0]
        ]],
    }
    area = compute_area_km2(geom)
    assert 7500 < area < 8000, f"Unexpected area: {area}"


def test_area_small_polygon():
    """Un poligono piccolo (Berna centro) < 2 km²."""
    geom = {
        "type": "Polygon",
        "coordinates": [[
            [7.438, 46.949], [7.452, 46.949],
            [7.452, 46.958], [7.438, 46.958], [7.438, 46.949]
        ]],
    }
    area = compute_area_km2(geom)
    assert area < 2.0, f"Unexpected area: {area}"


def test_area_multipolygon():
    """MultiPolygon: somma delle aree dei sotto-poligoni."""
    geom = {
        "type": "MultiPolygon",
        "coordinates": [
            [[[8.0, 47.0], [8.01, 47.0], [8.01, 47.01], [8.0, 47.01], [8.0, 47.0]]],
            [[[9.0, 47.0], [9.01, 47.0], [9.01, 47.01], [9.0, 47.01], [9.0, 47.0]]],
        ],
    }
    area = compute_area_km2(geom)
    assert area > 0, "MultiPolygon area should be > 0"


# ── API endpoints ─────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "status" in r.json()


def test_version():
    r = client.get("/api/version")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert data["auth_enabled"] is False
    assert data["max_area_km2"] == 500.0


def test_create_job_too_large():
    """AOI > 500 km² → 400."""
    payload = {
        "aoi": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]
                ]],
            },
            "properties": {},
        },
        "format": "gpkg",
        "symbology": True,
    }
    r = client.post("/api/jobs", json=payload)
    assert r.status_code == 400
    assert "exceeds" in r.json()["detail"].lower()


def test_create_job_invalid_geom_type():
    """Geometry type non supportato → 422."""
    payload = {
        "aoi": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [8.5, 47.3]},
            "properties": {},
        },
        "format": "gpkg",
        "symbology": False,
    }
    r = client.post("/api/jobs", json=payload)
    assert r.status_code == 422


def test_get_nonexistent_job():
    r = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_auth_login_not_implemented():
    r = client.get("/api/auth/login")
    assert r.status_code == 501


# ── Packager ─────────────────────────────────────────────────────────────

def test_packager_creates_zip():
    """Il packager crea uno ZIP con README e cartella data/."""
    from app.pipeline.packager import package

    with tempfile.TemporaryDirectory() as tmp:
        # File dummy da includere
        dummy = Path(tmp) / "roads.gpkg"
        dummy.write_bytes(b"fake gpkg content")

        zip_path = package(
            data_files=[dummy],
            job_id="test-job-1234",
            export_format="gpkg",
            area_km2=42.5,
            output_dir=tmp,
            symbology=False,
        )

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert any("README.txt" in n for n in names)
        assert any("roads.gpkg" in n for n in names)


def test_packager_with_qml(tmp_path):
    """Con symbology=True e qml_dir valido includde i .qml."""
    from app.pipeline.packager import package

    # Crea .qml dummy
    qml_dir = tmp_path / "styles"
    qml_dir.mkdir()
    (qml_dir / "roads.qml").write_text("<qml/>")
    (qml_dir / "buildings.qml").write_text("<qml/>")

    dummy_gpkg = tmp_path / "roads.gpkg"
    dummy_gpkg.write_bytes(b"fake")

    zip_path = package(
        data_files=[dummy_gpkg],
        job_id="test-qml-5678",
        export_format="gpkg",
        area_km2=10.0,
        output_dir=str(tmp_path),
        symbology=True,
        qml_dir=str(qml_dir),
    )

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert any("roads.qml" in n for n in names)
    assert any("buildings.qml" in n for n in names)

