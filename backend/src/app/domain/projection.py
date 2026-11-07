import math
import re
from collections.abc import Iterable
from dataclasses import dataclass

STANDARD_PARALLELS = (50.0, 70.0)
ORIGIN_LATITUDE = 60.0
CENTRAL_MERIDIAN = 100.0
CANVAS_CENTER = (500.0, 310.0)
CANVAS_FIT = (940.0, 520.0)
VIEW_BOX = "0 0 1000 620"
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _half_angle_tan(latitude: float) -> float:
    return math.tan(math.pi / 4 + math.radians(latitude) / 2)


def _cone() -> tuple[float, float, float]:
    first, second = STANDARD_PARALLELS
    cone = math.log(math.cos(math.radians(first)) / math.cos(math.radians(second))) / math.log(
        _half_angle_tan(second) / _half_angle_tan(first)
    )
    scale = math.cos(math.radians(first)) * _half_angle_tan(first) ** cone / cone
    origin = scale / _half_angle_tan(ORIGIN_LATITUDE) ** cone
    return cone, scale, origin


CONE, CONE_SCALE, ORIGIN_RADIUS = _cone()


def lambert(lon: float, lat: float) -> tuple[float, float]:
    longitude = lon + 360 if lon < 0 else lon
    radius = CONE_SCALE / _half_angle_tan(lat) ** CONE
    theta = CONE * math.radians(longitude - CENTRAL_MERIDIAN)
    return radius * math.sin(theta), ORIGIN_RADIUS - radius * math.cos(theta)


@dataclass(frozen=True, slots=True)
class SvgFrame:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @classmethod
    def enclosing(cls, projected: Iterable[tuple[float, float]]) -> "SvgFrame":
        xs: list[float] = []
        ys: list[float] = []
        for x, y in projected:
            xs.append(x)
            ys.append(y)
        if not xs:
            raise ValueError("SvgFrame needs at least one point")
        return cls(min(xs), max(xs), min(ys), max(ys))

    @property
    def scale(self) -> float:
        width, height = CANVAS_FIT
        return min(width / (self.max_x - self.min_x), height / (self.max_y - self.min_y))

    def place(self, lon: float, lat: float) -> tuple[float, float]:
        x, y = lambert(lon, lat)
        center_x, center_y = CANVAS_CENTER
        return (
            round(center_x + (x - (self.min_x + self.max_x) / 2) * self.scale, 1),
            round(center_y - (y - (self.min_y + self.max_y) / 2) * self.scale, 1),
        )


def path_bbox(path: str) -> tuple[float, float, float, float] | None:
    values = [float(token) for token in NUMBER.findall(path)]
    xs, ys = values[0::2], values[1::2]
    if not xs or len(xs) != len(ys):
        return None
    left, top = min(xs), min(ys)
    return left, top, round(max(xs) - left, 1), round(max(ys) - top, 1)
