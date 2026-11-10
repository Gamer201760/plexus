from typing import Protocol

from app.domain.market_scenario import (
    ScenarioCatalog,
    ScenarioModel,
)


class ScenarioRepository(Protocol):
    def catalog(self) -> ScenarioCatalog: ...

    def model(self, season: str) -> ScenarioModel: ...
