import json
from pathlib import Path

from app.domain.errors import DataUnavailable

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None
type JsonObject = dict[str, Json]


def read_json(data_dir: Path, relative: str) -> Json:
    path = data_dir / relative
    try:
        with path.open(encoding="utf-8") as file:
            loaded: Json = json.load(file)
    except FileNotFoundError:
        raise DataUnavailable(f"DATA_DIR={data_dir} has no {relative}") from None
    except (OSError, ValueError) as exc:
        raise DataUnavailable(f"DATA_DIR={data_dir}: cannot read {relative}: {exc}") from None
    return loaded


def objects(value: Json) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def obj(value: Json) -> JsonObject:
    return value if isinstance(value, dict) else {}


def text(row: JsonObject, key: str) -> str | None:
    value = row.get(key)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def number(row: JsonObject, key: str) -> float | None:
    value = row.get(key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def integer(row: JsonObject, key: str) -> int | None:
    value = number(row, key)
    return int(value) if value is not None else None


def pair(row: JsonObject, key: str) -> tuple[float, float] | None:
    value = row.get(key)
    if not isinstance(value, list) or len(value) < 2:
        return None
    first, second = value[0], value[1]
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return float(first), float(second)
    return None
