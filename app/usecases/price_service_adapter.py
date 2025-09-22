"""
Price service adapter - Dependency injection adapter for price services.
This module provides factory functions to create price services with injected dependencies.
"""

from datetime import date
from typing import Callable, Optional

from app.usecases.ports import (
    CommodityRepositoryPort,
    PaginatedPriceResult,
    PriceQuery,
    PriceRepositoryPort,
    ProvinceRepositoryPort,
)
from app.usecases.price_service import query_prices
from app.infra.repositories.commodities import make_commodity_repository
from app.infra.repositories.prices import make_price_repository
from app.infra.repositories.provinces import make_province_repository
from app.infra.db import get_engine


def make_price_query_service(
    *,
    price_repo: Optional[PriceRepositoryPort] = None,
    commodity_repo: Optional[CommodityRepositoryPort] = None,
    province_repo: Optional[ProvinceRepositoryPort] = None,
) -> Callable[..., PaginatedPriceResult]:
    """
    Factory function to create a price query service with injected dependencies.

    Args:
        price_repo: Optional price repository (will create default if None)
        commodity_repo: Optional commodity repository (will create default if None)
        province_repo: Optional province repository (will create default if None)

    Returns:
        Callable that accepts price query parameters and returns results
    """
    # Create repositories if not provided
    if price_repo is None:
        engine = get_engine()
        price_repo = make_price_repository(engine=engine)

    if commodity_repo is None:
        engine = get_engine()
        commodity_repo = make_commodity_repository(engine=engine)

    if province_repo is None:
        engine = get_engine()
        province_repo = make_province_repository(engine=engine)

    def price_query_service(
        *,
        level_harga_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        commodity_id: Optional[str] = None,
        province_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedPriceResult:
        """
        Query prices with validation and business logic.

        This is a thin adapter around the functional query_prices service
        that provides a clean interface for dependency injection.
        """
        return query_prices(
            price_repo=price_repo,
            commodity_repo=commodity_repo,
            province_repo=province_repo,
            level_harga_id=level_harga_id,
            period_start=period_start,
            period_end=period_end,
            commodity_id=commodity_id,
            province_id=province_id,
            limit=limit,
            offset=offset,
        )

    return price_query_service


# Create a default instance for convenience
default_price_query_service = make_price_query_service()
