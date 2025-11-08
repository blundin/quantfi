"""Unit tests for sync functionality."""

import pytest
import requests
import requests_mock

from src.api_client import APIError, AuthenticationError, IBKRAPIClient, NetworkError
from src.models.account import Account
from src.models.position import Position
from src.models.symbol import Symbol
from src.sync import sync_positions
from tests.fixtures.sample_responses import (
    sample_positions_response,
    sample_positions_response_empty,
)


def create_accounts_table(test_db):
    """Helper to create accounts table schema for tests."""
    with test_db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_currency TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (base_currency = 'USD')
            )
        """
        )
        # Note: With autocommit mode, commit() is a no-op, but tables are created immediately


def create_symbols_table(test_db):
    """Helper to create symbols table schema for tests."""
    with test_db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conid INTEGER UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                sec_type TEXT NOT NULL,
                currency TEXT NOT NULL,
                exchange TEXT,
                name TEXT,
                multiplier REAL,
                expiry TEXT,
                strike REAL,
                right TEXT,
                underlying_conid INTEGER,
                local_symbol TEXT,
                primary_exchange TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (currency = 'USD')
            )
        """
        )
        # Note: With autocommit mode, commit() is a no-op, but tables are created immediately


def create_positions_table(test_db):
    """Helper to create positions table schema for tests."""
    with test_db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                symbol_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                market_price INTEGER,
                market_value INTEGER,
                avg_cost INTEGER,
                currency TEXT NOT NULL,
                unrealized_pnl INTEGER,
                realized_pnl INTEGER,
                snapshot_ts TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (currency = 'USD'),
                UNIQUE (account_id, symbol_id, snapshot_ts),
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY (symbol_id) REFERENCES symbols(id) ON DELETE RESTRICT
            )
        """
        )
        # Note: With autocommit mode, commit() is a no-op, but tables are created immediately


class TestSyncPositions:
    """Test position sync functionality."""

    def test_sync_positions_success(self, test_db):
        """Test successful position sync."""
        # Create tables
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account first
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.save()

        # Mock API client
        api_client = IBKRAPIClient()
        api_response = sample_positions_response()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                json=api_response,
                status_code=200,
            )

            result = sync_positions(test_db, "U1234567", api_client)

            assert result["status"] == "success"
            assert result["positions_fetched"] == 2
            assert result["positions_saved"] == 2
            assert len(result["errors"]) == 0
            assert "snapshot_ts" in result

        # Verify positions were saved
        positions = Position.find_by_account(test_db, "U1234567")
        assert len(positions) == 2

    def test_sync_positions_empty_response(self, test_db):
        """Test sync with empty positions response."""
        # Create tables
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account first
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.save()

        # Mock API client
        api_client = IBKRAPIClient()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                json=sample_positions_response_empty(),
                status_code=200,
            )

            result = sync_positions(test_db, "U1234567", api_client)

            assert result["status"] == "success"
            assert result["positions_fetched"] == 0
            assert result["positions_saved"] == 0

    def test_sync_positions_creates_symbols_automatically(self, test_db):
        """Test that sync automatically creates Symbol records."""
        # Create tables
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account first
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.save()

        # Mock API client
        api_client = IBKRAPIClient()
        api_response = [
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
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                json=api_response,
                status_code=200,
            )

            result = sync_positions(test_db, "U1234567", api_client)

            assert result["status"] == "success"
            assert result["positions_saved"] == 1

        # Verify Symbol was created

        symbol = Symbol.find_by_conid(test_db, 265598)
        assert symbol is not None
        assert symbol.symbol == "AAPL"
        assert symbol.sec_type == "STK"

    def test_sync_positions_partial_failure(self, test_db):
        """Test sync with partial failures."""
        # Create tables
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account first
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.save()

        # Mock API client with one valid and one invalid position
        api_client = IBKRAPIClient()
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
            },
            {
                # Missing required fields - will cause validation error
                "conid": 272093,
                "symbol": "MSFT",
                # Missing secType - will default to "" which fails validation
                "currency": "USD",
            },
        ]

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                json=api_response,
                status_code=200,
            )

            result = sync_positions(test_db, "U1234567", api_client)

            assert result["status"] == "partial"
            assert result["positions_fetched"] == 2
            assert result["positions_saved"] == 1
            assert len(result["errors"]) == 1

    def test_sync_positions_authentication_error(self, test_db):
        """Test sync raises AuthenticationError on 401."""
        api_client = IBKRAPIClient()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                status_code=401,
            )

            with pytest.raises(AuthenticationError):
                sync_positions(test_db, "U1234567", api_client)

    def test_sync_positions_network_error(self, test_db):
        """Test sync raises NetworkError on connection failure."""
        api_client = IBKRAPIClient()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                exc=requests.exceptions.ConnectionError("Connection refused"),
            )

            with pytest.raises(NetworkError):
                sync_positions(test_db, "U1234567", api_client)

    def test_sync_positions_api_error(self, test_db):
        """Test sync raises APIError on API errors."""
        api_client = IBKRAPIClient()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                status_code=500,
            )

            with pytest.raises(APIError):
                sync_positions(test_db, "U1234567", api_client)

    def test_sync_positions_creates_client_if_not_provided(self, test_db):
        """Test sync creates API client if not provided."""
        # Create tables
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account first
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.save()

        api_response = sample_positions_response()

        with requests_mock.Mocker() as m:
            m.get(
                "https://localhost:5000/v1/api/portfolio/U1234567/positions",
                json=api_response,
                status_code=200,
            )

            # Don't provide api_client
            result = sync_positions(test_db, "U1234567", api_client=None)

            assert result["status"] == "success"
            assert result["positions_saved"] == 2
