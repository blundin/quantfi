"""IBKR Client Portal Web API client.

Handles authentication, session management, and API requests
via the local gateway (https://localhost:5000).
"""

import logging
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication/session errors occur."""

    pass


class NetworkError(Exception):
    """Raised when network/connectivity errors occur."""

    pass


class APIError(Exception):
    """Raised when API returns an error response."""

    pass


class IBKRAPIClient:
    """Client for IBKR Client Portal Web API via local gateway.

    Handles session management, retry logic, and error handling.
    All requests go through the local gateway at https://localhost:5000.
    """

    def __init__(
        self,
        base_url: str = "https://localhost:5000/v1/api",
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        """Initialize API client.

        Args:
            base_url: Base URL for API (default: https://localhost:5000/v1/api)
            verify_ssl: Whether to verify SSL certificates
                (default: False for self-signed)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create session with cookie persistence
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # Track CSRF token if provided by gateway
        self.csrf_token: str | None = None

    def tickle(self) -> dict[str, Any]:
        """Keep session alive and verify gateway is running.

        Returns:
            Response JSON (typically {"status": "ok"})

        Raises:
            AuthenticationError: If session expired (401/403)
            NetworkError: If gateway not reachable
            APIError: For other API errors
        """
        return self._get("/tickle")

    def get_accounts(self) -> list[dict[str, Any]]:
        """Get list of accessible accounts.

        Returns:
            List of account dictionaries with accountId, accountTitle, currency

        Raises:
            AuthenticationError: If session expired (401/403)
            NetworkError: If gateway not reachable
            APIError: For other API errors
        """
        return self._get("/portfolio/accounts")

    def get_positions(self, account_id: str) -> list[dict[str, Any]]:
        """Get current positions snapshot for an account.

        Args:
            account_id: IB account ID (e.g., "U1234567")

        Returns:
            List of position dictionaries with conid, symbol, position, etc.

        Raises:
            AuthenticationError: If session expired (401/403)
            NetworkError: If gateway not reachable
            APIError: For other API errors
        """
        endpoint = f"/portfolio/{account_id}/positions"
        return self._get(endpoint)

    @retry(
        retry=retry_if_exception_type((NetworkError, APIError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        reraise=True,
    )
    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make GET request with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/tickle")
            params: Optional query parameters

        Returns:
            Response JSON data

        Raises:
            AuthenticationError: If session expired (401/403)
            NetworkError: If gateway not reachable
            APIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = {}
        if self.csrf_token:
            headers["X-CSRF-TOKEN"] = self.csrf_token

        try:
            response = self.session.get(
                url, params=params, headers=headers, timeout=self.timeout
            )

            # Extract CSRF token from response headers if present
            if "X-CSRF-TOKEN" in response.headers:
                self.csrf_token = response.headers["X-CSRF-TOKEN"]

            # Handle HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Session expired. Please re-authenticate at "
                    "https://localhost:5000/ in your browser, then retry."
                )
            elif response.status_code == 403:
                raise AuthenticationError(
                    "Insufficient permissions. Please re-authenticate at "
                    "https://localhost:5000/ in your browser, then retry."
                )
            elif response.status_code == 404:
                raise APIError(
                    f"Endpoint not found: {endpoint}. "
                    "Check account ID or endpoint path."
                )
            elif response.status_code == 429:
                # Rate limiting - retry with backoff
                raise APIError(
                    f"Rate limit exceeded for {endpoint}. " "Retrying with backoff..."
                )
            elif response.status_code >= 500:
                # Server errors - retry with backoff
                raise APIError(
                    f"Server error {response.status_code} for {endpoint}. "
                    "Retrying with backoff..."
                )
            elif response.status_code >= 400:
                # Other client errors - don't retry
                raise APIError(
                    f"Client error {response.status_code} for {endpoint}: "
                    f"{response.text[:200]}"
                )

            # Success - return JSON
            try:
                return response.json()
            except ValueError as e:
                raise APIError(f"Invalid JSON response from {endpoint}: {str(e)}")

        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                f"Gateway not reachable at {self.base_url}. "
                "Ensure gateway is running: ./bin/run.sh root/conf.yaml"
            ) from e
        except requests.exceptions.Timeout as e:
            raise NetworkError(
                f"Request timeout for {endpoint} after {self.timeout}s"
            ) from e
        except requests.exceptions.SSLError as e:
            raise NetworkError(
                f"SSL error for {endpoint}. "
                "If using self-signed cert, set verify_ssl=False"
            ) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error for {endpoint}: {str(e)}") from e
