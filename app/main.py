"""
Main FastAPI application with clean architecture.
This is the composition root where all layers are wired together.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.common.settings import get_settings
from app.lifespan import lifespan_context
from app.common.logging import setup_logging
from app.api.router import api_router
import logging

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("pangan")

# Create FastAPI application
app = FastAPI(
    title="Pangan Indonesia Data Cache & API",
    version="0.1.0",
    description="Clean Architecture API for Indonesian food price data",
    lifespan=lifespan_context,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware for request/response logging with correlation ID."""
    from starlette.responses import Response

    request_id = request.headers.get("X-Request-ID")
    logger.info(
        {
            "event": "request_start",
            "method": request.method,
            "path": request.url.path,
            "request_id": request_id,
        }
    )

    response: Response = await call_next(request)

    logger.info(
        {
            "event": "request_end",
            "status_code": response.status_code,
            "path": request.url.path,
            "request_id": request_id,
        }
    )

    return response
