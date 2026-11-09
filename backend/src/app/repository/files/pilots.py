import hashlib
import json
import math
from pathlib import Path
from threading import RLock

from app.domain.errors import DataUnavailable
from app.domain.pilot import Pilot, PilotEdge, PilotPair, PilotPoint
from app.repository.files.json_values import Json, JsonObject, read_json
from app.usecase.pilots import PilotNotFound


def require_object(value: Json) -> JsonObject:
    if not isinstance(value, dict):
        raise TypeError("expected object")
    return value


def require_text(row: JsonObject, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing string: {key}")
    return value


def require_number(row: JsonObject, key: str, optional: bool = False) -> float | None:
    value = row.get(key)
    if optional and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"invalid number: {key}")
    return float(value)


def strings(row: JsonObject, key: str) -> tuple[str, ...]:
    values = row.get(key)
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError(f"invalid strings: {key}")
    return tuple(value for value in values if isinstance(value, str))


def rows(row: JsonObject, key: str) -> list[JsonObject]:
    values = row.get(key)
    if not isinstance(values, list):
        raise TypeError(f"invalid array: {key}")
    return [require_object(value) for value in values]


def boolean(row: JsonObject, key: str) -> bool:
    value = row.get(key)
    if not isinstance(value, bool):
        raise TypeError(f"invalid boolean: {key}")
    return value


def edge_record(row: JsonObject) -> PilotEdge:
    travel = require_number(row, "travel_h")
    frequency = require_number(row, "frequency_per_week", True)
    assumed = require_number(row, "assumed_frequency_per_week", True)
    assert travel is not None
    if travel < 0 or any(value is not None and value <= 0 for value in (frequency, assumed)):
        raise ValueError("negative time or nonpositive frequency")
    seasons = strings(row, "seasons")
    if not seasons or not set(seasons) <= {"summer", "winter"}:
        raise ValueError("invalid seasons")
    intervals = row.get("headway_intervals_h", [])
    if not isinstance(intervals, list):
        raise TypeError("invalid headway intervals")
    headways = []
    for value in intervals:
        number = require_number({"interval": value}, "interval")
        assert number is not None
        headways.append(number)
    period = row.get("source_period")
    if period is not None and not isinstance(period, str):
        raise ValueError("invalid source period")
    mode = require_text(row, "mode")
    if mode not in {
        "road",
        "air",
        "river",
        "winter_road",
        "rail",
        "scheduled_ferry",
        "ferry",
        "ice_crossing",
        "pontoon_bridge",
    }:
        raise ValueError("invalid transport mode")
    if headways and (
        any(value <= 0 for value in headways) or not math.isclose(sum(headways), 168.0)
    ):
        raise ValueError("invalid weekly headway intervals")
    if not require_text(row, "source_url").startswith(("https://", "http://")):
        raise ValueError("invalid source URL")
    return PilotEdge(
        require_text(row, "id"),
        require_text(row, "from_id"),
        require_text(row, "to_id"),
        require_text(row, "mode"),
        seasons,
        travel,
        frequency,
        assumed,
        require_text(row, "source_url"),
        period,
        strings(row, "assumptions"),
        boolean(row, "editable"),
        boolean(row, "bidirectional"),
        tuple(headways),
    )


def pilot_record(value: Json) -> Pilot:
    row = require_object(value)
    version = require_text(row, "artifact_version")
    payload = {key: item for key, item in row.items() if key != "artifact_version"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if hashlib.sha256(encoded.encode()).hexdigest() != version:
        raise ValueError("pilot checksum mismatch")
    points = []
    for point in rows(row, "points"):
        latitude, longitude = require_number(point, "latitude"), require_number(point, "longitude")
        assert latitude is not None and longitude is not None
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("invalid coordinates")
        points.append(
            PilotPoint(require_text(point, "id"), require_text(point, "name"), latitude, longitude)
        )
    edges = tuple(edge_record(item) for item in rows(row, "edges"))
    pairs = tuple(
        PilotPair(
            require_text(item, "id"), require_text(item, "from_id"), require_text(item, "to_id")
        )
        for item in rows(row, "pairs")
    )
    known = {point.id for point in points}
    if len(known) != len(points) or not known or not pairs:
        raise ValueError("missing or duplicate pilot points")
    if len({edge.id for edge in edges}) != len(edges) or len({pair.id for pair in pairs}) != len(
        pairs
    ):
        raise ValueError("duplicate pilot edges or pairs")
    endpoints: tuple[PilotEdge | PilotPair, ...] = (*edges, *pairs)
    if any(item.from_id not in known or item.to_id not in known for item in endpoints):
        raise ValueError("unknown endpoint")
    return Pilot(
        require_text(row, "id"),
        require_text(row, "name"),
        require_text(row, "model_version"),
        version,
        tuple(points),
        edges,
        pairs,
        strings(row, "assumptions"),
    )


class JsonPilotRepository:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._pilots: tuple[Pilot, ...] | None = None
        self._lock = RLock()

    def list(self) -> tuple[Pilot, ...]:
        with self._lock:
            if self._pilots is None:
                paths = sorted((self._data_dir / "pilots").glob("*.json"))
                if not paths:
                    raise DataUnavailable("Pilot artifacts are missing")
                try:
                    pilots = tuple(
                        pilot_record(
                            read_json(self._data_dir, str(path.relative_to(self._data_dir)))
                        )
                        for path in paths
                    )
                    if len({pilot.id for pilot in pilots}) != len(pilots):
                        raise ValueError("duplicate pilots")
                except (ValueError, KeyError, TypeError) as error:
                    raise DataUnavailable("Invalid pilot artifact") from error
                self._pilots = pilots
            return self._pilots

    def get(self, pilot_id: str) -> Pilot:
        for pilot in self.list():
            if pilot.id == pilot_id:
                return pilot
        raise PilotNotFound()
