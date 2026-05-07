"""
Utilità geometriche — calcolo area AOI.

Usa solo la stdlib + math per evitare dipendenze pesanti qui.
Per la produzione si potrebbe usare pyproj o shapely.
"""
from __future__ import annotations

import math
from typing import Any


def _ring_area_m2(coords: list[list[float]]) -> float:
    """
    Calcola l'area in m² di un anello di coordinate geografiche (lon, lat)
    usando la formula dell'area sferica (metodo dell'haversine generalizzato).
    Implementazione basata su geojson-area (MapBox).
    """
    n = len(coords)
    if n < 3:
        return 0.0

    EARTH_RADIUS = 6_378_137.0  # WGS-84 raggio equatoriale in m

    total = 0.0
    for i in range(n):
        p1 = coords[i]
        p2 = coords[(i + 1) % n]
        total += math.radians(p2[0] - p1[0]) * (
            2 + math.sin(math.radians(p1[1])) + math.sin(math.radians(p2[1]))
        )

    return abs(total * EARTH_RADIUS * EARTH_RADIUS / 2)


def compute_area_km2(geometry: dict[str, Any]) -> float:
    """
    Calcola l'area in km² di una geometry GeoJSON (Polygon o MultiPolygon).
    """
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    total_m2 = 0.0

    if geom_type == "Polygon":
        # coords[0] = outer ring; coords[1..] = holes (area negativa)
        if coords:
            total_m2 += _ring_area_m2(coords[0])
            for hole in coords[1:]:
                total_m2 -= _ring_area_m2(hole)

    elif geom_type == "MultiPolygon":
        for polygon_coords in coords:
            if polygon_coords:
                total_m2 += _ring_area_m2(polygon_coords[0])
                for hole in polygon_coords[1:]:
                    total_m2 -= _ring_area_m2(hole)

    return total_m2 / 1_000_000  # → km²
