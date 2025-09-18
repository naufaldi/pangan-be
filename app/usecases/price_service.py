"""
Price service - Application layer for price query operations.
This service orchestrates price-related business logic in a framework-agnostic way.
"""

import logging
from datetime import date
from typing import Optional

from app.usecases.ports import (
    PaginatedPriceResult,
    PriceQuery,
    PriceRepositoryPort,
    ProvinceRepositoryPort,
    CommodityRepositoryPort,
)

logger = logging.getLogger(__name__)


def query_prices(
    *,
    price_repo: PriceRepositoryPort,
    commodity_repo: Optional[CommodityRepositoryPort] = None,
    province_repo: Optional[ProvinceRepositoryPort] = None,
    level_harga_id: int,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    commodity_id: Optional[str] = None,
    province_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedPriceResult:
    """
    Query prices with business logic validation and coordination.

    Args:
        price_repo: Repository for price data access
        commodity_repo: Optional repository for commodity validation
        province_repo: Optional repository for province validation
        level_harga_id: Price level identifier (required)
        period_start: Filter prices from this date
        period_end: Filter prices until this date
        commodity_id: Filter by commodity ID
        province_id: Filter by province ID
        limit: Number of records to return (max 1000)
        offset: Number of records to skip

    Returns:
        PaginatedPriceResult: Query results with metadata

    Raises:
        ValueError: For invalid input parameters
        RuntimeError: For repository or business logic errors
    """
    # Business logic validation
    _validate_query_parameters(
        level_harga_id=level_harga_id,
        period_start=period_start,
        period_end=period_end,
        commodity_id=commodity_id,
        province_id=province_id,
        limit=limit,
        offset=offset,
    )

    # Validate existence of referenced entities if repositories provided
    if commodity_id and commodity_repo:
        _validate_commodity_exists(commodity_repo, commodity_id)

    if province_id and province_repo:
        _validate_province_exists(province_repo, province_id)

    # Build query object
    query = PriceQuery(
        level_harga_id=level_harga_id,
        period_start=period_start,
        period_end=period_end,
        commodity_id=commodity_id,
        province_id=province_id,
        limit=limit,
        offset=offset,
    )

    try:
        # Execute query through repository
        result = price_repo.query(query)

        logger.info(
            "Price query executed successfully",
            extra={
                "level_harga_id": level_harga_id,
                "commodity_id": commodity_id,
                "province_id": province_id,
                "period_start": period_start.isoformat() if period_start else None,
                "period_end": period_end.isoformat() if period_end else None,
                "limit": limit,
                "offset": offset,
                "results_count": len(result.data),
                "total_count": result.total,
            }
        )

        return result

    except Exception as e:
        logger.error(
            "Price query failed",
            extra={
                "error": str(e),
                "level_harga_id": level_harga_id,
                "commodity_id": commodity_id,
                "province_id": province_id,
                "period_start": period_start.isoformat() if period_start else None,
                "period_end": period_end.isoformat() if period_end else None,
                "limit": limit,
                "offset": offset,
            },
            exc_info=True
        )
        raise RuntimeError(f"Failed to query prices: {str(e)}") from e


def _validate_query_parameters(
    *,
    level_harga_id: int,
    period_start: Optional[date],
    period_end: Optional[date],
    commodity_id: Optional[str],
    province_id: Optional[str],
    limit: int,
    offset: int,
) -> None:
    """
    Validate query parameters according to business rules.

    Args:
        level_harga_id: Price level identifier
        period_start: Start date filter
        period_end: End date filter
        commodity_id: Commodity filter
        province_id: Province filter
        limit: Result limit
        offset: Result offset

    Raises:
        ValueError: If validation fails
    """
    # Validate level_harga_id range
    if not (1 <= level_harga_id <= 5):
        raise ValueError(f"level_harga_id must be between 1 and 5, got {level_harga_id}")

    # Validate date range logic
    if period_start and period_end and period_end < period_start:
        raise ValueError("period_end must be after or equal to period_start")

    # Validate date range is reasonable (not too far in past/future)
    today = date.today()
    if period_start and (period_start.year < 2000 or period_start > today.replace(year=today.year + 1)):
        raise ValueError("period_start must be between 2000 and next year")

    if period_end and (period_end.year < 2000 or period_end > today.replace(year=today.year + 1)):
        raise ValueError("period_end must be between 2000 and next year")

    # Validate pagination parameters
    if limit < 1 or limit > 1000:
        raise ValueError(f"limit must be between 1 and 1000, got {limit}")

    if offset < 0:
        raise ValueError(f"offset must be non-negative, got {offset}")

    # Validate string parameters are reasonable length
    if commodity_id and len(commodity_id.strip()) == 0:
        raise ValueError("commodity_id cannot be empty")

    if province_id and len(province_id.strip()) == 0:
        raise ValueError("province_id cannot be empty")


def _validate_commodity_exists(commodity_repo: CommodityRepositoryPort, commodity_id: str) -> None:
    """
    Validate that a commodity exists.

    Args:
        commodity_repo: Repository for commodity data
        commodity_id: Commodity identifier to validate

    Raises:
        ValueError: If commodity doesn't exist
    """
    try:
        commodities = commodity_repo.list_all()
        commodity_ids = {c.id for c in commodities}

        if commodity_id not in commodity_ids:
            available_ids = sorted(list(commodity_ids))[:10]  # Show first 10 for error message
            raise ValueError(
                f"Commodity '{commodity_id}' not found. "
                f"Available commodities: {available_ids}"
            )
    except Exception as e:
        logger.warning(f"Failed to validate commodity existence: {e}")
        # Don't fail the query if validation fails, just log it


def _validate_province_exists(province_repo: ProvinceRepositoryPort, province_id: str) -> None:
    """
    Validate that a province exists.

    Args:
        province_repo: Repository for province data
        province_id: Province identifier to validate

    Raises:
        ValueError: If province doesn't exist
    """
    try:
        provinces = province_repo.list_all()
        province_ids = {p.id for p in provinces}

        if province_id not in province_ids:
            available_ids = sorted(list(province_ids))[:10]  # Show first 10 for error message
            raise ValueError(
                f"Province '{province_id}' not found. "
                f"Available provinces: {available_ids}"
            )
    except Exception as e:
        logger.warning(f"Failed to validate province existence: {e}")
        # Don't fail the query if validation fails, just log it
