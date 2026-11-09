import json
import re
from pathlib import Path

import pytest

from app.domain.errors import DataUnavailable, RegionNotFound
from app.domain.transport import Confidence, Mode, Season
from app.repository.files.atlas import JsonAtlasRepository
from app.settings import DEFAULT_DATA_DIR

ALTAI = "01000000"
BARNAUL = "01701000001"
RING = re.compile(r"M([^MZ]+)Z")


def rings(path: str) -> list[list[tuple[float, float]]]:
    result = []
    for body in RING.findall(path):
        points = [tuple(float(value) for value in pair.split(",")) for pair in body.split("L")]
        result.append([(point[0], point[1]) for point in points])
    return result


def inside(point: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1], strict=True):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


@pytest.fixture(scope="module")
def atlas() -> JsonAtlasRepository:
    return JsonAtlasRepository(DEFAULT_DATA_DIR)


def test_projection_reproduces_every_exported_region_vertex(atlas: JsonAtlasRepository) -> None:
    boundaries = json.loads((DEFAULT_DATA_DIR / "geo/regions.json").read_text(encoding="utf-8"))
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


def test_real_links_keep_unknown_values_null(atlas: JsonAtlasRepository) -> None:
    links = atlas.links()

    assert len(links) == 1650
    assert any(link.season is None for link in links)
    assert any(link.km is None for link in links)
    assert all(link.km != 0 for link in links if link.km is not None)


def test_settlements_are_projected_and_cached(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    repository = JsonAtlasRepository(tmp_path, region_cache_size=1)

    first = repository.settlements("R1")
    assert repository.settlements("R1") is first
    repository.settlements("R2")

    assert repository.cached_regions() == ["R2"]
    assert first[0].x is not None and first[0].revenue_rub is None
    assert first[0].companies == 0


def test_raw_strings_map_to_typed_values(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    repository = JsonAtlasRepository(tmp_path)

    link = repository.links()[0]
    assert (link.mode, link.season, link.confidence) == (Mode.AIR, None, Confidence.LOW)
    assert (link.km, link.freq_per_week, link.vehicle) == (None, 2.5, None)
    assert repository.links()[1].season is Season.ALL
    assert repository.winter_roads()[0].road_km == 49.565
    assert repository.winter_roads()[0].closure_date is None
    assert repository.economy()["R1"].strict_revenue_rub is None
    assert [name.name for name in repository.settlement_names()] == ["Ёлкино", "Озёрный"]


def test_unknown_region_and_missing_files_fail_clearly(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    repository = JsonAtlasRepository(tmp_path)

    with pytest.raises(RegionNotFound):
        repository.settlements("R9")
    with pytest.raises(DataUnavailable, match="atlas.json"):
        JsonAtlasRepository(tmp_path / "absent").regions()


def write_dataset(root: Path) -> None:
    square = [[[60.0, 50.0], [70.0, 50.0], [70.0, 60.0], [60.0, 60.0], [60.0, 50.0]]]
    files: dict[str, object] = {
        "geo/regions.json": {
            "features": [
                {
                    "properties": {"name": "A"},
                    "geometry": {"type": "Polygon", "coordinates": square},
                }
            ]
        },
        "geo/region-paths.json": {
            "regions": [{"id": "R1", "name": "A", "path": "M1,2L3,4Z"}],
            "missing": ["R2"],
            "source": "test",
            "source_url": None,
        },
        "atlas.json": {
            "regions": [
                {"id": "R1", "name": "Альфа", "settlements": 1, "population": 10},
                {"id": "R2", "name": "Бета", "settlements": 1, "population": 5},
            ],
            "points": [
                {"id": "P1", "name": "Ёлкино", "lat": 55.0, "lon": 65.0, "pop": 10, "region": "R1"}
            ],
            "links": [
                link_row("0", "air", "", "", "2.5", "low"),
                link_row("1", "river", "all", "12", "", "high"),
                link_row("2", "teleport", "all", "1", "1", "high"),
            ],
        },
        "additional.json": {
            "regions": [{"region_id": "R1", "company_rows": 3, "strict_revenue_rub": None}],
            "route_seasons": [{"road_km": "49.565", "closure_date": "", "district": "D"}],
            "sources": [{"id": "s", "title": "S", "rows": 4}],
        },
        "indices.json": [],
        "additional/regions/R1.json": [settlement_row("1", "R1", "Ёлкино")],
        "additional/regions/R2.json": [settlement_row("2", "R2", "Озёрный")],
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")


def link_row(
    link_id: str, mode: str, season: str, km: str, freq: str, confidence: str
) -> dict[str, str]:
    return {
        "id": link_id,
        "region": "R1",
        "from_id": "P1",
        "to_id": "ext:Город",
        "from_name": "Ёлкино",
        "to_name": "Город",
        "mode": mode,
        "km": km,
        "freq_per_week": freq,
        "freq_note": "",
        "season": season,
        "confidence": confidence,
        "source_url": "",
        "source_date": "2026",
        "vehicle": "",
    }


def settlement_row(point_id: str, region_id: str, name: str) -> dict[str, object]:
    return {
        "point_id": point_id,
        "region_id": region_id,
        "name": name,
        "population": 10,
        "lat": 55.0,
        "lon": 65.0,
        "company_rows": 0,
        "revenue_rub": None,
    }


def test_overview_geometry_covers_every_region_with_fewer_vertices(
    atlas: JsonAtlasRepository,
) -> None:
    shapes = atlas.geo().shapes
    assert all(shape.path_low and shape.path_low.startswith("M") for shape in shapes)
    full = sum(shape.path.count("L") for shape in shapes)
    overview = sum((shape.path_low or "").count("L") for shape in shapes)
    assert overview < full / 2
