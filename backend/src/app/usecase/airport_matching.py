import re

from app.domain.transport import great_circle_km
from app.usecase.dto.atlas import PointRecord

TRANSLITERATION = dict(zip(
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    ("a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n",
     "o", "p", "r", "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"),
    strict=True,
))


def place_key(name: str) -> str:
    value = re.sub(r"^(г\.|город|посёлок|поселок|село|с\.|пгт|п\.|деревня|д\.)\s+", "", name.casefold())
    return re.sub(r"[^a-z0-9]", "", "".join(TRANSLITERATION.get(c, c) for c in value))


def airport_distance(point: PointRecord, latitude: float, longitude: float) -> float:
    return great_circle_km((point.lat, point.lon), (latitude, longitude))
