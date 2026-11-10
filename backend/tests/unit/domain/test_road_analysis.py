import pytest

from app.domain.road_analysis import SettlementAccess, compare_access


def test_already_unreachable_residents_are_not_newly_isolated() -> None:
    before = (SettlementAccess("a", 100, 20, True), SettlementAccess("b", 50, 0, False))
    after = (SettlementAccess("b", 50, 0, False), SettlementAccess("a", 100, 0, False))
    result = compare_access(before, after)
    assert result.isolated_population == 100
    assert result.affected_population == 100
    assert result.before == pytest.approx(20 * 100 / 150)
    assert result.after == 0


def test_reachability_does_not_depend_on_hansen_underflow() -> None:
    result = compare_access(
        (SettlementAccess("a", 10, 0, True),), (SettlementAccess("a", 10, 0, False),)
    )
    assert result.isolated_population == result.affected_population == 10


def test_small_numeric_noise_does_not_count_as_benefit() -> None:
    result = compare_access(
        (SettlementAccess("a", 10, 100, True),), (SettlementAccess("a", 10, 100.000001, True),)
    )
    assert result.affected_population == 0


def test_changed_population_is_rejected() -> None:
    with pytest.raises(ValueError, match="Population"):
        compare_access(
            (SettlementAccess("a", 10, 100, True),), (SettlementAccess("a", 11, 100, True),)
        )


def test_disjoint_identifiers_are_rejected() -> None:
    with pytest.raises(ValueError, match="identifiers"):
        compare_access(
            (SettlementAccess("a", 10, 100, True),), (SettlementAccess("b", 10, 100, True),)
        )
