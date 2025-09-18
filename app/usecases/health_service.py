"""
Health service - Application layer for health check operations.
This service orchestrates health-related business logic in a framework-agnostic way.
"""

from datetime import datetime
from sqlalchemy import text
import logging
from app.core.models import HealthStatus
from app.lifespan import is_ready
from app.infra.db import get_engine


class HealthService:
    """Service for handling health check operations."""

    def get_liveness_status(self) -> HealthStatus:
        """
        Get liveness status - indicates if the application is running.
        This is a simple always-healthy check.
        """
        return HealthStatus(status="ok", timestamp=datetime.now(), is_ready=True)

    def get_readiness_status(self) -> HealthStatus:
        """
        Get readiness status - indicates if the application is ready to serve traffic.
        This checks if all required services are available.
        """
        app_ready = is_ready()
        db_ready = False
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ready = True
        except Exception as e:
            logging.getLogger(__name__).error("DB readiness check failed: %s", e)
            db_ready = False

        is_ok = app_ready and db_ready
        return HealthStatus(
            status="ready" if is_ok else "starting",
            timestamp=datetime.now(),
            is_ready=is_ok,
        )
