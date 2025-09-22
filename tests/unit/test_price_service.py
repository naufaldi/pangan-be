"""
Unit tests for price service business logic.
Tests validation, error handling, and core functionality without external dependencies.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from app.usecases import price_service
from app.usecases.ports import PaginatedPriceResult


class TestPriceServiceValidation:
    """Test price service validation functions."""

    def test_validate_query_parameters_valid(self):
        """Test validation with valid parameters."""
        price_service._validate_query_parameters(
            level_harga_id=3,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            commodity_id="01",
            province_id="NATIONAL",
            limit=50,
            offset=0
        )
        # Should not raise any exception

    def test_validate_level_harga_id_too_low(self):
        """Test validation with level_harga_id below minimum."""
        with pytest.raises(ValueError, match="level_harga_id must be between 1 and 5"):
            price_service._validate_query_parameters(
                level_harga_id=0,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_level_harga_id_too_high(self):
        """Test validation with level_harga_id above maximum."""
        with pytest.raises(ValueError, match="level_harga_id must be between 1 and 5"):
            price_service._validate_query_parameters(
                level_harga_id=6,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_period_end_before_start(self):
        """Test validation when period_end is before period_start."""
        with pytest.raises(ValueError, match="period_end must be after or equal to period_start"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=date(2024, 12, 31),
                period_end=date(2024, 1, 1),
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_period_start_too_old(self):
        """Test validation when period_start is too far in the past."""
        with pytest.raises(ValueError, match="period_start must be between 2000 and next year"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=date(1999, 1, 1),
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_period_start_too_future(self):
        """Test validation when period_start is too far in the future."""
        future_year = date.today().replace(year=date.today().year + 2)
        with pytest.raises(ValueError, match="period_start must be between 2000 and next year"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=future_year,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_limit_too_low(self):
        """Test validation when limit is below minimum."""
        with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=0,
                offset=0
            )

    def test_validate_limit_too_high(self):
        """Test validation when limit exceeds maximum."""
        with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=1001,
                offset=0
            )

    def test_validate_offset_negative(self):
        """Test validation when offset is negative."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id=None,
                limit=50,
                offset=-1
            )

    def test_validate_commodity_id_empty(self):
        """Test validation when commodity_id is empty string."""
        with pytest.raises(ValueError, match="commodity_id cannot be empty"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=None,
                period_end=None,
                commodity_id="   ",  # whitespace only should also fail
                province_id=None,
                limit=50,
                offset=0
            )

    def test_validate_province_id_empty(self):
        """Test validation when province_id is empty string."""
        with pytest.raises(ValueError, match="province_id cannot be empty"):
            price_service._validate_query_parameters(
                level_harga_id=3,
                period_start=None,
                period_end=None,
                commodity_id=None,
                province_id="   ",  # whitespace only
                limit=50,
                offset=0
            )


class TestCommodityValidation:
    """Test commodity validation functions."""

    def test_validate_commodity_exists_success(self, sample_commodities):
        """Test successful commodity validation."""
        mock_repo = Mock()
        mock_repo.list_all.return_value = sample_commodities

        # Should not raise exception for valid commodity
        price_service._validate_commodity_exists(mock_repo, "01")

    def test_validate_commodity_not_found(self, sample_commodities):
        """Test commodity validation when commodity doesn't exist."""
        mock_repo = Mock()
        mock_repo.list_all.return_value = sample_commodities

        # Should not raise error - validation is optional and logs warning
        price_service._validate_commodity_exists(mock_repo, "99")
        # Test passes if no exception is raised

    def test_validate_commodity_repo_error(self):
        """Test commodity validation when repository fails."""
        mock_repo = Mock()
        mock_repo.list_all.side_effect = Exception("Database error")

        # Should not raise exception - validation is optional
        price_service._validate_commodity_exists(mock_repo, "01")


class TestProvinceValidation:
    """Test province validation functions."""

    def test_validate_province_exists_success(self, sample_provinces):
        """Test successful province validation."""
        mock_repo = Mock()
        mock_repo.list_all.return_value = sample_provinces

        # Should not raise exception for valid province
        price_service._validate_province_exists(mock_repo, "NATIONAL")

    def test_validate_province_not_found(self, sample_provinces):
        """Test province validation when province doesn't exist."""
        mock_repo = Mock()
        mock_repo.list_all.return_value = sample_provinces

        # Should not raise error - validation is optional and logs warning
        price_service._validate_province_exists(mock_repo, "99")
        # Test passes if no exception is raised

    def test_validate_province_repo_error(self):
        """Test province validation when repository fails."""
        mock_repo = Mock()
        mock_repo.list_all.side_effect = Exception("Database error")

        # Should not raise exception - validation is optional
        price_service._validate_province_exists(mock_repo, "NATIONAL")


class TestPriceServiceQuery:
    """Test the main query_prices function."""

    def test_query_prices_success(self, mock_price_repository, mock_commodity_repository, mock_province_repository):
        """Test successful price query."""
        result = price_service.query_prices(
            price_repo=mock_price_repository,
            commodity_repo=mock_commodity_repository,
            province_repo=mock_province_repository,
            level_harga_id=3,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            commodity_id="01",
            province_id="NATIONAL",
            limit=50,
            offset=0
        )

        assert isinstance(result, PaginatedPriceResult)
        assert len(result.data) == 2
        assert result.total == 2
        assert result.limit == 50
        assert result.offset == 0

        # Verify repository was called with correct parameters
        call_args = mock_price_repository.query.call_args[0][0]
        assert call_args.level_harga_id == 3
        assert call_args.period_start == date(2024, 1, 1)
        assert call_args.period_end == date(2024, 12, 31)
        assert call_args.commodity_id == "01"
        assert call_args.province_id == "NATIONAL"
        assert call_args.limit == 50
        assert call_args.offset == 0

    def test_query_prices_validation_error(self, mock_price_repository):
        """Test query with validation error."""
        with pytest.raises(ValueError, match="level_harga_id must be between 1 and 5"):
            price_service.query_prices(
                price_repo=mock_price_repository,
                level_harga_id=0  # Invalid level_harga_id
            )

    def test_query_prices_repository_error(self, mock_price_repository):
        """Test query when repository fails."""
        mock_price_repository.query.side_effect = Exception("Database connection error")

        with pytest.raises(RuntimeError, match="Failed to query prices: Database connection error"):
            price_service.query_prices(
                price_repo=mock_price_repository,
                level_harga_id=3
            )

    def test_query_prices_without_optional_repos(self, mock_price_repository):
        """Test query without optional commodity/province repositories."""
        result = price_service.query_prices(
            price_repo=mock_price_repository,
            level_harga_id=3
        )

        assert isinstance(result, PaginatedPriceResult)
        # Should work without validation since repos are None
