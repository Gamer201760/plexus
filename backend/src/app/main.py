import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.tools import AtlasTools
from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_analysis.jobs import AnalysisJobs
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.controller.atlas.catalog import build_catalog_router
from app.controller.atlas.regions import build_regions_router
from app.controller.chat.router import build_chat_router
from app.controller.errors import ErrorHandlers
from app.controller.road_analysis.router import build_analysis_router
from app.controller.road_graph.compression import RoadGraphCompression
from app.controller.road_graph.router import build_road_graph_router
from app.controller.router import build_api_router
from app.controller.scenarios.router import build_scenarios_router
from app.controller.scenarios.sensitivity import build_sensitivity_router
from app.repository.files.atlas import JsonAtlasRepository
from app.repository.files.road_analysis import FileAnalysisStore
from app.repository.files.scenario import FilesScenarioRepository
from app.repository.files.snapshot import SnapshotAtlasRepository
from app.settings import Settings, load_settings
from app.usecase.chat import Chat
from app.usecase.interface import AtlasRepository
from app.usecase.links import LinkQueries
from app.usecase.overview import OverviewQuery
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.scenarios import ScenarioQueries
from app.usecase.search import Search
from app.usecase.sensitivity import AccessibilitySensitivity
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
    atlas = (
        SnapshotAtlasRepository(config.data_dir, config.graph_dir)
        if config.graph_dir
        else JsonAtlasRepository(config.data_dir)
    )
    road_jobs = RoadJobs(config.graph_dir) if config.graph_dir else None
    road_graph = RoadGraph(road_jobs, atlas)
    analysis_jobs = (
        AnalysisJobs(road_jobs, FileAnalysisStore(config.graph_dir))
        if road_jobs and config.graph_dir
        else None
    )
    analysis = RoadAnalysis(analysis_jobs, atlas)
    corridors = RoadCorridors(CorridorResolver(road_jobs) if road_jobs else None)
    sensitivity = AccessibilitySensitivity(atlas)
    scenarios = ScenarioQueries(FilesScenarioRepository(config.scenario_dir))
    gateway = (
        CodexResponsesGateway(
            AtlasTools(
                RegionQueries(atlas),
                LinkQueries(atlas),
                SettlementQueries(atlas),
                Search(atlas),
                ReferenceQueries(atlas),
                CalculationTools(
                    sensitivity, road_graph if road_jobs else None, analysis, corridors
                ),
            )
        )
        if config.chat_enabled
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        if analysis_jobs is not None:
            analysis_jobs.close()
        if road_jobs is not None:
            road_jobs.close()
        if gateway is not None:
            await gateway.close()

    app = FastAPI(title="Plexus API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(RoadGraphCompression, minimum_size=1000, compresslevel=3)
    app.state.atlas = atlas
    ErrorHandlers(StdlibLogger("app")).register(app)
    app.include_router(
        build_api_router(
            *build_atlas_routers(atlas),
            build_scenarios_router(scenarios),
            build_sensitivity_router(sensitivity),
            build_chat_router(Chat(gateway)),
        )
    )
    app.include_router(build_road_graph_router(road_graph), prefix="/api/v1")
    app.include_router(build_analysis_router(analysis), prefix="/api/v1")
    return app
