from collections import Counter
from dataclasses import dataclass

from app.domain.transport import Mode, Season
from app.usecase.index_status import IndexStatus, index_status
from app.usecase.interface import AtlasRepository

UNKNOWN_SEASON = "unknown"


@dataclass(frozen=True, slots=True)
class Overview:
    regions: int
    settlements: int
    population: int
    links: int
    links_by_mode: dict[str, int]
    links_by_season: dict[str, int]
    companies: int | None
    revenue_rub: float | None
    index: IndexStatus


def _known_sum[T: (int, float)](values: list[T | None]) -> T | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None


class OverviewQuery:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def run(self) -> Overview:
        regions = self._repository.regions()
        links = self._repository.links()
        economy = list(self._repository.economy().values())
        modes = Counter(link.mode for link in links)
        seasons = Counter(link.season.value if link.season else UNKNOWN_SEASON for link in links)
        return Overview(
            regions=len(regions),
            settlements=self._repository.total_settlements(),
            population=sum(region.population for region in regions),
            links=len(links),
            links_by_mode={mode.value: modes[mode] for mode in Mode},
            links_by_season={
                key: seasons[key] for key in [*(season.value for season in Season), UNKNOWN_SEASON]
            },
            companies=_known_sum([record.company_rows for record in economy]),
            revenue_rub=_known_sum([record.strict_revenue_rub for record in economy]),
            index=index_status(self._repository.indices()),
        )
