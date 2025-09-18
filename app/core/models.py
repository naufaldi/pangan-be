"""
Core domain models and value objects.
This module contains the fundamental business entities and value objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass(frozen=True)
class Commodity:
    """Domain model for commodity (food item)."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Province:
    """Domain model for province."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PriceData:
    """Domain model for price data point."""

    commodity_id: str
    province_id: str
    level_harga_id: int
    period_start: datetime
    period_end: datetime
    price: Decimal
    unit: str
    created_at: datetime
    updated_at: datetime
    checksum: Optional[str] = None


@dataclass(frozen=True)
class HealthStatus:
    """Domain model for health check status."""

    status: str
    timestamp: datetime
    is_ready: bool
