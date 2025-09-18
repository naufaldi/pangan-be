"""
Performance tests for the /prices API endpoint.
Tests response times and performance characteristics with the running server.
"""

import pytest
import requests
import time


@pytest.fixture
def api_base_url():
    """Base URL for the API under test."""
    return "http://127.0.0.1:8000"


@pytest.fixture
def api_client(api_base_url):
    """HTTP client for making API requests."""
    return requests.Session()


# Skip performance tests if server is not available
@pytest.fixture(autouse=True)
def skip_if_server_unavailable(api_base_url):
    """Skip tests if the server is not running."""
    try:
        response = requests.get(f"{api_base_url}/health/healthz", timeout=2)
        if response.status_code != 200:
            pytest.skip("Test server is not available or not healthy")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip("Test server is not running")


class TestPricesAPIPerformance:
    """Performance tests for the /prices endpoint."""

    def test_response_time_basic_query(self, api_client, api_base_url):
        """Test response time for basic query."""
        start_time = time.time()

        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)
        assert isinstance(data["data"], list)

        # Performance assertion: should be under 150ms target
        assert response_time < 0.150, f"Response time {response_time:.3f}s exceeded 150ms target"
        print(".3f")

    def test_response_time_with_filtering(self, api_client, api_base_url):
        """Test response time with commodity filtering."""
        start_time = time.time()

        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&commodity_id=01")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)

        # Should be reasonably fast
        assert response_time < 0.100, f"Filtered query response time {response_time:.3f}s exceeded 100ms target"
        print(".3f")

    def test_response_time_with_pagination(self, api_client, api_base_url):
        """Test response time with pagination parameters."""
        start_time = time.time()

        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=10&offset=0")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)
        assert len(data["data"]) <= 10
        assert data["limit"] == 10
        assert data["offset"] == 0

        # Pagination should not significantly impact performance
        assert response_time < 0.100, f"Paginated query response time {response_time:.3f}s exceeded 100ms target"
        print(".3f")

    def test_response_time_with_date_filter(self, api_client, api_base_url):
        """Test response time with date range filtering."""
        start_time = time.time()

        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&period_start=2024-01-01&period_end=2024-12-31")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total"], int)

        # Date filtering should be reasonably fast
        assert response_time < 0.100, f"Date filtered query response time {response_time:.3f}s exceeded 100ms target"
        print(".3f")

    def test_concurrent_requests_simulation(self, api_client, api_base_url):
        """Simulate multiple concurrent requests."""
        import threading
        import queue

        results = queue.Queue()
        response_times = []

        def make_request(request_id):
            start_time = time.time()
            response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=5")
            end_time = time.time()

            response_time = end_time - start_time
            results.put((request_id, response.status_code, response_time))

        # Simulate 3 concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        while not results.empty():
            request_id, status_code, response_time = results.get()
            assert status_code == 200, f"Request {request_id} failed with status {status_code}"
            response_times.append(response_time)

        # All requests should be reasonably fast
        max_response_time = max(response_times)
        avg_response_time = sum(response_times) / len(response_times)

        assert max_response_time < 0.150, ".3f"
        assert avg_response_time < 0.100, ".3f"

        print(".3f")
        print(".3f")

    def test_database_query_efficiency(self, api_client, api_base_url):
        """Test that database queries are efficient."""
        start_time = time.time()
        response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit=1")
        end_time = time.time()

        assert response.status_code == 200

        # Single record query should be very fast
        response_time = end_time - start_time
        assert response_time < 0.050, ".3f"
        print(".3f")


def measure_response_time(client, url, description):
    """Helper function to measure response time for a given request."""
    start_time = time.time()
    response = client.get(url)
    end_time = time.time()

    response_time = end_time - start_time
    print(".3f")

    return response, response_time


class TestPerformanceBenchmarks:
    """Benchmark tests to establish performance baselines."""

    def test_query_complexity_impact(self, api_client, api_base_url):
        """Test how query complexity affects performance."""
        test_cases = [
            (f"{api_base_url}/prices?level_harga_id=3", "Basic query"),
            (f"{api_base_url}/prices?level_harga_id=3&commodity_id=01", "Single commodity filter"),
            (f"{api_base_url}/prices?level_harga_id=3&period_start=2024-01-01", "Date range filter"),
            (f"{api_base_url}/prices?level_harga_id=3&commodity_id=01&period_start=2024-01-01&limit=25&offset=0", "Complex query"),
        ]

        for url, description in test_cases:
            response, response_time = measure_response_time(api_client, url, description)
            assert response.status_code == 200
            assert response_time < 0.150, ".3f"

    def test_pagination_performance_scaling(self, api_client, api_base_url):
        """Test how pagination affects performance with different page sizes."""
        page_sizes = [5, 10, 25, 50]

        for page_size in page_sizes:
            start_time = time.time()
            response = api_client.get(f"{api_base_url}/prices?level_harga_id=3&limit={page_size}")
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) <= page_size

            # Performance should scale reasonably with page size
            expected_max_time = 0.050 + (page_size * 0.001)  # Base time + per-record overhead
            assert response_time < expected_max_time, ".3f"

            print(".3f")
