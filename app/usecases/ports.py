from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Callable, Iterable, Mapping, Sequence

"""
Use case layer ports (interfaces) and DTO types.

These ports define framework-agnostic contracts that adapters in `app/infra/`
must implement. Data shapes follow the RORO (Receive an Object, Return an
Object) pattern.

Notes:
- Keep ports synchronous to match current sync SQLAlchemy usage. FastAPI will
  run sync path operations in a threadpool. If we migrate to async DB/HTTP,
  we can introduce async variants without breaking call sites.
"""


# -------------------------
# DTOs (request/response)
# -------------------------


@dataclass(frozen=True)
class FetchParams:
    """Parameters for upstream fetch.

    period_start/end should represent the desired window in YYYY-MM-DD date
    semantics; the upstream may also require start_year/end_year as hints.
    province_id is optional; default behavior is NATIONAL aggregation.
    """

    start_year: int
    end_year: int
    period_start: date
    period_end: date
    level_harga_id: int
    province_id: str | None = None


@dataclass(frozen=True)
class PriceUpsertRow:
    """Normalized monthly price fact intended for upsert."""

    commodity_id: str
    province_id: str
    level_harga_id: int
    period_start: date
    period_end: date
    price: Decimal
    unit: str
    checksum: str | None = None


@dataclass(frozen=True)
class PriceRecord:
    """Record returned from queries. `id` may map to a DB surrogate key.

    Includes joined commodity and province names for API responses.
    """

    id: int | None
    commodity_id: str
    commodity_name: str  # Added for API responses (joined from commodities table)
    province_id: str
    province_name: str   # Added for API responses (joined from provinces table)
    level_harga_id: int
    period_start: date
    period_end: date
    price: Decimal
    unit: str


@dataclass(frozen=True)
class PriceQuery:
    """Filters and pagination for querying prices."""

    level_harga_id: int
    period_start: date | None = None
    period_end: date | None = None
    commodity_id: str | None = None
    province_id: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class UpsertSummary:
    inserted: int
    updated: int
    unchanged: int


@dataclass(frozen=True)
class CommodityDTO:
    id: str
    name: str


@dataclass(frozen=True)
class ProvinceDTO:
    id: str
    name: str


@dataclass(frozen=True)
class PaginatedPriceResult:
    """Result wrapper for paginated price queries."""

    data: Sequence[PriceRecord]
    total: int
    limit: int
    offset: int


# -------------------------
# Ports (interfaces)
# -------------------------


# ------------------------------------
# Functional ports (records of callables)
# ------------------------------------

# Callable aliases
UpstreamFetchFn = Callable[[FetchParams], Mapping]
UpstreamTestConnectionFn = Callable[[], bool]
UpsertManyFn = Callable[[Iterable[PriceUpsertRow]], UpsertSummary]
QueryPricesFn = Callable[[PriceQuery], PaginatedPriceResult]  # Updated to use structured result
ListCommoditiesFn = Callable[[], Sequence[CommodityDTO]]
ListProvincesFn = Callable[[], Sequence[ProvinceDTO]]


@dataclass(frozen=True)
class UpstreamClientPort:
    fetch: UpstreamFetchFn
    test_connection: UpstreamTestConnectionFn


@dataclass(frozen=True)
class PriceRepositoryPort:
    upsert_many: UpsertManyFn
    query: QueryPricesFn


@dataclass(frozen=True)
class CommodityRepositoryPort:
    list_all: ListCommoditiesFn


@dataclass(frozen=True)
class ProvinceRepositoryPort:
    list_all: ListProvincesFn
