"""Unit tests for API client."""

import pytest
import requests
import requests_mock

from src.api_client import (
    APIError,
    AuthenticationError,
    ClientError,
    IBKRAPIClient,
    NetworkError,
)


class TestIBKRAPIClient:
    """Test IBKR API client functionality."""

    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = IBKRAPIClient()
        assert client.base_url == "https://localhost:5001/v1/api"
        assert client.timeout == 30
        assert client.session.verify is False
        assert client.csrf_token is None

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = IBKRAPIClient(
            base_url="https://example.com/api",
            verify_ssl=True,
            timeout=60,
        )
        assert client.base_url == "https://example.com/api"
        assert client.timeout == 60
        assert client.session.verify is True

    def test_tickle_success(self):
        """Test successful tickle call."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                json={"status": "ok"},
                status_code=200,
            )
            result = client.tickle()
            assert result == {"status": "ok"}

    def test_tickle_401_raises_authentication_error(self):
        """Test tickle with 401 raises AuthenticationError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=401,
            )
            with pytest.raises(AuthenticationError, match="Session expired"):
                client.tickle()

    def test_tickle_403_raises_authentication_error(self):
        """Test tickle with 403 raises AuthenticationError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=403,
            )
            with pytest.raises(AuthenticationError, match="Insufficient permissions"):
                client.tickle()

    def test_tickle_404_raises_client_error(self):
        """Test tickle with 404 raises ClientError (non-retryable)."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=404,
            )
            with pytest.raises(ClientError, match="Endpoint not found"):
                client.tickle()

    def test_tickle_500_raises_api_error_retryable(self):
        """Test tickle with 500 raises retryable APIError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=500,
            )
            # Should raise APIError (retryable)
            with pytest.raises(APIError, match="Server error"):
                client.tickle()

    def test_tickle_connection_error_raises_network_error(self):
        """Test tickle with connection error raises NetworkError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                exc=requests.exceptions.ConnectionError("Connection refused"),
            )
            with pytest.raises(NetworkError, match="Gateway not reachable"):
                client.tickle()

    def test_tickle_timeout_raises_network_error(self):
        """Test tickle with timeout raises NetworkError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                exc=requests.exceptions.Timeout("Request timeout"),
            )
            with pytest.raises(NetworkError, match="Request timeout"):
                client.tickle()

    def test_tickle_invalid_json_raises_client_error(self):
        """Test tickle with invalid JSON raises ClientError (non-retryable)."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                text="not json",
                status_code=200,
            )
            with pytest.raises(ClientError, match="Invalid JSON response"):
                client.tickle()

    def test_csrf_token_extraction(self):
        """Test CSRF token extraction from response headers."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                json={"status": "ok"},
                status_code=200,
                headers={"X-CSRF-TOKEN": "test-token-123"},
            )
            client.tickle()
            assert client.csrf_token == "test-token-123"

    def test_csrf_token_in_subsequent_requests(self):
        """Test CSRF token is included in subsequent requests."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            # First request sets CSRF token
            m.get(
                "https://localhost:5001/v1/api/tickle",
                json={"status": "ok"},
                status_code=200,
                headers={"X-CSRF-TOKEN": "test-token-123"},
            )
            client.tickle()

            # Second request should include CSRF token
            m.get(
                "https://localhost:5001/v1/api/portfolio/accounts",
                json=[],
                status_code=200,
            )
            client.get_accounts()

            # Verify CSRF token was sent
            last_request = m.request_history[-1]
            assert last_request.headers.get("X-CSRF-TOKEN") == "test-token-123"

    def test_get_accounts_success(self):
        """Test successful get_accounts call."""
        client = IBKRAPIClient()
        expected_response = [
            {"accountId": "U1234567", "accountTitle": "Individual", "currency": "USD"}
        ]
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/portfolio/accounts",
                json=expected_response,
                status_code=200,
            )
            result = client.get_accounts()
            assert result == expected_response

    def test_get_positions_success(self):
        """Test successful get_positions call."""
        client = IBKRAPIClient()
        expected_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "marketPrice": 150.25,
                "currency": "USD",
            }
        ]
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/portfolio/U1234567/positions",
                json=expected_response,
                status_code=200,
            )
            result = client.get_positions("U1234567")
            assert result == expected_response

    def test_get_positions_404_raises_client_error(self):
        """Test get_positions with 404 raises ClientError (non-retryable)."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/portfolio/INVALID/positions",
                status_code=404,
            )
            with pytest.raises(ClientError, match="Endpoint not found"):
                client.get_positions("INVALID")

    def test_retry_on_500_error(self):
        """Test that 500 errors are retried."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            # First two attempts fail with 500, third succeeds
            m.get(
                "https://localhost:5001/v1/api/tickle",
                [
                    {"status_code": 500},
                    {"status_code": 500},
                    {"json": {"status": "ok"}, "status_code": 200},
                ],
            )
            # Should eventually succeed after retries
            result = client.tickle()
            assert result == {"status": "ok"}
            assert len(m.request_history) == 3

    def test_no_retry_on_401_error(self):
        """Test that 401 errors are not retried."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=401,
            )
            with pytest.raises(AuthenticationError):
                client.tickle()
            # Should only make one request (no retry)
            assert len(m.request_history) == 1

    def test_429_rate_limiting_raises_api_error_retryable(self):
        """Test that 429 rate limiting raises retryable APIError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            # First attempt gets 429, second succeeds
            m.get(
                "https://localhost:5001/v1/api/tickle",
                [
                    {"status_code": 429},
                    {"json": {"status": "ok"}, "status_code": 200},
                ],
            )
            # Should eventually succeed after retry
            result = client.tickle()
            assert result == {"status": "ok"}
            assert len(m.request_history) == 2

    def test_429_rate_limiting_retries_with_backoff(self):
        """Test that 429 errors are retried with exponential backoff."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            # First two attempts get 429, third succeeds
            m.get(
                "https://localhost:5001/v1/api/tickle",
                [
                    {"status_code": 429},
                    {"status_code": 429},
                    {"json": {"status": "ok"}, "status_code": 200},
                ],
            )
            result = client.tickle()
            assert result == {"status": "ok"}
            assert len(m.request_history) == 3

    def test_ssl_error_raises_network_error(self):
        """Test that SSLError raises NetworkError."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                exc=requests.exceptions.SSLError("SSL certificate verification failed"),
            )
            with pytest.raises(NetworkError, match="SSL error"):
                client.tickle()

    def test_retry_exhaustion_after_5_attempts(self):
        """Test that retries stop after 5 attempts."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            # All 5 attempts fail with 500
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=500,
            )
            with pytest.raises(APIError, match="Server error"):
                client.tickle()
            # Should have made exactly 5 attempts
            assert len(m.request_history) == 5

    def test_other_4xx_errors_raise_client_error_no_retry(self):
        """Test that other 4xx errors (400, 402, etc.) raise ClientError without retry."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=400,
                text="Bad Request: Invalid parameters",
            )
            with pytest.raises(ClientError, match="Client error 400"):
                client.tickle()
            # Should only make one request (no retry for ClientError)
            assert len(m.request_history) == 1

    def test_402_payment_required_no_retry(self):
        """Test that 402 Payment Required raises ClientError and doesn't retry."""
        client = IBKRAPIClient()
        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5001/v1/api/tickle",
                status_code=402,
                text="Payment Required",
            )
            with pytest.raises(ClientError, match="Client error 402"):
                client.tickle()
            assert len(m.request_history) == 1
