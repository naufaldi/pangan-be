"""
Commodities API endpoints.

This module provides endpoints for retrieving commodity information.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

# Logger setup
logger = logging.getLogger(__name__)
from app.infra.db import get_engine
from app.infra.repositories.commodities import make_commodity_repository
from app.usecases.ports import CommodityRepositoryPort
from pydantic import BaseModel


# Pydantic response models
class CommodityResponse(BaseModel):
    """Response model for commodity data."""

    id: str
    name: str

    class Config:
        from_attributes = True


# Dependency injection
def get_commodity_repository() -> CommodityRepositoryPort:
    """Get commodity repository instance."""
    engine = get_engine()
    return make_commodity_repository(engine=engine)


# Router
router = APIRouter(
    prefix="/commodities",
    tags=["Commodities"],
    responses={
        404: {"description": "Commodities not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "",
    response_model=List[CommodityResponse],
    summary="Get all commodities",
    description="""
    Retrieve a list of all available commodities in the system.

    This endpoint returns all commodities that have price data available.
    Each commodity includes its unique identifier and display name.

    **Example Response:**
    ```json
    [
        {
            "id": "27",
            "name": "Beras Premium"
        },
        {
            "id": "28",
            "name": "Beras Medium"
        }
    ]
    ```
    """,
)
def get_commodities(
    commodity_repo: CommodityRepositoryPort = Depends(get_commodity_repository),
) -> List[CommodityResponse]:
    """
    Get all commodities.

    Args:
        commodity_repo: Repository for commodity data access

    Returns:
        List of all commodities with their IDs and names

    Raises:
        HTTPException: If there's an error retrieving commodities
    """
    try:
        logger.info("Fetching all commodities")

        # Get all commodities from repository
        commodities = commodity_repo.list_all()

        if not commodities:
            logger.warning("No commodities found in database")
            raise HTTPException(
                status_code=404,
                detail="No commodities found",
            )

        # Convert to response models
        response_data = [
            CommodityResponse(id=commodity.id, name=commodity.name)
            for commodity in commodities
        ]

        logger.info(
            "Commodities retrieved successfully",
            extra={"commodity_count": len(response_data)}
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve commodities",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving commodities",
        )
