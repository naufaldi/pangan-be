"""
API Interface Layer (Presentation Layer).
Contains FastAPI routers, request/response DTOs, and HTTP-related logic.
This layer depends on the use cases layer but not vice versa.
"""

from app.api.router import api_router
from app.api.schemas import HealthResponse, ErrorResponse

__all__ = ["api_router", "HealthResponse", "ErrorResponse"]
