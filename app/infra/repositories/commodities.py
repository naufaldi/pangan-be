from __future__ import annotations

"""
SQLAlchemy-backed Commodity repository adapter (functional port).
"""

from sqlalchemy import asc, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.infra.models import Commodity
from app.usecases.ports import CommodityDTO, CommodityRepositoryPort


def make_commodity_repository(*, engine: Engine) -> CommodityRepositoryPort:
    def list_all() -> list[CommodityDTO]:
        with Session(bind=engine, future=True) as db:
            rows = db.execute(
                select(Commodity).order_by(asc(Commodity.name))
            ).scalars().all()
            return [CommodityDTO(id=r.id, name=r.name) for r in rows]

    return CommodityRepositoryPort(list_all=list_all)

