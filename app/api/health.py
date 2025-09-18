"""
Health API endpoints following clean architecture.
This module handles HTTP requests and delegates to the use case layer.
"""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.usecases import health_service
from app.api.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/healthz", summary="Liveness probe", response_model=HealthResponse)
async def healthz():
    """
    Liveness probe endpoint.
    Returns 200 when the application is running.
    Used by orchestrators to determine if the application should be restarted.
    """
    try:
        health_status = health_service.get_liveness_status()
        return JSONResponse(
            {
                "status": health_status.status,
                "timestamp": health_status.timestamp.isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            {"status": "error", "detail": "Health check failed"}, status_code=500
        )


@router.get("/readyz", summary="Readiness probe", response_model=HealthResponse)
async def readyz():
    """
    Readiness probe endpoint.
    Returns 503 if the application is not ready to serve traffic.
    Used by load balancers to determine if the application should receive traffic.
    """
    try:
        health_status = health_service.get_readiness_status()

        if not health_status.is_ready:
            return JSONResponse(
                {
                    "status": "starting",
                    "timestamp": health_status.timestamp.isoformat(),
                },
                status_code=503,
            )

        return JSONResponse(
            {
                "status": health_status.status,
                "timestamp": health_status.timestamp.isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            {"status": "error", "detail": "Readiness check failed"}, status_code=503
        )
