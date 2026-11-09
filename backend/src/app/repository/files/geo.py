from collections.abc import Iterator
from pathlib import Path

from app.domain.projection import VIEW_BOX, SvgFrame, lambert
from app.repository.files.json_values import Json, obj, objects, read_json, text
from app.usecase.dto import BoundaryShape, GeoLayer, GeoPolygon, GeoRing, RegionShape

BOUNDARIES = "geo/regions.json"
REGION_PATHS = "geo/region-paths.json"
LOW_PATHS = "geo/region-paths-low.json"


def _positions(value: Json) -> Iterator[tuple[float, float]]:
    if not isinstance(value, list) or not value:
        return
    if not isinstance(value[0], list):
        lon, lat = value[0], value[1] if len(value) > 1 else None
        if isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
            yield float(lon), float(lat)
        return
    for item in value:
        yield from _positions(item)


def _ring(value: Json) -> GeoRing:
    ring: GeoRing = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, list) and len(item) >= 2:
            lon, lat = item[0], item[1]
            if isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
                eastward = float(lon) + 360 if lon < 0 else float(lon)
                ring.append((eastward, float(lat)))
    return ring


def _polygons(geometry: Json) -> list[GeoPolygon]:
    shape = obj(geometry)
    coordinates = shape.get("coordinates")
    multi = isinstance(coordinates, list) and shape.get("type") == "MultiPolygon"
    raw: list[Json] = list(coordinates) if multi and isinstance(coordinates, list) else [coordinates]
    polygons: list[GeoPolygon] = []
    for polygon in raw:
        if not isinstance(polygon, list):
            continue
        kept = [ring for ring in (_ring(item) for item in polygon) if len(ring) >= 4]
        if kept:
            polygons.append(kept)
    return polygons


def _ring_area(ring: GeoRing) -> float:
    total = 0.0
    for index, (x1, y1) in enumerate(ring):
        x2, y2 = ring[(index + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def _mainland_bounds(polygons: list[GeoPolygon]) -> tuple[float, float, float, float]:
    outer = max((polygon[0] for polygon in polygons if polygon), key=_ring_area)
    xs = [point[0] for point in outer]
    ys = [point[1] for point in outer]
    return (min(xs), min(ys), max(xs), max(ys))


def boundary_layer(data_dir: Path) -> list[BoundaryShape]:
    paths = obj(read_json(data_dir, REGION_PATHS))
    ids = {text(row, "name"): text(row, "id") for row in objects(paths.get("regions"))}
    shapes: list[BoundaryShape] = []
    for feature in objects(obj(read_json(data_dir, BOUNDARIES)).get("features")):
        name = text(obj(feature.get("properties")), "name")
        region_id = ids.get(name)
        polygons = _polygons(feature.get("geometry"))
        if name is None or region_id is None or not polygons:
            continue
        shapes.append(
            BoundaryShape(
                id=region_id,
                name=name,
                bounds=_mainland_bounds(polygons),
                polygons=polygons,
            )
        )
    return shapes


def boundary_frame(data_dir: Path) -> SvgFrame:
    features = objects(obj(read_json(data_dir, BOUNDARIES)).get("features"))
    return SvgFrame.enclosing(
        lambert(lon, lat)
        for feature in features
        for lon, lat in _positions(obj(feature.get("geometry")).get("coordinates"))
    )


def region_layer(data_dir: Path) -> GeoLayer:
    document = obj(read_json(data_dir, REGION_PATHS))
    low_document = obj(read_json(data_dir, LOW_PATHS)) if (data_dir / LOW_PATHS).exists() else {}
    low_paths = {text(row, "id"): text(row, "path") for row in objects(low_document.get("regions"))}
    shapes = []
    for row in objects(document.get("regions")):
        region_id, name, path = text(row, "id"), text(row, "name"), text(row, "path")
        if region_id and path:
            shapes.append(
                RegionShape(
                    id=region_id,
                    name=name or region_id,
                    path=path,
                    path_low=low_paths.get(region_id),
                )
            )
    return GeoLayer(
        view_box=VIEW_BOX,
        shapes=shapes,
        source=text(document, "source"),
        source_url=text(document, "source_url"),
    )
