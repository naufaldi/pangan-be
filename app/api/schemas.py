"""
API Schemas (DTOs) for request/response validation.
This module contains Pydantic models for API data transfer objects.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Response model for health endpoints."""

    status: str


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    detail: str


class PriceQueryParams(BaseModel):
    """Query parameters for GET /prices endpoint.

    Using Pydantic BaseModel provides:
    - Automatic validation and type coercion
    - OpenAPI schema generation
    - IDE autocomplete and refactoring support
    - Runtime type checking
    """

    level_harga_id: int = Field(..., description="Price level identifier (1-5)", ge=1, le=5)
    commodity_id: Optional[str] = Field(None, description="Filter by commodity ID")
    province_id: Optional[str] = Field(None, description="Filter by province ID")
    period_start: Optional[date] = Field(None, description="Filter prices from this date (YYYY-MM-DD)")
    period_end: Optional[date] = Field(None, description="Filter prices until this date (YYYY-MM-DD)")
    limit: int = Field(50, description="Number of records to return", ge=1, le=1000)
    offset: int = Field(0, description="Number of records to skip", ge=0)

    @field_validator("period_end")
    @classmethod
    def validate_period_range(cls, v, info):
        """Validate that period_end is not before period_start if both are provided."""
        if v is not None and info.data.get("period_start") is not None:
            if v < info.data["period_start"]:
                raise ValueError("period_end must be after or equal to period_start")
        return v


class PriceResponse(BaseModel):
    """Response model for individual price records."""

    id: int = Field(..., description="Unique price record identifier")
    commodity_id: str = Field(..., description="Commodity identifier")
    commodity_name: str = Field(..., description="Commodity name")
    province_id: str = Field(..., description="Province identifier")
    province_name: str = Field(..., description="Province name")
    level_harga_id: int = Field(..., description="Price level identifier")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    price: float = Field(..., description="Price value", gt=0)
    unit: str = Field(..., description="Price unit (e.g., Rp./Kg)")


class PaginatedPriceResponse(BaseModel):
    """Paginated response wrapper for price records."""

    data: List[PriceResponse] = Field(..., description="List of price records")
    total: int = Field(..., description="Total number of records matching the query", ge=0)
    limit: int = Field(..., description="Number of records per page", ge=1, le=1000)
    offset: int = Field(..., description="Number of records skipped", ge=0)
