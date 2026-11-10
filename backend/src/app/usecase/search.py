from dataclasses import dataclass

from app.domain.errors import InvalidQuery
from app.domain.text import normalize_name
from app.usecase.interface.atlas import AtlasRepository

MIN_QUERY = 2
MAX_LIMIT = 50


@dataclass(frozen=True, slots=True)
class RegionHit:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class SettlementHit:
    id: str
    name: str
    region_id: str
    region_name: str
    population: int | None


@dataclass(frozen=True, slots=True)
class SearchResult:
    regions: list[RegionHit]
    settlements: list[SettlementHit]


def _rank(name: str, needle: str) -> int | None:
    position = name.find(needle)
    if position < 0:
        return None
    while position >= 0:
        if position == 0 or not name[position - 1].isalnum():
            return 0
        position = name.find(needle, position + 1)
    return 1


class Search:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def run(self, text: str, limit: int = 8) -> SearchResult:
        needle = normalize_name(text)
        if len(needle) < MIN_QUERY:
            raise InvalidQuery(f"Query needs at least {MIN_QUERY} characters")
        if limit < 1 or limit > MAX_LIMIT:
            raise InvalidQuery(f"Limit must be between 1 and {MAX_LIMIT}")
        regions = sorted(self._repository.regions(), key=lambda region: region.name)
        region_names = {region.id: region.name for region in regions}
        region_hits = [
            (rank, RegionHit(id=region.id, name=region.name))
            for region in regions
            if (rank := _rank(normalize_name(region.name), needle)) is not None
        ]
        settlement_hits = [
            (rank, -(item.population or 0), item)
            for item in self._repository.search_names(needle)
            if (rank := _rank(normalize_name(item.name), needle)) is not None
        ]
        settlement_hits.sort(key=lambda hit: (hit[0], hit[1], hit[2].name))
        return SearchResult(
            regions=[hit for _, hit in sorted(region_hits, key=lambda hit: hit[0])][:limit],
            settlements=[
                SettlementHit(
                    id=item.id,
                    name=item.name,
                    region_id=item.region_id,
                    region_name=region_names.get(item.region_id, item.region_id),
                    population=item.population,
                )
                for _, _, item in settlement_hits[:limit]
            ],
        )
