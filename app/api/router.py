from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.prices import router as prices_router
from app.api.commodities import router as commodities_router
from app.api.provinces import router as provinces_router

# Main API router that includes all sub-routers
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router)
api_router.include_router(prices_router)
api_router.include_router(commodities_router)
api_router.include_router(provinces_router)
