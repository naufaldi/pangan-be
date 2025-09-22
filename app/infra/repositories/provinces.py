from __future__ import annotations

from sqlalchemy import asc, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.infra.models import Province
from app.usecases.ports import ProvinceDTO, ProvinceRepositoryPort

"""
SQLAlchemy-backed Province repository adapter (functional port).
"""


def make_province_repository(*, engine: Engine) -> ProvinceRepositoryPort:
    def list_all() -> list[ProvinceDTO]:
        with Session(bind=engine, future=True) as db:
            rows = db.execute(
                select(Province).order_by(asc(Province.name))
            ).scalars().all()
            return [ProvinceDTO(id=r.id, name=r.name) for r in rows]

    return ProvinceRepositoryPort(list_all=list_all)

