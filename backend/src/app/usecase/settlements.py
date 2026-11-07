from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import InvalidQuery, RegionNotFound
from app.domain.text import normalize_name
from app.usecase.dto import SettlementRecord
from app.usecase.interface import AtlasRepository

MAX_PAGE = 500


class SettlementSort(StrEnum):
    POPULATION = "population"
    NAME = "name"
    COMPANIES = "companies"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class SettlementQuery:
    region_id: str
    text: str | None = None
    sort: SettlementSort = SettlementSort.POPULATION
    order: SortOrder = SortOrder.DESC
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class SettlementPage:
    total: int
    items: list[SettlementRecord]


def _known_number(value: int | None) -> tuple[bool, int]:
    return value is None, value or 0


def _sort_key(
    sort: SettlementSort, descending: bool
) -> Callable[[SettlementRecord], tuple[bool, int | str, str]]:
    sign = -1 if descending else 1

    def key(item: SettlementRecord) -> tuple[bool, int | str, str]:
        name = normalize_name(item.name)
        if sort is SettlementSort.NAME:
            return False, name, item.id
        missing, value = _known_number(
            item.population if sort is SettlementSort.POPULATION else item.companies
        )
        return missing, sign * value, name

    return key


class SettlementQueries:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def page(self, query: SettlementQuery) -> SettlementPage:
        if query.limit < 1 or query.limit > MAX_PAGE or query.offset < 0:
            raise InvalidQuery("Page bounds are invalid")
        if query.region_id not in {region.id for region in self._repository.regions()}:
            raise RegionNotFound()
        items = self._repository.settlements(query.region_id)
        needle = normalize_name(query.text or "")
        if needle:
            items = [item for item in items if needle in normalize_name(item.name)]
        descending = query.order is SortOrder.DESC
        ordered = sorted(items, key=_sort_key(query.sort, descending))
        if query.sort is SettlementSort.NAME and descending:
            ordered.reverse()
        return SettlementPage(
            total=len(ordered), items=ordered[query.offset : query.offset + query.limit]
        )
