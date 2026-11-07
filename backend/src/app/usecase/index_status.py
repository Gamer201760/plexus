from dataclasses import dataclass
from enum import StrEnum

from app.domain.transport import Season
from app.usecase.dto import IndexRecord

FORMULA = "A_i = Σ M_j · exp(−β · t_ij)"
HALF_LIFE_HOURS = 2
MARKETS = 180
MISSING_REASON = "Regional index rows are not exported yet: indices.json is empty"
SCENARIO_BY_SEASON = {Season.ALL: "road", Season.SUMMER: "summer", Season.WINTER: "winter"}


class IndexState(StrEnum):
    READY = "ready"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class IndexComponent:
    key: str
    title: str
    description: str
    source: str


@dataclass(frozen=True, slots=True)
class IndexStatus:
    status: IndexState
    reason: str | None
    formula: str
    half_life_hours: int
    markets: int
    components: list[IndexComponent]


COMPONENTS = [
    IndexComponent(
        key="markets",
        title="Рынки M_j",
        description="Население 180 городов из матрицы Точно, от 13 тыс. жителей",
        source="Матрица Точно, перепись населения",
    ),
    IndexComponent(
        key="travel_time",
        title="Время в пути t_ij",
        description=(
            "Кратчайшее время по дорожному графу OSM, магистральной сети Точно "
            "и ручным связям: авиация, реки, зимники, переправы"
        ),
        source="OpenStreetMap, матрица Точно, региональные CSV проекта",
    ),
    IndexComponent(
        key="decay",
        title="Затухание β",
        description="β = ln 2 / 2 ч: вес рынка уменьшается вдвое каждые два часа пути",
        source="Hansen (1959)",
    ),
    IndexComponent(
        key="scenario",
        title="Сценарий сезона",
        description=(
            "road — только дороги, summer и winter — дороги и сезонные связи. "
            "Сезон «все» показывает сценарий road"
        ),
        source="Расчёт проекта",
    ),
]


def index_status(rows: list[IndexRecord]) -> IndexStatus:
    ready = bool(rows)
    return IndexStatus(
        status=IndexState.READY if ready else IndexState.MISSING,
        reason=None if ready else MISSING_REASON,
        formula=FORMULA,
        half_life_hours=HALF_LIFE_HOURS,
        markets=MARKETS,
        components=list(COMPONENTS),
    )


def hansen_by_region(rows: list[IndexRecord], season: Season) -> dict[str, float | None]:
    scenario = SCENARIO_BY_SEASON[season]
    return {row.region_id: row.hansen for row in rows if row.scenario == scenario}
