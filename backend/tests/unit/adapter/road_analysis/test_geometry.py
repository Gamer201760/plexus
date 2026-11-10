import numpy as np

from app.adapter.road_analysis.geometry import region_edges


def test_crossing_segment_without_inside_endpoints_and_hole() -> None:
    polygon = [
        [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0), (0.0, 0.0)],
        [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0), (1.0, 1.0)],
    ]
    lon = np.array([-1.0, 5.0, 1.5, 2.5]) + 100
    lat = np.array([0.5, 0.5, 2.0, 2.0])
    polygon = [[(x + 100, y) for x, y in ring] for ring in polygon]
    positions, crosses = region_edges(lon, lat, np.array([0, 2]), np.array([1, 3]), [polygon])
    assert positions.tolist() == [0]
    assert crosses.tolist() == [True]


def test_islands_and_antimeridian_are_included() -> None:
    polygons = [
        [[(179.0, 0.0), (182.0, 0.0), (182.0, 4.0), (179.0, 4.0), (179.0, 0.0)]],
        [[(160.0, 0.0), (162.0, 0.0), (162.0, 4.0), (160.0, 4.0), (160.0, 0.0)]],
    ]
    positions, _ = region_edges(
        np.array([179.5, -179.0, 160.5, 161.5]),
        np.ones(4),
        np.array([0, 2]),
        np.array([1, 3]),
        polygons,
    )
    assert positions.tolist() == [0, 1]
