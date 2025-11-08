"""Unit tests for Position model.

Tests the Position model's validation, persistence, query methods,
and automatic Symbol creation.
"""

import pytest

from src.models.account import Account
from src.models.active_model import ActiveModelError
from src.models.position import Position
from src.models.symbol import Symbol

# Import the actual exception type that will be raised
try:
    from pysqlcipher3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3


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


class TestPositionFieldValidation:
    """Test Position field name validation."""

    def test_position_rejects_invalid_fields(self, test_db):
        """Test that Position rejects invalid field names in __init__."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        # Create account and symbol first
        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        with pytest.raises(ValueError, match="Invalid fields"):
            Position(
                database=test_db,
                account_id="U1234567",
                symbol_id=symbol.id,
                quantity=100.0,
                currency="USD",
                snapshot_ts="2025-01-01T00:00:00Z",
                invalid_field="should fail",  # Not in schema
            )

    def test_position_accepts_all_valid_fields(self, test_db):
        """Test that Position accepts all valid fields."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        # Create account and symbol first
        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            market_price=150000000,  # $150.00 in micro-dollars
            market_value=15000000000,  # $15,000.00 in micro-dollars
            avg_cost=145000000,  # $145.00 in micro-dollars
            currency="USD",
            unrealized_pnl=500000000,  # $500.00 in micro-dollars
            realized_pnl=0,
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        assert position.account_id == "U1234567"
        assert position.symbol_id == symbol.id
        assert position.quantity == 100.0
        assert position.market_price == 150000000
        assert position.market_value == 15000000000
        assert position.currency == "USD"
        assert position.snapshot_ts == "2025-01-01T00:00:00Z"
        assert position.created_at is not None
        assert position.updated_at is not None


class TestPositionValidation:
    """Test Position business rule validation."""

    def test_validate_requires_account_id(self, test_db):
        """Test that account_id is required."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="account_id is required"):
            position.validate()

    def test_validate_requires_symbol_id(self, test_db):
        """Test that symbol_id is required."""
        create_accounts_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="symbol_id is required"):
            position.validate()

    def test_validate_requires_quantity(self, test_db):
        """Test that quantity is required."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="quantity is required"):
            position.validate()

    def test_validate_requires_currency(self, test_db):
        """Test that currency is required."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="currency is required"):
            position.validate()

    def test_validate_requires_snapshot_ts(self, test_db):
        """Test that snapshot_ts is required."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
        )

        with pytest.raises(ActiveModelError, match="snapshot_ts is required"):
            position.validate()

    def test_validate_requires_currency_usd(self, test_db):
        """Test that currency must be USD in Phase 1."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="EUR",  # Invalid
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="Currency must be USD"):
            position.validate()

    def test_validate_requires_account_exists(self, test_db):
        """Test that account must exist in database."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="NONEXISTENT",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(
            ActiveModelError, match="Account NONEXISTENT does not exist"
        ):
            position.validate()

    def test_validate_requires_symbol_exists(self, test_db):
        """Test that symbol must exist in database."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=99999,  # Non-existent symbol
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="Symbol 99999 does not exist"):
            position.validate()

    def test_validate_requires_quantity_numeric(self, test_db):
        """Test that quantity must be numeric."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity="not a number",  # Invalid
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        with pytest.raises(ActiveModelError, match="quantity must be numeric"):
            position.validate()

    def test_validate_requires_valid_iso8601_snapshot_ts(self, test_db):
        """Test that snapshot_ts must be valid ISO-8601 format."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="invalid date",  # Invalid
        )

        with pytest.raises(
            ActiveModelError, match="snapshot_ts must be valid ISO-8601"
        ):
            position.validate()

    def test_validate_requires_currency_amounts_integer(self, test_db):
        """Test that currency amounts must be integers (micro-dollars)."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
            market_price=150.25,  # Should be integer, not float
        )

        with pytest.raises(ActiveModelError, match="market_price must be INTEGER"):
            position.validate()


class TestPositionSave:
    """Test Position save operations."""

    def test_save_creates_new_position(self, test_db):
        """Test that save() creates a new position."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        assert not hasattr(position, "id") or position.id is None
        result = position.save()
        assert result is True
        assert position.id is not None

        # Verify it was saved
        loaded = Position.find_by_id(test_db, position.id)
        assert loaded is not None
        assert loaded.account_id == "U1234567"
        assert loaded.symbol_id == symbol.id
        assert loaded.quantity == 100.0

    def test_save_updates_existing_position(self, test_db):
        """Test that save() updates an existing position."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position.save()

        # Update quantity
        position.quantity = 150.0
        position.save()

        # Verify update
        loaded = Position.find_by_id(test_db, position.id)
        assert loaded.quantity == 150.0

    def test_save_enforces_unique_constraint(self, test_db):
        """Test that save() enforces unique constraint.

        Tests the unique constraint on (account_id, symbol_id, snapshot_ts).
        """
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        # Create first position
        position1 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position1.save()

        # Try to create duplicate (same account, symbol, snapshot_ts)
        position2 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=200.0,  # Different quantity
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",  # Same snapshot_ts
        )

        # Should raise error due to unique constraint
        with pytest.raises(sqlite3.IntegrityError):  # SQLite will raise IntegrityError
            position2.save()


class TestPositionQueries:
    """Test Position query methods."""

    def test_find_by_id(self, test_db):
        """Test finding position by ID."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position.save()

        loaded = Position.find_by_id(test_db, position.id)
        assert loaded is not None
        assert loaded.id == position.id
        assert loaded.account_id == "U1234567"

    def test_find_by_account(self, test_db):
        """Test finding positions by account."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account1 = Account(
            database=test_db, id="U1234567", name="Account 1", base_currency="USD"
        )
        account1.save()

        account2 = Account(
            database=test_db, id="U7654321", name="Account 2", base_currency="USD"
        )
        account2.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        # Create positions for account1
        position1 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position1.save()

        position2 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=200.0,
            currency="USD",
            snapshot_ts="2025-01-02T00:00:00Z",
        )
        position2.save()

        # Create position for account2
        position3 = Position(
            database=test_db,
            account_id="U7654321",
            symbol_id=symbol.id,
            quantity=50.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position3.save()

        # Find positions for account1
        positions = Position.find_by_account(test_db, "U1234567")
        assert len(positions) == 2
        assert all(p.account_id == "U1234567" for p in positions)

    def test_find_by_account_and_symbol(self, test_db):
        """Test finding positions by account and symbol."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol1 = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol1.save()

        symbol2 = Symbol(
            database=test_db,
            conid=272093,
            symbol="MSFT",
            sec_type="STK",
            currency="USD",
        )
        symbol2.save()

        # Create positions for symbol1
        position1 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol1.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position1.save()

        position2 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol1.id,
            quantity=150.0,
            currency="USD",
            snapshot_ts="2025-01-02T00:00:00Z",
        )
        position2.save()

        # Create position for symbol2
        position3 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol2.id,
            quantity=50.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position3.save()

        # Find positions for account and symbol1
        positions = Position.find_by_account_and_symbol(test_db, "U1234567", symbol1.id)
        assert len(positions) == 2
        assert all(p.symbol_id == symbol1.id for p in positions)

    def test_find_latest_by_account_and_symbol(self, test_db):
        """Test finding latest position snapshot."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        # Create older position
        position1 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position1.save()

        # Create newer position
        position2 = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=150.0,
            currency="USD",
            snapshot_ts="2025-01-02T00:00:00Z",
        )
        position2.save()

        # Find latest
        latest = Position.find_latest_by_account_and_symbol(
            test_db, "U1234567", symbol.id
        )
        assert latest is not None
        assert latest.id == position2.id
        assert latest.quantity == 150.0
        assert latest.snapshot_ts == "2025-01-02T00:00:00Z"


class TestPositionAutomaticSymbolCreation:
    """Test automatic Symbol creation from API data."""

    def test_create_from_api_data_creates_symbol_if_missing(self, test_db):
        """Test that create_from_api_data creates Symbol if it doesn't exist."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        # Symbol doesn't exist yet
        assert Symbol.find_by_conid(test_db, 265598) is None

        # Create position from API data - should auto-create Symbol
        position = Position.create_from_api_data(
            database=test_db,
            account_id="U1234567",
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            quantity=100.0,
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        # Verify Symbol was created
        symbol = Symbol.find_by_conid(test_db, 265598)
        assert symbol is not None
        assert symbol.symbol == "AAPL"
        assert symbol.sec_type == "STK"
        assert symbol.currency == "USD"

        # Verify Position was created
        assert position is not None
        assert position.account_id == "U1234567"
        assert position.symbol_id == symbol.id
        assert position.quantity == 100.0

    def test_create_from_api_data_uses_existing_symbol(self, test_db):
        """Test that create_from_api_data uses existing Symbol if it exists."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        # Create Symbol first
        existing_symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
            name="Apple Inc.",
        )
        existing_symbol.save()
        symbol_id = existing_symbol.id

        # Create position from API data - should use existing Symbol
        position = Position.create_from_api_data(
            database=test_db,
            account_id="U1234567",
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            quantity=100.0,
            snapshot_ts="2025-01-01T00:00:00Z",
        )

        # Verify it used the existing Symbol
        assert position.symbol_id == symbol_id

        # Verify only one Symbol exists
        symbols = Symbol.where(test_db, conid=265598)
        assert len(symbols) == 1

    def test_create_from_api_data_with_options_symbol(self, test_db):
        """Test automatic Symbol creation for options positions."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        # Create underlying stock Symbol first
        underlying = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        underlying.save()

        # Create position from API data for option - should auto-create option Symbol
        position = Position.create_from_api_data(
            database=test_db,
            account_id="U1234567",
            conid=5000000,  # Option conid
            symbol="AAPL",
            sec_type="OPT",
            quantity=10.0,  # 10 contracts
            snapshot_ts="2025-01-01T00:00:00Z",
            expiry="2025-03-21",
            strike=150.0,
            right="C",
            underlying_conid=265598,
        )

        # Verify option Symbol was created
        option_symbol = Symbol.find_by_conid(test_db, 5000000)
        assert option_symbol is not None
        assert option_symbol.sec_type == "OPT"
        assert option_symbol.expiry == "2025-03-21"
        assert option_symbol.strike == 150.0
        assert option_symbol.right == "C"
        assert option_symbol.underlying_conid == 265598

        # Verify Position was created
        assert position.symbol_id == option_symbol.id
        assert position.quantity == 10.0

    def test_create_from_api_data_with_optional_symbol_fields(self, test_db):
        """Test automatic Symbol creation with optional fields."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        # Create position with all optional Symbol fields
        position = Position.create_from_api_data(
            database=test_db,
            account_id="U1234567",
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            quantity=100.0,
            snapshot_ts="2025-01-01T00:00:00Z",
            symbol_name="Apple Inc.",
            exchange="NASDAQ",
            primary_exchange="NASDAQ",
            local_symbol="AAPL",
        )

        # Verify Symbol was created with all fields
        symbol = Symbol.find_by_conid(test_db, 265598)
        assert symbol is not None
        assert symbol.name == "Apple Inc."
        assert symbol.exchange == "NASDAQ"
        assert symbol.primary_exchange == "NASDAQ"
        assert symbol.local_symbol == "AAPL"

        # Verify Position was created
        assert position is not None
        assert position.symbol_id == symbol.id

    def test_create_from_api_data_with_currency_amounts(self, test_db):
        """Test create_from_api_data with currency amounts in micro-dollars."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        position = Position.create_from_api_data(
            database=test_db,
            account_id="U1234567",
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            quantity=100.0,
            snapshot_ts="2025-01-01T00:00:00Z",
            market_price=150000000,  # $150.00 in micro-dollars
            market_value=15000000000,  # $15,000.00 in micro-dollars
            avg_cost=145000000,  # $145.00 in micro-dollars
            unrealized_pnl=500000000,  # $500.00 in micro-dollars
            realized_pnl=0,
        )

        assert position.market_price == 150000000
        assert position.market_value == 15000000000
        assert position.avg_cost == 145000000
        assert position.unrealized_pnl == 500000000
        assert position.realized_pnl == 0

    def test_create_from_api_data_raises_if_account_not_found(self, test_db):
        """Test that create_from_api_data raises if account doesn't exist."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        with pytest.raises(ValueError, match="Account NONEXISTENT does not exist"):
            Position.create_from_api_data(
                database=test_db,
                account_id="NONEXISTENT",
                conid=265598,
                symbol="AAPL",
                sec_type="STK",
                quantity=100.0,
                snapshot_ts="2025-01-01T00:00:00Z",
            )


class TestPositionDelete:
    """Test Position delete operations."""

    def test_delete_removes_position(self, test_db):
        """Test that delete() removes position from database."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position.save()

        position_id = position.id

        # Delete position
        result = position.delete()
        assert result is True

        # Verify it's gone
        loaded = Position.find_by_id(test_db, position_id)
        assert loaded is None

    def test_delete_raises_if_no_id(self, test_db):
        """Test that delete() raises if position has no ID."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        # Not saved, so no ID

        with pytest.raises(ValueError, match="Cannot delete"):
            position.delete()


class TestPositionRepr:
    """Test Position string representation."""

    def test_repr_with_id(self, test_db):
        """Test __repr__ with ID."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)
        create_positions_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        position.save()

        repr_str = repr(position)
        assert "Position" in repr_str
        assert str(position.id) in repr_str
        assert "U1234567" in repr_str
        assert str(symbol.id) in repr_str
        assert "100.0" in repr_str

    def test_repr_without_id(self, test_db):
        """Test __repr__ without ID (unsaved)."""
        create_accounts_table(test_db)
        create_symbols_table(test_db)

        account = Account(
            database=test_db, id="U1234567", name="Test Account", base_currency="USD"
        )
        account.save()

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        position = Position(
            database=test_db,
            account_id="U1234567",
            symbol_id=symbol.id,
            quantity=100.0,
            currency="USD",
            snapshot_ts="2025-01-01T00:00:00Z",
        )
        # Not saved

        repr_str = repr(position)
        assert "Position" in repr_str
        assert "U1234567" in repr_str
        assert str(symbol.id) in repr_str
        assert "100.0" in repr_str
