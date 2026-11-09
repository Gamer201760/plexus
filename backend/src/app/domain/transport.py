import math
from enum import StrEnum


class Season(StrEnum):
    ALL = "all"
    SUMMER = "summer"
    WINTER = "winter"


class Mode(StrEnum):
    BUS = "bus"
    AIR = "air"
    RIVER = "river"
    WINTER_ROAD = "winter_road"
    FERRY = "ferry"
    ICE_CROSSING = "ice_crossing"
    PONTOON_BRIDGE = "pontoon_bridge"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


CROSSING_MODES = frozenset({Mode.FERRY, Mode.ICE_CROSSING, Mode.PONTOON_BRIDGE})
FERRY_LINE_MIN_KM = 30.0
EARTH_DIAMETER_KM = 12742.0


def runs_in_season(link_season: Season | None, selected: Season) -> bool:
    if selected is Season.ALL:
        return True
    return link_season is selected or link_season is Season.ALL


def great_circle_km(start: tuple[float, float], end: tuple[float, float]) -> float:
    lat1, lon1 = (math.radians(value) for value in start)
    lat2, lon2 = (math.radians(value) for value in end)
    haversine = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return EARTH_DIAMETER_KM * math.asin(math.sqrt(haversine))


def is_crossing(mode: Mode, span_km: float | None) -> bool:
    if mode not in CROSSING_MODES:
        return False
    if mode is not Mode.FERRY or span_km is None:
        return True
    return span_km <= FERRY_LINE_MIN_KM


def is_frequency_assumed(mode: Mode, freq_per_week: float | None, span_km: float | None) -> bool:
    scheduled = mode not in {Mode.WINTER_ROAD, Mode.BUS} and not is_crossing(mode, span_km)
    known = freq_per_week is not None and freq_per_week > 0
    return scheduled and not known
