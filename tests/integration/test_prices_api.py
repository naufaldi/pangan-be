"""
Integration tests for the /prices API endpoint.
Tests the full HTTP request/response cycle with the running server.
These tests assume the server is running with populated test data.
"""

import pytest
import requests
from datetime import date


@pytest.fixture
def api_base_url():
    """Base URL for the API under test."""
    # This assumes the server is running on the default port
    # In a real CI/CD environment, this would be configurable
    return "http://127.0.0.1:8000"


@pytest.fixture
def api_client(api_base_url):
    """HTTP client for making API requests."""
    return requests.Session()


# Skip integration tests if server is not available
@pytest.fixture(autouse=True)
def skip_if_server_unavailable(api_base_url):
    """Skip tests if the server is not running."""
    try:
        response = requests.get(f"{api_base_url}/health/healthz", timeout=2)
        if response.status_code != 200:
            pytest.skip("Test server is not available or not healthy")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip("Test server is not running")


class TestPricesAPI:
    """Integration tests for the /prices endpoint."""

    def test_get_prices_basic(self, api_client, api_base_url):
        """Test basic price query with required parameter."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Check first record structure
        record = data["data"][0]
        assert "id" in record
        assert "commodity_id" in record
        assert "commodity_name" in record
        assert "province_id" in record
        assert "province_name" in record
        assert "level_harga_id" in record
        assert "period_start" in record
        assert "period_end" in record
        assert "price" in record
        assert "unit" in record

    def test_get_prices_with_commodity_filter(self, api_client, api_base_url):
        """Test price query with commodity filter."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&commodity_id=01")

        assert response.status_code == 200
        data = response.json()

        # Filter should work (may return 0 or more results depending on data)
        assert isinstance(data["total"], int)
        assert isinstance(data["data"], list)
        if data["total"] > 0:
            # If we have results, they should match the filter
            for record in data["data"]:
                assert record["commodity_id"] == "01"

    def test_get_prices_with_pagination(self, api_client, api_base_url):
        """Test price query with pagination."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)
        assert isinstance(data["data"], list)
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["data"]) <= 2  # Should not exceed limit

    def test_get_prices_with_date_filter(self, api_client, api_base_url):
        """Test price query with date range filter."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&period_start=2024-01-01&period_end=2024-12-31")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)
        assert isinstance(data["data"], list)
        # Date filtering should work (may return 0 or more results)

    def test_get_prices_sorted_by_period_desc(self, api_client, api_base_url):
        """Test that results are sorted by period_start descending."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=10")

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 1:
            # Check that dates are in descending order
            dates = [record["period_start"] for record in data["data"]]
            assert dates == sorted(dates, reverse=True)


class TestPricesAPIErrorHandling:
    """Test error handling in the /prices endpoint."""

    def test_missing_required_parameter(self, api_client, api_base_url):
        """Test request without required level_harga_id."""
        response = api_client.get(f"{api_base_url}/prices")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_level_harga_id_too_low(self, api_client, api_base_url):
        """Test request with level_harga_id below minimum."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=0")

        assert response.status_code == 422

    def test_invalid_level_harga_id_too_high(self, api_client, api_base_url):
        """Test request with level_harga_id above maximum."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=6")

        assert response.status_code == 422

    def test_invalid_date_range(self, api_client, api_base_url):
        """Test request with invalid date range (end before start)."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&period_end=2024-01-01&period_start=2024-12-31")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_invalid_limit_too_high(self, api_client, api_base_url):
        """Test request with limit above maximum."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=2000")

        assert response.status_code == 422

    def test_invalid_limit_too_low(self, api_client, api_base_url):
        """Test request with limit below minimum."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=0")

        assert response.status_code == 422

    def test_invalid_offset_negative(self, api_client, api_base_url):
        """Test request with negative offset."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&offset=-1")

        assert response.status_code == 422


class TestPricesAPIPaginationEdgeCases:
    """Test pagination edge cases."""

    def test_pagination_offset_beyond_total(self, api_client, api_base_url):
        """Test pagination when offset exceeds total records."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&offset=1000")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)
        assert len(data["data"]) == 0  # No records returned
        assert data["offset"] == 1000

    def test_pagination_large_limit(self, api_client, api_base_url):
        """Test pagination with large limit."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=1000")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)
        assert len(data["data"]) <= data["total"]
        assert data["limit"] == 1000

    def test_pagination_minimum_limit(self, api_client, api_base_url):
        """Test pagination with minimum limit."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)
        assert len(data["data"]) <= 1  # Should not exceed limit
        assert data["limit"] == 1


class TestPricesAPIFilteringCombinations:
    """Test various filtering combinations."""

    def test_filter_by_commodity_and_date(self, api_client, api_base_url):
        """Test filtering by both commodity and date range."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&commodity_id=01&period_start=2024-01-01&period_end=2024-12-31")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)
        if data["total"] > 0:
            for record in data["data"]:
                assert record["commodity_id"] == "01"
                # Date filtering should work

    def test_filter_by_date_range_only(self, api_client, api_base_url):
        """Test filtering by date range only."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&period_start=2024-01-01&period_end=2024-12-31")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)
        # Date filtering should work

    def test_filter_nonexistent_commodity(self, api_client, api_base_url):
        """Test filtering by non-existent commodity."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&commodity_id=999")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["data"]) == 0

    def test_empty_result_set(self, api_client, api_base_url):
        """Test query that returns no results."""
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&period_start=2025-01-01&period_end=2025-12-31")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["data"]) == 0
