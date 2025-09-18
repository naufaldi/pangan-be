from __future__ import annotations

"""
Database seeding utilities for static dimensions.

Idempotent upsert for `commodities` and `provinces`.
"""

from typing import Iterable, Mapping

from sqlalchemy.orm import Session

from app.infra.models import Commodity, Province


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

