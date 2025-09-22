from __future__ import annotations

"""
Database seeding utilities for static dimensions.

Idempotent upsert for `commodities` and `provinces`.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Iterable, Mapping

from sqlalchemy.orm import Session

from app.infra.models import Commodity, Province

logger = logging.getLogger(__name__)


def seed_provinces(db: Session, provinces: Iterable[Mapping[str, str]] | None = None) -> int:
    """Seed provinces table idempotently.

    Args:
        db: SQLAlchemy Session
        provinces: iterable of {"id": str, "name": str}. If None, seeds minimal defaults.

    Returns:
        Number of upserts performed.
    """
    items = list(
        provinces
        if provinces is not None
        else [
            {"id": "NATIONAL", "name": "National Aggregate"},
        ]
    )

    count = 0
    for it in items:
        obj = Province(id=str(it["id"]).strip(), name=str(it["name"]).strip())
        db.merge(obj)  # merge provides PK-based upsert semantics
        count += 1
    db.commit()
    return count


def seed_commodities(
    db: Session, commodities: Iterable[Mapping[str, str]] | None = None
) -> int:
    """Seed commodities table idempotently.

    Args:
        db: SQLAlchemy Session
        commodities: iterable of {"id": str, "name": str}. If None, seeds no defaults.

    Returns:
        Number of upserts performed.
    """
    items = list(commodities or [])
    count = 0
    for it in items:
        obj = Commodity(id=str(it["id"]).strip(), name=str(it["name"]).strip())
        db.merge(obj)
        count += 1
    if count:
        db.commit()
    return count


def seed_dimensions(
    db: Session,
    *,
    commodities: Iterable[Mapping[str, str]] | None = None,
    provinces: Iterable[Mapping[str, str]] | None = None,
) -> dict[str, int]:
    """Seed both commodities and provinces idempotently.

    Returns a summary dict of rows upserted per table.
    """
    up_commodities = seed_commodities(db, commodities)
    up_provinces = seed_provinces(db, provinces)
    return {"commodities": up_commodities, "provinces": up_provinces}


async def seed_administrative_data():
    """
    Seed administrative data (provinces, regencies, districts) from CSV files.

    This function is called during deployment to populate the database with
    Indonesian administrative divisions data.
    """
    from app.infra.db import get_engine

    logger.info("Starting administrative data seeding...")

    try:
        # Get database engine and create session
        engine = get_engine()
        with Session(engine) as db:
            # For now, seed with minimal provinces data
            # In production, you would load this from CSV files
            provinces_data = [
                {"id": "11", "name": "ACEH"},
                {"id": "12", "name": "SUMATERA UTARA"},
                {"id": "13", "name": "SUMATERA BARAT"},
                {"id": "14", "name": "RIAU"},
                {"id": "15", "name": "JAMBI"},
                {"id": "16", "name": "SUMATERA SELATAN"},
                {"id": "17", "name": "BENGKULU"},
                {"id": "18", "name": "LAMPUNG"},
                {"id": "19", "name": "KEPULAUAN BANGKA BELITUNG"},
                {"id": "21", "name": "KEPULAUAN RIAU"},
                {"id": "31", "name": "DKI JAKARTA"},
                {"id": "32", "name": "JAWA BARAT"},
                {"id": "33", "name": "JAWA TENGAH"},
                {"id": "34", "name": "DI YOGYAKARTA"},
                {"id": "35", "name": "JAWA TIMUR"},
                {"id": "36", "name": "BANTEN"},
                {"id": "51", "name": "BALI"},
                {"id": "52", "name": "NUSA TENGGARA BARAT"},
                {"id": "53", "name": "NUSA TENGGARA TIMUR"},
                {"id": "61", "name": "KALIMANTAN BARAT"},
                {"id": "62", "name": "KALIMANTAN TENGAH"},
                {"id": "63", "name": "KALIMANTAN SELATAN"},
                {"id": "64", "name": "KALIMANTAN TIMUR"},
                {"id": "65", "name": "KALIMANTAN UTARA"},
                {"id": "71", "name": "SULAWESI UTARA"},
                {"id": "72", "name": "SULAWESI TENGAH"},
                {"id": "73", "name": "SULAWESI SELATAN"},
                {"id": "74", "name": "SULAWESI TENGGARA"},
                {"id": "75", "name": "GORONTALO"},
                {"id": "76", "name": "SULAWESI BARAT"},
                {"id": "81", "name": "MALUKU"},
                {"id": "82", "name": "MALUKU UTARA"},
                {"id": "91", "name": "PAPUA BARAT"},
                {"id": "94", "name": "PAPUA"},
            ]

            result = seed_provinces(db, provinces_data)
            logger.info(f"Successfully seeded {result} provinces")

            # TODO: Add regencies and districts seeding when CSV files are available
            # This would involve:
            # 1. Loading CSV files from a predefined location
            # 2. Parsing and validating the data
            # 3. Seeding regencies and districts tables

    except Exception as e:
        logger.error(f"Failed to seed administrative data: {e}")
        raise

    logger.info("Administrative data seeding completed successfully")


# For synchronous execution (used in deployment scripts)
def seed_administrative_data_sync():
    """Synchronous wrapper for seed_administrative_data."""
    asyncio.run(seed_administrative_data())
