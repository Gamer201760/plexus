from collections.abc import Iterator
from pathlib import Path

from app.domain.projection import VIEW_BOX, SvgFrame, lambert
from app.repository.files.json_values import Json, obj, objects, read_json, text
from app.usecase.dto import GeoLayer, RegionShape

BOUNDARIES = "geo/regions.json"
REGION_PATHS = "geo/region-paths.json"


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


def boundary_frame(data_dir: Path) -> SvgFrame:
    features = objects(obj(read_json(data_dir, BOUNDARIES)).get("features"))
    return SvgFrame.enclosing(
        lambert(lon, lat)
        for feature in features
        for lon, lat in _positions(obj(feature.get("geometry")).get("coordinates"))
    )


def region_layer(data_dir: Path) -> GeoLayer:
    document = obj(read_json(data_dir, REGION_PATHS))
    shapes = []
    for row in objects(document.get("regions")):
        region_id, name, path = text(row, "id"), text(row, "name"), text(row, "path")
        if region_id and path:
            shapes.append(RegionShape(id=region_id, name=name or region_id, path=path))
    return GeoLayer(
        view_box=VIEW_BOX,
        shapes=shapes,
        source=text(document, "source"),
        source_url=text(document, "source_url"),
    )
