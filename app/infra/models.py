from __future__ import annotations

from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class Commodity(Base):
    __tablename__ = "commodities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    prices: Mapped[list["PriceMonthly"]] = relationship(back_populates="commodity")


class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    prices: Mapped[list["PriceMonthly"]] = relationship(back_populates="province")


class PriceMonthly(Base):
    __tablename__ = "prices_monthly"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    commodity_id: Mapped[str] = mapped_column(String, ForeignKey("commodities.id"))
    province_id: Mapped[str] = mapped_column(String, ForeignKey("provinces.id"))
    level_harga_id: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[str | None] = mapped_column(Text, nullable=True)
    inserted_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    commodity: Mapped[Commodity] = relationship(back_populates="prices")
    province: Mapped[Province] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint(
            "commodity_id",
            "province_id",
            "level_harga_id",
            "period_start",
            "period_end",
            name="uq_prices_monthly_unique_window",
        ),
        CheckConstraint("period_start <= period_end", name="ck_period_order"),
    )
