#!/usr/bin/env python3
"""
Database migration script for production deployment.

This script runs Alembic migrations to ensure the database schema is up to date.
It's designed to be called from deployment scripts and CI/CD pipelines.
"""

import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from alembic import command
    from alembic.config import Config
    from app.common.logging import setup_logging
    from app.common.settings import get_settings

    def run_migrations():
        """Run database migrations using Alembic."""
        # Setup logging
        settings = get_settings()
        setup_logging(settings.LOG_LEVEL)
        logger = logging.getLogger(__name__)

        logger.info("Starting database migrations...")

        try:
            # Configure Alembic
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", "migrations")
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

            # Run migrations
            command.upgrade(alembic_cfg, "head")

            logger.info("Database migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False

    if __name__ == "__main__":
        success = run_migrations()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root with proper dependencies installed")
    sys.exit(1)
