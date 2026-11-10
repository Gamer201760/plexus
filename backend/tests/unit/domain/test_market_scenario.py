import numpy as np
import pytest

from app.domain.errors import InvalidQuery
from app.domain.market_evaluation import evaluate, link_weight, point_access, population_mean
from app.domain.market_scenario import (
    BETA_PER_H,
    MarketCity,
    NewTrunkLink,
    ScenarioModel,
    ScenarioRegion,
)

CITIES = (
    MarketCity("X", "Alpha", 1000.0, 50.0, 40.0, True),
    MarketCity("Y", "Beta", 500.0, 51.0, 41.0, False),
    MarketCity("Z", "Beta", 2000.0, 52.0, 42.0, False),
)
REGIONS = (ScenarioRegion("01", "Alpha"), ScenarioRegion("02", "Beta"))
ROAD = np.array(
    [
        [1.0, np.inf, np.inf],
        [15.0, 2.0, 3.0],
        [np.inf, np.inf, np.inf],
        [0.5, 30.0, 40.0],
    ],
    dtype=np.float32,
)
CITY = np.array([[0.0, 10.0, 20.0], [10.0, 0.0, 10.0], [20.0, 10.0, 0.0]])
POPULATION = np.array([100.0, 50.0, 10.0, 70.0])
REGION_IDX = np.array([0, 1, 1, 0], dtype=np.int32)
MARKETS = np.array([city.population for city in CITIES])


def closed(matrix: np.ndarray) -> np.ndarray:
    result = matrix.copy()
    for k in range(len(result)):
        np.minimum(result, result[:, k, None] + result[None, k, :], out=result)
    return result


def best_from(road: np.ndarray, city: np.ndarray) -> np.ndarray:
    combined: np.ndarray = (road[:, :, None].astype(np.float64) + city[None, :, :]).min(axis=1)
    return combined


def model() -> ScenarioModel:
    best = best_from(ROAD, CITY).astype(np.float32)
    access = point_access(best, MARKETS)
    return ScenarioModel(
        "road",
        "model-v1",
        "artifact-1",
        float(np.average(access, weights=POPULATION)),
        CITIES,
        REGIONS,
        ROAD,
        best,
        CITY,
        POPULATION,
        REGION_IDX,
        {"p1": 0, "p2": 1, "p3": 2, "p4": 3},
        access,
        population_mean(access, POPULATION, REGION_IDX, 2),
        np.bincount(REGION_IDX, weights=POPULATION, minlength=2),
    )


def test_added_trunk_link_matches_full_recomputation() -> None:
    subject = model()
    link = NewTrunkLink("X", "Z", "air", 1.0, 28)
    weight, notes = link_weight(link)
    assert weight == pytest.approx(6.5)
    assert notes == ("uniform_headways_random_need",)
    result = evaluate(subject, (link,))
    patched = CITY.copy()
    patched[0, 2] = patched[2, 0] = weight
    reference_best = best_from(ROAD, closed(patched))
    reference_access = np.exp(-BETA_PER_H * reference_best) @ MARKETS
    reference_region = population_mean(reference_access, POPULATION, REGION_IDX, 2)
    scale = 100.0 / subject.normalization_base
    by_id = {impact.region_id: impact for impact in result.regions}
    for index, region in enumerate(REGIONS):
        assert by_id[region.region_id].changed_index == pytest.approx(
            reference_region[index] * scale
        )
        assert by_id[region.region_id].baseline_index == pytest.approx(
            subject.region_access[index] * scale
        )
    assert result.national_baseline_index == pytest.approx(100.0)
    assert result.national_changed_index == pytest.approx(
        np.average(reference_access, weights=POPULATION) * scale
    )
    assert result.national_changed_index > result.national_baseline_index
    assert result.improved_city_pairs == 1
    assert result.city_pairs[0].from_city == "X"
    assert result.city_pairs[0].baseline_h == pytest.approx(20.0)
    assert result.city_pairs[0].changed_h == pytest.approx(6.5)
    assert np.array_equal(subject.city_best_h, CITY)


def test_relay_improvement_propagates_through_hub() -> None:
    subject = model()
    result = evaluate(subject, (NewTrunkLink("X", "Y", "road", 1.0),))
    patched = CITY.copy()
    patched[0, 1] = patched[1, 0] = 1.0
    reference_best = best_from(ROAD, closed(patched))
    reference_access = np.exp(-BETA_PER_H * reference_best) @ MARKETS
    scale = 100.0 / subject.normalization_base
    assert result.improved_city_pairs == 2
    assert result.national_changed_index == pytest.approx(
        np.average(reference_access, weights=POPULATION) * scale
    )


def test_isolated_point_stays_isolated() -> None:
    result = evaluate(model(), (NewTrunkLink("X", "Z", "rail", 2.0, 14),))
    beta = {impact.region_id: impact for impact in result.regions}["02"]
    assert beta.delta_index >= 0


@pytest.mark.parametrize(
    "link",
    [
        NewTrunkLink("X", "Q", "air", 1.0, 7),
        NewTrunkLink("p3", "p3", "road", 1.0),
        NewTrunkLink("X", "X", "air", 1.0, 7),
        NewTrunkLink("X", "Y", "teleport", 1.0),
        NewTrunkLink("X", "Y", "air", 0.0, 7),
        NewTrunkLink("X", "Y", "air", float("nan"), 7),
        NewTrunkLink("X", "Y", "air", 1.0, 0),
        NewTrunkLink("X", "Y", "air", 1.0, 29),
        NewTrunkLink("X", "Y", "road", 1.0, 7),
    ],
)
def test_invalid_link_is_rejected(link: NewTrunkLink) -> None:
    with pytest.raises(InvalidQuery):
        evaluate(model(), (link,))


def test_empty_links_are_rejected_and_unknown_frequency_is_assumed() -> None:
    with pytest.raises(InvalidQuery):
        evaluate(model(), ())
    weight, notes = link_weight(NewTrunkLink("X", "Y", "air", 1.0))
    assert weight == pytest.approx(1.0 + 84.0 + 2.5)
    assert "assumed_frequency:X-Y:1" in notes


def test_settlement_link_connects_isolated_point_exactly() -> None:
    subject = model()
    result = evaluate(subject, (NewTrunkLink("p3", "X", "air", 2.0, 14),))
    weight = 2.0 + 6.0 + 2.5
    row = weight + CITY[0]
    expected_access = float(np.exp(-BETA_PER_H * row) @ MARKETS)
    reference = subject.point_access.copy()
    reference[2] = expected_access
    scale = 100.0 / subject.normalization_base
    reference_region = population_mean(reference, POPULATION, REGION_IDX, 2)
    by_id = {impact.region_id: impact for impact in result.regions}
    assert by_id["02"].changed_index == pytest.approx(reference_region[1] * scale)
    assert by_id["01"].delta_index == pytest.approx(0.0)
    assert result.improved_city_pairs == 0
    assert "settlement_links_serve_named_endpoints_only" in result.assumptions


def test_settlement_chain_relaxes_through_other_settlement() -> None:
    subject = model()
    links = (
        NewTrunkLink("p3", "p1", "road", 1.0),
        NewTrunkLink("p1", "X", "road", 0.5),
    )
    result = evaluate(subject, links)
    row_p1 = np.minimum((ROAD[0].astype(np.float64)[:, None] + CITY).min(axis=0), 0.5 + CITY[0])
    row_p3 = 1.0 + row_p1
    reference = subject.point_access.copy()
    reference[0] = float(np.exp(-BETA_PER_H * row_p1) @ MARKETS)
    reference[2] = float(np.exp(-BETA_PER_H * row_p3) @ MARKETS)
    scale = 100.0 / subject.normalization_base
    reference_region = population_mean(reference, POPULATION, REGION_IDX, 2)
    by_id = {impact.region_id: impact for impact in result.regions}
    for index, region in enumerate(REGIONS):
        assert by_id[region.region_id].changed_index == pytest.approx(
            reference_region[index] * scale
        )
