from collections import Counter
from dataclasses import dataclass

from app.domain.errors import RegionNotFound
from app.domain.projection import path_bbox
from app.domain.transport import Mode, NetworkMode, Season, runs_in_season
from app.usecase.dto.atlas import EconomyRecord, LinkRecord, RegionRecord
from app.usecase.index_status import hansen_by_region, resolved_scenario
from app.usecase.interface.atlas import AtlasRepository


@dataclass(frozen=True, slots=True)
class RegionSummary:
    id: str
    name: str
    settlements: int
    population: int
    links: int
    links_season: int
    companies: int | None
    revenue_rub: float | None
    hansen: float | None
    has_geometry: bool
    index_population_coverage: float | None = None
    index_settlement_coverage: float | None = None
    index_model_version: str | None = None
    index_artifact_version: str | None = None


@dataclass(frozen=True, slots=True)
class ModeCounts:
    mode: Mode
    all: int
    summer: int
    winter: int


@dataclass(frozen=True, slots=True)
class RegionDetail:
    summary: RegionSummary
    path: str | None
    bbox: tuple[float, float, float, float] | None
    links_by_mode: list[ModeCounts]
    economy: EconomyRecord | None


def _mode_counts(links: list[LinkRecord]) -> list[ModeCounts]:
    counts: dict[Season, Counter[Mode]] = {
        season: Counter(link.mode for link in links if runs_in_season(link.season, season))
        for season in Season
    }
    return [
        ModeCounts(
            mode=mode,
            all=counts[Season.ALL][mode],
            summer=counts[Season.SUMMER][mode],
            winter=counts[Season.WINTER][mode],
        )
        for mode in Mode
        if counts[Season.ALL][mode]
    ]


class RegionQueries:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def summaries(
        self, season: Season, network_mode: NetworkMode = NetworkMode.MULTIMODAL
    ) -> list[RegionSummary]:
        regions = sorted(self._repository.regions(), key=lambda region: region.name)
        return self._summaries(regions, season, network_mode)

    def detail(
        self, region_id: str, season: Season, network_mode: NetworkMode = NetworkMode.MULTIMODAL
    ) -> RegionDetail:
        region = self._find(region_id)
        shapes = {shape.id: shape.path for shape in self._repository.geo().shapes}
        path = shapes.get(region_id)
        links = [link for link in self._repository.links() if link.region_id == region_id]
        return RegionDetail(
            summary=self._summaries([region], season, network_mode)[0],
            path=path,
            bbox=path_bbox(path) if path else None,
            links_by_mode=_mode_counts(links),
            economy=self._repository.economy().get(region_id),
        )

    def _find(self, region_id: str) -> RegionRecord:
        for region in self._repository.regions():
            if region.id == region_id:
                return region
        raise RegionNotFound()

    def _summaries(
        self, regions: list[RegionRecord], season: Season, network_mode: NetworkMode
    ) -> list[RegionSummary]:
        total: Counter[str] = Counter()
        seasonal: Counter[str] = Counter()
        for link in self._repository.links():
            total[link.region_id] += 1
            seasonal[link.region_id] += runs_in_season(link.season, season)
        economy = self._repository.economy()
        shapes = {shape.id for shape in self._repository.geo().shapes}
        rows = self._repository.indices()
        hansen = hansen_by_region(rows, season, network_mode)
        coverage = {
            row.region_id: row
            for row in rows
            if row.scenario == resolved_scenario(rows, season, network_mode)
        }
        return [
            RegionSummary(
                id=region.id,
                name=region.name,
                settlements=region.settlements,
                population=region.population,
                links=total[region.id],
                links_season=seasonal[region.id],
                companies=_economy(economy.get(region.id)).company_rows,
                revenue_rub=_economy(economy.get(region.id)).strict_revenue_rub,
                hansen=hansen.get(region.id),
                has_geometry=region.id in shapes,
                index_population_coverage=_ratio(
                    coverage[region.id].covered_population, coverage[region.id].total_population
                )
                if region.id in coverage
                else None,
                index_settlement_coverage=_ratio(
                    coverage[region.id].covered_settlements, coverage[region.id].total_settlements
                )
                if region.id in coverage
                else None,
                index_model_version=coverage[region.id].model_version
                if region.id in coverage
                else None,
                index_artifact_version=coverage[region.id].artifact_version
                if region.id in coverage
                else None,
            )
            for region in regions
        ]


def _economy(record: EconomyRecord | None) -> EconomyRecord:
    return record or EconomyRecord("", None, None, None, None)


def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    return (
        numerator / denominator
        if numerator is not None and denominator is not None and denominator > 0
        else None
    )
