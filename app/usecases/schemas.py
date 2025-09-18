from __future__ import annotations

"""
Schemas for ingestion pipeline validation (upstream payload and normalized rows).
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UpstreamProvincePrice(BaseModel):
    model_config = ConfigDict(extra="allow")

    satuan: str = Field(default="")


class UpstreamCommodityRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    commodity_id: str = Field(alias="Komoditas_id")
    name: Optional[str] = Field(default=None, alias="Komoditas")
    year: Optional[int] = Field(default=None, alias="Tahun")
    today_province_price: Optional[UpstreamProvincePrice] = None
    Jan: Optional[Decimal] = None
    Feb: Optional[Decimal] = None
    Mar: Optional[Decimal] = None
    Apr: Optional[Decimal] = None
    Mei: Optional[Decimal] = None
    Jun: Optional[Decimal] = None
    Jul: Optional[Decimal] = None
    Agu: Optional[Decimal] = None
    Sep: Optional[Decimal] = None
    Okt: Optional[Decimal] = None
    Nov: Optional[Decimal] = None
    Des: Optional[Decimal] = None

    @field_validator('commodity_id', mode='before')
    @classmethod
    def convert_commodity_id_to_str(cls, v):
        return str(v) if v is not None else v


class UpstreamPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_data: Mapping[str, Any]
    data: Mapping[str, list[UpstreamCommodityRecord]]


class NormalizedPriceRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commodity_id: str
    province_id: str
    level_harga_id: int
    period_start: date
    period_end: date
    price: Decimal
    unit: str
    checksum: Optional[str] = None


