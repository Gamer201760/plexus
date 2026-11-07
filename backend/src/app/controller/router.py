from fastapi import APIRouter

from app.controller.health.router import router as health_router


def build_api_router(*features: APIRouter) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(health_router)
    for feature in features:
        router.include_router(feature)
    return router
