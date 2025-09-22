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

# Configure CORS based on environment
if settings.ENV == "development":
    # Development: Allow all origins for local development
    allow_origins = ["*"]
    allow_credentials = True
else:
    # Production: Restrict to specific domains for security
    # You can configure this via ALLOWED_ORIGINS environment variable
    allowed_origins_env = settings.__dict__.get("ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        allow_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
    else:
        # Default production origins - update these for your domain
        allow_origins = [
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            "https://api.yourdomain.com"
        ]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
