import os

from fastapi import APIRouter, FastAPI

from app.adapter.log.stdlib import StdlibLogger
from app.controller.atlas.catalog import build_catalog_router
from app.controller.atlas.regions import build_regions_router
from app.controller.errors import ErrorHandlers
from app.controller.pilots.router import build_pilots_router
from app.controller.router import build_api_router
from app.controller.scenarios.router import build_scenarios_router
from app.repository.files.atlas import JsonAtlasRepository
from app.repository.files.pilots import JsonPilotRepository
from app.repository.files.scenario import FilesScenarioRepository
from app.settings import Settings, load_settings
from app.usecase.interface import AtlasRepository
from app.usecase.links import LinkQueries
from app.usecase.overview import OverviewQuery
from app.usecase.pilots import PilotQueries
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.scenarios import ScenarioQueries
from app.usecase.search import Search
from app.usecase.settlements import SettlementQueries


def build_atlas_routers(repository: AtlasRepository) -> list[APIRouter]:
    return [
        build_catalog_router(
            OverviewQuery(repository), ReferenceQueries(repository), Search(repository)
        ),
        build_regions_router(
            RegionQueries(repository), LinkQueries(repository), SettlementQueries(repository)
        ),
    ]


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or load_settings(os.environ)
    atlas = JsonAtlasRepository(config.data_dir)
    app = FastAPI(title="Plexus API", version="1.0.0")
    app.state.atlas = atlas
    ErrorHandlers(StdlibLogger("app")).register(app)
    pilots = PilotQueries(JsonPilotRepository(config.data_dir))
    scenarios = ScenarioQueries(FilesScenarioRepository(config.scenario_dir))
    app.include_router(
        build_api_router(
            *build_atlas_routers(atlas),
            build_pilots_router(pilots),
            build_scenarios_router(scenarios),
        )
    )
    return app
