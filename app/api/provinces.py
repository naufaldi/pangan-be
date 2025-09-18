"""
Provinces API endpoints.

This module provides endpoints for retrieving province information.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.infra.db import get_engine
from app.infra.repositories.provinces import make_province_repository
from app.usecases.ports import ProvinceRepositoryPort
from pydantic import BaseModel


# Logger setup
logger = logging.getLogger(__name__)


# Pydantic response models
class ProvinceResponse(BaseModel):
    """Response model for province data."""

    id: str
    name: str

    class Config:
        from_attributes = True


# Dependency injection
def get_province_repository() -> ProvinceRepositoryPort:
    """Get province repository instance."""
    engine = get_engine()
    return make_province_repository(engine=engine)


# Router
router = APIRouter(
    prefix="/provinces",
    tags=["Provinces"],
    responses={
        404: {"description": "Provinces not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "",
    response_model=List[ProvinceResponse],
    summary="Get all provinces",
    description="""
    Retrieve a list of all available provinces in the system.

    This endpoint returns all provinces that have price data available.
    Each province includes its unique identifier and display name.

    **Example Response:**
    ```json
    [
        {
            "id": "NATIONAL",
            "name": "National Aggregate"
        }
    ]
    ```
    """,
)
def get_provinces(
    province_repo: ProvinceRepositoryPort = Depends(get_province_repository),
) -> List[ProvinceResponse]:
    """
    Get all provinces.

    Args:
        province_repo: Repository for province data access

    Returns:
        List of all provinces with their IDs and names

    Raises:
        HTTPException: If there's an error retrieving provinces
    """
    try:
        logger.info("Fetching all provinces")

        # Get all provinces from repository
        provinces = province_repo.list_all()

        if not provinces:
            logger.warning("No provinces found in database")
            raise HTTPException(
                status_code=404,
                detail="No provinces found",
            )

        # Convert to response models
        response_data = [
            ProvinceResponse(id=province.id, name=province.name)
            for province in provinces
        ]

        logger.info(
            "Provinces retrieved successfully",
            extra={"province_count": len(response_data)}
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve provinces",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving provinces",
        )
