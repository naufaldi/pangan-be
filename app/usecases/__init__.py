"""
Use cases (Application Layer).
This module contains application services that orchestrate domain logic.
All services are framework-agnostic and contain no external dependencies.
"""

from app.usecases.health_service import HealthService
from app.usecases.price_service import query_prices
from app.usecases.price_service_adapter import make_price_query_service, default_price_query_service

# Expose services for easy importing
health_service = HealthService()

__all__ = [
    "health_service",
    "HealthService",
    "query_prices",
    "make_price_query_service",
    "default_price_query_service"
]
