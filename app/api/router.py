from fastapi import APIRouter
from app.api.health import router as health_router

# Main API router that includes all sub-routers
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router)
