from __future__ import annotations

import time
from datetime import date
from typing import Mapping

import httpx

from app.usecases.ports import FetchParams, UpstreamClientPort

"""
HTTP upstream client adapter using httpx with exponential backoff.

Follows functional style returning an UpstreamClientPort, closing over config.
"""


DEFAULT_BASE_URL = (
    "https://api-panelhargav2.badanpangan.go.id/api/front/harga-pangan-bulanan-v2"
)


def _default_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "https://panelharga.badanpangan.go.id",
        "Referer": "https://panelharga.badanpangan.go.id/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"'
    }


def _format_period(start: date, end: date) -> str:
    # Upstream expects DD/MM/YYYY - DD/MM/YYYY
    def _fmt(d: date) -> str:
        return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"

    return f"{_fmt(start)} - {_fmt(end)}"


def _build_query(params: FetchParams) -> dict[str, str]:
    q: dict[str, str] = {
        "start_year": str(params.start_year),
        "end_year": str(params.end_year),
        "period_date": _format_period(params.period_start, params.period_end),
        "level_harga_id": str(params.level_harga_id),
        # empty string for national aggregation (as seen in RFC curl)
        "province_id": "" if params.province_id in (None, "NATIONAL") else str(params.province_id),
    }
    return q


def make_mock_upstream_client() -> UpstreamClientPort:
    """Create a mock UpstreamClientPort for development/testing when upstream is unavailable."""

    def test_connection() -> bool:
        return True  # Mock is always "available"

    def fetch(params: FetchParams) -> Mapping:
        print("🎭 Using mock upstream data for development")
        # Return mock response that matches the real API structure
        return {
            "request_data": {
                "start_year": params.start_year,
                "end_year": params.end_year,
                "period_date": _format_period(params.period_start, params.period_end),
                "province_id": params.province_id or "",
                "level_harga_id": params.level_harga_id
            },
            "data": {
                "2024": [
                    {
                        "Komoditas_id": 27,
                        "Komoditas": "Beras Premium",
                        "background": "https://panelharga.badanpangan.go.id/assets/img/komoditas-ikon/beras-premium.png",
                        "Tahun": 2024,
                        "today_province_price": {
                            "satuan": "Rp./Kg",
                            "hargatertinggi": 20000,
                            "provinsitertinggi": "Papua Barat",
                            "provinsiterendah": "D.I Yogyakarta",
                            "hargaterendah": 14500,
                            "hargaratarata": 16067
                        },
                        "Jan": 13228,
                        "Feb": 13487,
                        "Mar": 13612,
                        "Apr": 13702,
                        "Mei": 13668,
                        "Jun": 13656,
                        "Jul": 13663,
                        "Agu": 13830,
                        "Sep": 14554,
                        "Okt": 15008,
                        "Nov": 15045,
                        "Des": 15056
                    },
                    {
                        "Komoditas_id": 28,
                        "Komoditas": "Beras Medium",
                        "background": "https://panelharga.badanpangan.go.id/assets/img/komoditas-ikon/beras-medium.png",
                        "Tahun": 2024,
                        "today_province_price": {
                            "satuan": "Rp./Kg",
                            "hargatertinggi": 18000,
                            "provinsitertinggi": "Papua Barat",
                            "provinsiterendah": "Jawa Timur",
                            "hargaterendah": 12807,
                            "hargaratarata": 13777
                        },
                        "Jan": 11609,
                        "Feb": 11821,
                        "Mar": 11891,
                        "Apr": 11962,
                        "Mei": 11934,
                        "Jun": 11906,
                        "Jul": 11969,
                        "Agu": 12145,
                        "Sep": 12908,
                        "Okt": 13280,
                        "Nov": 13236,
                        "Des": 13254
                    }
                ]
            }
        }

    return UpstreamClientPort(fetch=fetch, test_connection=test_connection)


def make_upstream_client(
    *,
    base_url: str | None = None,
    timeout_seconds: float = 20.0,
    max_attempts: int = 5,
    use_mock: bool = False,
) -> UpstreamClientPort:
    """Create an UpstreamClientPort backed by httpx.

    Args:
        base_url: override API endpoint.
        timeout_seconds: total timeout per attempt.
        max_attempts: retry attempts with backoff 1,2,4,8,16s.
        use_mock: if True, return mock client for development/testing.
    """

    if use_mock:
        return make_mock_upstream_client()

    client = httpx.Client(
        timeout=30.0,  # Total timeout - matches working curl behavior
        headers=_default_headers()
    )
    url = base_url or DEFAULT_BASE_URL

    def test_connection() -> bool:
        """Test basic connectivity to upstream endpoint."""
        try:
            # Use the exact same parameters that work with curl
            test_params = {
                "start_year": "2023",
                "end_year": "2025",
                "period_date": "02/09/2025 - 02/09/2025",
                "province_id": "",
                "level_harga_id": "3"
            }
            resp = client.get(url, params=test_params)
            return resp.status_code < 400
        except Exception as e:
            print(f"Connection test failed with error: {e}")
            return False

    def fetch(params: FetchParams) -> Mapping:
        if params.start_year > params.end_year:
            raise ValueError("start_year must be <= end_year")
        if params.period_start > params.period_end:
            raise ValueError("period_start must be <= period_end")

        # Test connection first
        if not test_connection():
            raise ConnectionError("Upstream endpoint is not accessible. Please check your internet connection or try again later.")

        # Simplified retry logic - API responds reliably in ~7 seconds
        backoffs = [2, 4, 8]  # Reduced retry attempts
        attempts = max(1, min(max_attempts, len(backoffs)))
        last_exc: Exception | None = None

        for i in range(attempts):
            try:
                print(f"🔄 Attempt {i + 1}/{attempts} - Fetching data from upstream...")
                resp = client.get(url, params=_build_query(params))
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, Mapping):
                    raise ValueError("Unexpected upstream response type (expected object)")
                print("✅ Successfully fetched data from upstream")
                return data
            except httpx.TimeoutException as e:
                last_exc = ConnectionError(f"Request timed out after 30s: {e}")
                print(f"⏰ Request timed out (attempt {i + 1}/{attempts})")
            except httpx.ConnectError as e:
                last_exc = ConnectionError(f"Connection failed: {e}")
                print(f"🔌 Connection failed (attempt {i + 1}/{attempts})")
            except httpx.HTTPStatusError as e:
                # Don't retry on HTTP errors (4xx, 5xx)
                raise ConnectionError(f"HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:  # noqa: BLE001
                last_exc = ConnectionError(f"Unexpected error: {e}")
                print(f"❌ Unexpected error (attempt {i + 1}/{attempts}): {e}")

            if i < attempts - 1:
                sleep_time = backoffs[i]
                print(f"⏳ Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

        # If we reach here, all attempts failed
        assert last_exc is not None
        raise last_exc

    return UpstreamClientPort(fetch=fetch, test_connection=test_connection)

