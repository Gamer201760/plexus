from app.domain.errors import DomainError, InvalidQuery
from app.domain.market_scenario import (
    NewTrunkLink,
    ScenarioCatalog,
    ScenarioEvaluation,
    evaluate,
)
from app.usecase.interface.scenarios import ScenarioRepository


class StaleScenarioVersion(DomainError):
    code = "stale_scenario_version"
    message = "Reload the current scenario catalog"




class ScenarioQueries:
    def __init__(self, repository: ScenarioRepository) -> None:
        self._repository = repository

    def catalog(self) -> ScenarioCatalog:
        return self._repository.catalog()

    def evaluate(
        self,
        season: str,
        model_version: str,
        artifact_version: str,
        links: tuple[NewTrunkLink, ...],
    ) -> ScenarioEvaluation:
        catalog = self._repository.catalog()
        if season not in catalog.seasons:
            raise InvalidQuery("Unknown scenario season")
        if model_version != catalog.model_version or artifact_version != catalog.artifact_version:
            raise StaleScenarioVersion()
        return evaluate(self._repository.model(season), links)
