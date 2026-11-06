from fastapi import APIRouter

from app.controller.health.router import router as health_router

api_router_v1 = APIRouter(prefix="/api/v1")
api_router_v1.include_router(health_router)
