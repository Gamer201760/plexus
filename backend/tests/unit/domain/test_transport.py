import pytest

from app.domain.text import normalize_name
from app.domain.transport import (
    Mode,
    Season,
    great_circle_km,
    is_crossing,
    is_frequency_assumed,
    runs_in_season,
)


@pytest.mark.parametrize(
    ("link_season", "selected", "expected"),
    [
        (Season.SUMMER, Season.ALL, True),
        (None, Season.ALL, True),
        (Season.SUMMER, Season.SUMMER, True),
        (Season.ALL, Season.SUMMER, True),
        (Season.WINTER, Season.SUMMER, False),
        (None, Season.SUMMER, False),
        (Season.ALL, Season.WINTER, True),
        (Season.SUMMER, Season.WINTER, False),
        (None, Season.WINTER, False),
    ],
)
def test_season_filter_follows_contract(
    link_season: Season | None, selected: Season, expected: bool
) -> None:
    assert runs_in_season(link_season, selected) is expected


@pytest.mark.parametrize(
    ("mode", "freq", "span", "expected"),
    [
        (Mode.AIR, None, 300.0, True),
        (Mode.AIR, 0.0, 300.0, True),
        (Mode.AIR, 2.0, 300.0, False),
        (Mode.RIVER, None, None, True),
        (Mode.WINTER_ROAD, None, 80.0, False),
        (Mode.ICE_CROSSING, None, 1.0, False),
        (Mode.PONTOON_BRIDGE, None, 45.0, False),
        (Mode.FERRY, None, 5.0, False),
        (Mode.FERRY, None, 120.0, True),
        (Mode.FERRY, None, None, False),
    ],
)
def test_frequency_is_assumed_only_for_scheduled_lines_without_frequency(
    mode: Mode, freq: float | None, span: float | None, expected: bool
) -> None:
    assert is_frequency_assumed(mode, freq, span) is expected


def test_long_ferry_is_a_line_not_a_crossing() -> None:
    assert is_crossing(Mode.FERRY, 30.0)
    assert not is_crossing(Mode.FERRY, 30.1)
    assert not is_crossing(Mode.AIR, 1.0)


def test_great_circle_distance_matches_known_pair() -> None:
    barnaul, biysk = (53.348, 83.78), (52.539, 85.213)

    assert great_circle_km(barnaul, biysk) == pytest.approx(130, abs=5)
    assert great_circle_km(barnaul, barnaul) == 0


def test_name_normalization_folds_case_yo_and_spaces() -> None:
    assert normalize_name("  Село   СЕМЁНОВКА ") == "село семеновка"
    assert normalize_name("Ёлкино") == normalize_name("елкино")
