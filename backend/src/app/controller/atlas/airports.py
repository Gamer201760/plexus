from fastapi import APIRouter

from app.usecase.airports import AirportCatalog, AirportQueries


def build_airports_router(airports: AirportQueries) -> APIRouter:
    router = APIRouter(tags=["airports"])

    @router.get("/airports", response_model=AirportCatalog)
    def catalog() -> AirportCatalog:
        return airports.result

    return router
