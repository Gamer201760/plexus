import hashlib
import json
from pathlib import Path

import pytest

from app.domain.errors import DataUnavailable
from app.repository.files.pilots import JsonPilotRepository

SOURCE = (
    Path(__file__).resolve().parents[5] / "frontend" / "atlas" / "public" / "pilots" / "tuva.json"
)


def write_pilot(directory: Path, payload: dict[str, object]) -> None:
    payload.pop("artifact_version", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["artifact_version"] = hashlib.sha256(encoded.encode()).hexdigest()
    target = directory / "pilots" / "tuva.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload))


@pytest.mark.parametrize(
    "field,value",
    [
        ("travel_h", -1),
        ("travel_h", float("inf")),
        ("mode", "unrecognized"),
        ("frequency_per_week", 0),
        ("source_url", "javascript:invalid"),
        ("headway_intervals_h", [48]),
    ],
)
def test_invalid_but_correctly_hashed_artifact_fails(
    tmp_path: Path, field: str, value: object
) -> None:
    payload = json.loads(SOURCE.read_text())
    payload["edges"][0][field] = value
    write_pilot(tmp_path, payload)
    with pytest.raises(DataUnavailable):
        JsonPilotRepository(tmp_path).get("tuva")


def test_content_checksum_detects_modified_file(tmp_path: Path) -> None:
    payload = json.loads(SOURCE.read_text())
    payload["name"] = "Changed"
    target = tmp_path / "pilots" / "tuva.json"
    target.parent.mkdir()
    target.write_text(json.dumps(payload))
    with pytest.raises(DataUnavailable):
        JsonPilotRepository(tmp_path).list()
