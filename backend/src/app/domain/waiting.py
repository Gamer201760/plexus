import math

from app.domain.errors import InvalidQuery


def periodic_wait(intervals_h: tuple[float, ...], period_h: float = 168.0) -> float:
    if not intervals_h or not math.isfinite(period_h) or period_h <= 0:
        raise InvalidQuery("A positive period and headway intervals are required")
    if any(not math.isfinite(value) or value <= 0 for value in intervals_h):
        raise InvalidQuery("Headway intervals must be finite and positive")
    if not math.isclose(sum(intervals_h), period_h):
        raise InvalidQuery("Headway intervals must cover the period")
    return sum(value * value for value in intervals_h) / (2 * period_h)
