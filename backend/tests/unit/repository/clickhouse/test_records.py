from dataclasses import asdict

from app.repository.clickhouse.records import decode, encode
from app.usecase.dto.atlas import BoundaryShape
from app.usecase.dto.road_graph import RoadAddition, RoadJob, RoadResult


def test_optional_coordinates_distinguish_absence_from_empty_geometry() -> None:
    missing = RoadAddition(1, 2, 0.5)
    empty = RoadAddition(1, 2, 0.5, [])
    assert encode(RoadAddition, missing)["coordinates"] == []
    assert encode(RoadAddition, empty)["coordinates"] == [[]]
    assert decode(RoadAddition, encode(RoadAddition, missing)) == missing
    assert decode(RoadAddition, encode(RoadAddition, empty)) == empty


def test_json_integral_numbers_restore_float_types_for_stable_fingerprints() -> None:
    value = decode(
        BoundaryShape,
        {
            "id": "R",
            "name": "Region",
            "bounds": [1, 2, 3, 4],
            "polygons": [[[[1, 2], [3, 4], [1, 2]]]],
        },
    )
    assert all(type(v) is float for v in value.bounds)
    assert all(type(v) is float for v in value.polygons[0][0][0])
    assert asdict(value)["bounds"] == (1.0, 2.0, 3.0, 4.0)


def test_job_roundtrip_preserves_result_nulls_and_nested_dataclasses() -> None:
    result = RoadResult(10.0, 12.0, 2.0, 20.0, 100, 2, 1, 50.0, 0.01)
    job = RoadJob("id", "R", "Region", "road", [], "completed", 5, 5, "snapshot", result=result)
    assert decode(RoadJob, encode(RoadJob, job)) == job
    assert encode(RoadJob, job)["addition"] == []
    assert encode(RoadJob, job)["result"][0]["money"] == []
