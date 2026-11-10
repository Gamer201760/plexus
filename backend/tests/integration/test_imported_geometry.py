import json
from pathlib import Path

import pytest
from tests.storage import atlas_repository
from tests.unit.repository.files.test_json_atlas import inside, rings

from app.repository.files.atlas import JsonAtlasRepository

ALTAI = "01000000"
BARNAUL = "01701000001"


@pytest.fixture(scope="module")
def imported_sources(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("archived-sources")
    reader = atlas_repository().reader
    rows = reader.rows("SELECT path,body FROM plexus_atlas.documents", {})
    for row in rows:
        path = root / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(row["body"])
    return root


@pytest.fixture(scope="module")
def atlas(imported_sources: Path) -> JsonAtlasRepository:
    return JsonAtlasRepository(imported_sources)


def test_projection_reproduces_every_exported_region_vertex(atlas: JsonAtlasRepository, imported_sources: Path) -> None:
    boundaries = json.loads((imported_sources / "geo/regions.json").read_text(encoding="utf-8"))
    paths = {shape.name: shape.path for shape in atlas.geo().shapes}
    frame = atlas.frame()
    for feature in boundaries["features"]:
        geometry = feature["geometry"]
        polygons = (
            geometry["coordinates"]
            if geometry["type"] == "MultiPolygon"
            else [geometry["coordinates"]]
        )
        lon, lat = polygons[0][0][0][:2]
        first = rings(paths[feature["properties"]["name"]])[0][0]
        assert frame.place(lon, lat) == first


def test_barnaul_lands_inside_altai_krai(atlas: JsonAtlasRepository) -> None:
    barnaul = atlas.points()[BARNAUL]
    shape = next(shape for shape in atlas.geo().shapes if shape.id == ALTAI)

    assert any(inside((barnaul.x, barnaul.y), ring) for ring in rings(shape.path))
    assert atlas.frame().place(83.78, 53.348) == pytest.approx((barnaul.x, barnaul.y), abs=0.2)


def test_boundaries_join_ids_and_normalize_longitudes(atlas: JsonAtlasRepository) -> None:
    boundaries = atlas.boundaries()
    drawn = {shape.id for shape in atlas.geo().shapes}

    assert {shape.id for shape in boundaries} == drawn
    assert atlas.boundaries() is boundaries
    for shape in boundaries:
        min_lon, min_lat, max_lon, max_lat = shape.bounds
        assert 10 < min_lon <= max_lon < 200
        assert 40 < min_lat <= max_lat < 85
        assert all(point[0] >= 0 for polygon in shape.polygons for ring in polygon for point in ring)


def test_real_links_keep_unknown_values_null(atlas: JsonAtlasRepository) -> None:
    links = atlas.links()

    assert len(links) == 46487
    assert any(link.season is None for link in links)
    assert any(link.km is None for link in links)
    assert all(link.km != 0 for link in links if link.km is not None)


def test_overview_geometry_covers_every_region_with_fewer_vertices(
    atlas: JsonAtlasRepository,
) -> None:
    shapes = atlas.geo().shapes
    assert all(shape.path_low and shape.path_low.startswith("M") for shape in shapes)
    full = sum(shape.path.count("L") for shape in shapes)
    overview = sum((shape.path_low or "").count("L") for shape in shapes)
    assert overview < full / 2

