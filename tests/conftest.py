"""
Test configuration and fixtures for Pangan Indonesia API tests.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from app.usecases.ports import (
    PriceRecord,
    CommodityDTO,
    ProvinceDTO,
    PaginatedPriceResult,
    PriceRepositoryPort,
    CommodityRepositoryPort,
    ProvinceRepositoryPort,
)


@pytest.fixture
def sample_price_records():
    """Sample price records for testing."""
    return [
        PriceRecord(
            id=1,
            commodity_id="01",
            commodity_name="Beras",
            province_id="NATIONAL",
            province_name="National Aggregate",
            level_harga_id=3,
            period_start=date(2024, 11, 1),
            period_end=date(2024, 11, 30),
            price=9500.0,
            unit="Rp./Kg"
        ),
        PriceRecord(
            id=2,
            commodity_id="02",
            commodity_name="Jagung",
            province_id="NATIONAL",
            province_name="National Aggregate",
            level_harga_id=3,
            period_start=date(2024, 11, 1),
            period_end=date(2024, 11, 30),
            price=4500.0,
            unit="Rp./Kg"
        )
    ]


@pytest.fixture
def sample_commodities():
    """Sample commodities for testing."""
    return [
        CommodityDTO(id="01", name="Beras"),
        CommodityDTO(id="02", name="Jagung"),
        CommodityDTO(id="03", name="Gandum")
    ]


@pytest.fixture
def sample_provinces():
    """Sample provinces for testing."""
    return [
        ProvinceDTO(id="NATIONAL", name="National Aggregate"),
        ProvinceDTO(id="11", name="Aceh"),
        ProvinceDTO(id="12", name="Sumatera Utara")
    ]


@pytest.fixture
def mock_price_repository(sample_price_records):
    """Mock price repository for unit testing."""
    repo = Mock()
    repo.query.return_value = PaginatedPriceResult(
        data=sample_price_records,
        total=len(sample_price_records),
        limit=50,
        offset=0
    )
    return repo


@pytest.fixture
def mock_commodity_repository(sample_commodities):
    """Mock commodity repository for unit testing."""
    repo = Mock()
    repo.list_all.return_value = sample_commodities
    return repo


@pytest.fixture
def mock_province_repository(sample_provinces):
    """Mock province repository for unit testing."""
    repo = Mock()
    repo.list_all.return_value = sample_provinces
    return repo
