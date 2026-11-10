from itertools import pairwise
from typing import Any

import numpy as np

from app.usecase.dto import GeoPolygon, GeoRing


def inside_ring(x: Any, y: Any, ring: GeoRing) -> Any:
    inside = np.zeros(len(x), dtype=bool)
    for (ax, ay), (bx, by) in pairwise(ring):
        if ay == by:
            continue
        crossing = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay) + ax)
        inside ^= crossing
    return inside


def inside(x: Any, y: Any, polygons: list[GeoPolygon]) -> Any:
    result = np.zeros(len(x), dtype=bool)
    for polygon in polygons:
        if not polygon:
            continue
        part = inside_ring(x, y, polygon[0])
        for hole in polygon[1:]:
            part &= ~inside_ring(x, y, hole)
        result |= part
    return result


def segments_intersect(ax: Any, ay: Any, bx: Any, by: Any, ring: GeoRing) -> Any:
    hit = np.zeros(len(ax), dtype=bool)
    for (cx, cy), (dx, dy) in pairwise(ring):
        ab_c = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        ab_d = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax)
        cd_a = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx)
        cd_b = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx)
        overlap = (np.minimum(ax, bx) <= max(cx, dx)) & (np.maximum(ax, bx) >= min(cx, dx))
        overlap &= (np.minimum(ay, by) <= max(cy, dy)) & (np.maximum(ay, by) >= min(cy, dy))
        hit |= overlap & (ab_c * ab_d <= 0) & (cd_a * cd_b <= 0)
    return hit


def region_edges(
    lon: Any, lat: Any, src: Any, dst: Any, polygons: list[GeoPolygon]
) -> tuple[Any, Any]:
    lon = np.where(lon < 0, lon + 360, lon)
    vertices = [p for polygon in polygons for ring in polygon for p in ring]
    if not vertices:
        return np.array([], dtype=int), np.array([], dtype=bool)
    west, south = np.min(vertices, axis=0)
    east, north = np.max(vertices, axis=0)
    mask = (np.minimum(lon[src], lon[dst]) <= east) & (np.maximum(lon[src], lon[dst]) >= west)
    mask &= (np.minimum(lat[src], lat[dst]) <= north) & (np.maximum(lat[src], lat[dst]) >= south)
    positions = np.flatnonzero(mask)
    a, b = src[positions], dst[positions]
    left, right = inside(lon[a], lat[a], polygons), inside(lon[b], lat[b], polygons)
    hit = left | right
    for polygon in polygons:
        for ring in polygon:
            hit |= segments_intersect(lon[a], lat[a], lon[b], lat[b], ring)
    return positions[hit], (~(left & right))[hit]
