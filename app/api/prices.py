"""
Prices API endpoints following clean architecture.
This module handles HTTP requests for price data and delegates to the use case layer.
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.schemas import PaginatedPriceResponse
from app.usecases import price_service
from app.usecases.ports import PriceRepositoryPort, CommodityRepositoryPort, ProvinceRepositoryPort
from app.infra.repositories.prices import make_price_repository
from app.infra.repositories.commodities import make_commodity_repository
from app.infra.repositories.provinces import make_province_repository
from app.infra.db import get_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prices", tags=["prices"])


def get_price_repository() -> PriceRepositoryPort:
    """Dependency injection for price repository."""
    engine = get_engine()
    return make_price_repository(engine=engine)


def get_commodity_repository() -> CommodityRepositoryPort:
    """Dependency injection for commodity repository."""
    engine = get_engine()
    return make_commodity_repository(engine=engine)


def get_province_repository() -> ProvinceRepositoryPort:
    """Dependency injection for province repository."""
    engine = get_engine()
    return make_province_repository(engine=engine)


@router.get(
    "",
    summary="Query price data with filters and pagination",
    response_model=PaginatedPriceResponse,
    responses={
        200: {
            "description": "Successful price query",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "commodity_id": "01",
                                "commodity_name": "Beras",
                                "province_id": "NATIONAL",
                                "province_name": "National",
                                "level_harga_id": 3,
                                "period_start": "2024-11-01",
                                "period_end": "2024-11-30",
                                "price": 9500.0,
                                "unit": "Rp./Kg"
                            }
                        ],
                        "total": 1,
                        "limit": 50,
                        "offset": 0
                    }
                }
            }
        },
        400: {
            "description": "Invalid query parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "level_harga_id must be between 1 and 5"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "period_end must be after or equal to period_start"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to query prices: database connection error"}
                }
            }
        }
    }
)
async def get_prices(
    # Query parameters with validation
    level_harga_id: int = Query(..., description="Price level identifier (1-5)", ge=1, le=5),
    commodity_id: Optional[str] = Query(None, description="Filter by commodity ID"),
    province_id: Optional[str] = Query(None, description="Filter by province ID"),
    period_start: Optional[date] = Query(None, description="Filter prices from this date (YYYY-MM-DD)"),
    period_end: Optional[date] = Query(None, description="Filter prices until this date (YYYY-MM-DD)"),
    limit: int = Query(50, description="Number of records to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of records to skip", ge=0),
    # Dependency injection
    price_repo: PriceRepositoryPort = Depends(get_price_repository),
    commodity_repo: Optional[CommodityRepositoryPort] = Depends(get_commodity_repository),
    province_repo: Optional[ProvinceRepositoryPort] = Depends(get_province_repository),
):
    """
    Query price data with comprehensive filtering and pagination.

    **Required Parameters:**
    - `level_harga_id`: Price level identifier (1-5)

    **Optional Filters:**
    - `commodity_id`: Filter by specific commodity
    - `province_id`: Filter by specific province
    - `period_start`: Filter prices from this date
    - `period_end`: Filter prices until this date

    **Pagination:**
    - `limit`: Number of records per page (1-1000, default: 50)
    - `offset`: Number of records to skip (default: 0)

    **Sorting:**
    - Results are sorted by period_start in descending order (most recent first)

    **Examples:**

    Get latest 10 consumer-level (level 3) prices:
    ```
    GET /prices?level_harga_id=3&limit=10
    ```

    Get rice prices for November 2024:
    ```
    GET /prices?level_harga_id=3&commodity_id=01&period_start=2024-11-01&period_end=2024-11-30
    ```

    Get prices with pagination:
    ```
    GET /prices?level_harga_id=3&limit=50&offset=100
    ```
    """
    try:
        # Delegate to use case layer
        result = price_service.query_prices(
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

        # Convert to API response format
        response_data = {
            "data": [
                {
                    "id": record.id,
                    "commodity_id": record.commodity_id,
                    "commodity_name": record.commodity_name,
                    "province_id": record.province_id,
                    "province_name": record.province_name,
                    "level_harga_id": record.level_harga_id,
                    "period_start": record.period_start.isoformat(),
                    "period_end": record.period_end.isoformat(),
                    "price": float(record.price),  # Convert Decimal to float for JSON
                    "unit": record.unit,
                }
                for record in result.data
            ],
            "total": result.total,
            "limit": result.limit,
            "offset": result.offset,
        }

        return JSONResponse(content=response_data)

    except ValueError as e:
        # Business logic validation errors
        logger.warning(f"Price query validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # System errors (database, etc.)
        logger.error(f"Price query system error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in price query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )
