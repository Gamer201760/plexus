from collections.abc import Mapping
from typing import Any

from app.repository.clickhouse.client import ClickHouseReader, QueryValue
from app.repository.clickhouse.road_view import ClickHouseRoadView


class Reader(ClickHouseReader):
    def __init__(self) -> None:
        super().__init__("http://localhost:18123", "test", "test")
        self.parameters: list[dict[str, QueryValue]] = []

    def rows(self, sql: str, parameters: Mapping[str, QueryValue]) -> list[dict[str, Any]]:
        self.parameters.append(dict(parameters))
        if "atlas_metadata" in sql:
            return [{"value": "road-test"}]
        if "GROUP BY rank" in sql:
            return [{"rank": 1, "n": "10"}, {"rank": 4, "n": "300000"}]
        return [
            {
                "way_id": "9876543210",
                "name": "Road",
                "highway": "trunk",
                "speed_kmh": 90.0,
                "source_node": "12",
                "target_node": "14",
                "coordinates": [[38.0, 55.0], [39.0, 55.5], [40.0, 56.0]],
            }
        ]


def test_view_preserves_identifiers_and_only_reduces_whole_road_classes() -> None:
    view = ClickHouseRoadView("http://localhost:18123", "test", "test")
    reader = Reader()
    view.reader = reader
    result = view.view((38.0, 54.0, 43.0, 57.0), 7.0)
    assert result.detail == "secondary"
    assert result.truncated
    assert result.matched == 10
    assert result.version == "road-test"
    assert result.segments[0].way_id == 9876543210
    assert result.segments[0].source_node == 12
    assert result.segments[0].target_node == 14
    assert len(result.segments[0].coordinates) == 3
    assert reader.parameters == [
        {"west": 38.0, "south": 54.0, "east": 43.0, "north": 57.0, "level": 4},
        {"west": 38.0, "south": 54.0, "east": 43.0, "north": 57.0, "level": 3},
        {},
    ]
