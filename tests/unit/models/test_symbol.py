"""Unit tests for Symbol model.

Tests the Symbol model's validation, persistence, and query methods.
"""

import pytest

from src.models.symbol import Symbol
from src.models.active_model import ActiveModelError


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
                updated_at TEXT NOT NULL
            )
        """
        )


class TestSymbolFieldValidation:
    """Test Symbol field name validation."""

    def test_symbol_rejects_invalid_fields(self, test_db):
        """Test that Symbol rejects invalid field names in __init__."""
        with pytest.raises(ValueError, match="Invalid fields"):
            Symbol(
                database=test_db,
                conid=265598,
                symbol="AAPL",
                sec_type="STK",
                currency="USD",
                invalid_field="should fail",  # Not in schema
            )

    def test_symbol_accepts_all_valid_fields(self, test_db):
        """Test that Symbol accepts all valid fields."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
            exchange="NASDAQ",
            name="Apple Inc.",
            primary_exchange="NASDAQ",
        )
        assert symbol.conid == 265598
        assert symbol.symbol == "AAPL"
        assert symbol.sec_type == "STK"
        assert symbol.currency == "USD"
        assert symbol.exchange == "NASDAQ"
        assert symbol.name == "Apple Inc."
        assert symbol.created_at is not None
        assert symbol.updated_at is not None


class TestSymbolValidation:
    """Test Symbol business rule validation."""

    def test_validate_requires_conid(self, test_db):
        """Test that conid is required."""
        symbol = Symbol(
            database=test_db,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        with pytest.raises(ActiveModelError, match="conid is required"):
            symbol.validate()

    def test_validate_requires_symbol(self, test_db):
        """Test that symbol ticker is required."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            sec_type="STK",
            currency="USD",
        )
        with pytest.raises(ActiveModelError, match="symbol is required"):
            symbol.validate()

    def test_validate_requires_sec_type(self, test_db):
        """Test that sec_type is required."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            currency="USD",
        )
        with pytest.raises(ActiveModelError, match="sec_type is required"):
            symbol.validate()

    def test_validate_requires_currency(self, test_db):
        """Test that currency is required."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
        )
        with pytest.raises(ActiveModelError, match="currency is required"):
            symbol.validate()

    def test_validate_currency_must_be_usd(self, test_db):
        """Test that currency must be USD in Phase 1."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="EUR",
        )
        with pytest.raises(ActiveModelError, match="Currency must be USD"):
            symbol.validate()

    def test_validate_sec_type_must_be_valid(self, test_db):
        """Test that sec_type must be one of valid types."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="INVALID",
            currency="USD",
        )
        with pytest.raises(ActiveModelError, match="sec_type must be one of"):
            symbol.validate()

    def test_validate_accepts_valid_sec_types(self, test_db):
        """Test that all valid security types are accepted."""
        valid_types = ["STK", "OPT", "FUT", "CASH", "BOND", "CFD", "FOP", "WAR", "IOPT"]
        for sec_type in valid_types:
            symbol = Symbol(
                database=test_db,
                conid=265598,
                symbol="TEST",
                sec_type=sec_type,
                currency="USD",
            )
            # Should not raise
            symbol.validate()

    def test_validate_option_right_must_be_c_or_p(self, test_db):
        """Test that option right must be 'C' or 'P'."""
        symbol = Symbol(
            database=test_db,
            conid=123456,
            symbol="AAPL",
            sec_type="OPT",
            currency="USD",
            right="X",  # Invalid
        )
        with pytest.raises(ActiveModelError, match="right must be 'C' or 'P'"):
            symbol.validate()

    def test_validate_accepts_valid_option_rights(self, test_db):
        """Test that valid option rights are accepted."""
        for right in ["C", "P"]:
            symbol = Symbol(
                database=test_db,
                conid=123456,
                symbol="AAPL",
                sec_type="OPT",
                currency="USD",
                right=right,
                strike=150.0,
                expiry="2024-12-20",
            )
            # Should not raise
            symbol.validate()

    def test_validate_stock_symbol_passes(self, test_db):
        """Test that a valid stock symbol passes validation."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        # Should not raise
        symbol.validate()

    def test_validate_underlying_conid_must_be_integer(self, test_db):
        """Test that underlying_conid must be an integer if provided."""
        symbol = Symbol(
            database=test_db,
            conid=123456,
            symbol="AAPL",
            sec_type="OPT",
            currency="USD",
            underlying_conid="not-an-int",  # Invalid
        )
        with pytest.raises(ActiveModelError, match="underlying_conid must be an integer"):
            symbol.validate()

    def test_validate_accepts_conid_zero(self, test_db):
        """Test that conid=0 is valid (edge case)."""
        symbol = Symbol(
            database=test_db,
            conid=0,  # Valid integer, though unlikely in practice
            symbol="TEST",
            sec_type="STK",
            currency="USD",
        )
        # Should not raise
        symbol.validate()


class TestSymbolSave:
    """Test Symbol save operations."""

    def test_save_new_symbol_creates_record(self, test_db):
        """Test that saving a new symbol creates a database record."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )

        result = symbol.save()
        assert result is True
        assert symbol.id is not None  # Auto-generated

        # Verify it was saved
        found = Symbol.find_by_id(test_db, symbol.id)
        assert found is not None
        assert found.conid == 265598
        assert found.symbol == "AAPL"
        assert found.sec_type == "STK"

    def test_save_new_symbol_auto_increments_id(self, test_db):
        """Test that INTEGER PRIMARY KEY auto-increments."""
        create_symbols_table(test_db)

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
            conid=265599,
            symbol="MSFT",
            sec_type="STK",
            currency="USD",
        )
        symbol2.save()

        assert symbol2.id > symbol1.id

    def test_save_updates_existing_symbol(self, test_db):
        """Test that saving an existing symbol updates it."""
        create_symbols_table(test_db)

        # Create and save initial symbol
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()
        original_id = symbol.id
        original_updated_at = symbol.updated_at

        # Update
        symbol.name = "Apple Inc."
        symbol.save()

        assert symbol.id == original_id  # ID unchanged
        assert symbol.name == "Apple Inc."
        assert symbol.updated_at != original_updated_at  # Updated timestamp changed

    def test_save_updates_existing_symbol_loaded_from_db(self, test_db):
        """Test that saving a symbol loaded from database updates it."""
        create_symbols_table(test_db)

        # Create initial symbol
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()
        symbol_id = symbol.id

        # Load from database and update
        loaded = Symbol.find_by_id(test_db, symbol_id)
        assert loaded is not None
        assert loaded.name is None or loaded.name == ""

        loaded.name = "Apple Inc."
        loaded.exchange = "NASDAQ"
        loaded.save()

        # Verify update
        updated = Symbol.find_by_id(test_db, symbol_id)
        assert updated.name == "Apple Inc."
        assert updated.exchange == "NASDAQ"

    def test_save_rejects_duplicate_conid(self, test_db):
        """Test that saving a symbol with duplicate conid raises database error."""
        create_symbols_table(test_db)

        # Create first symbol
        symbol1 = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol1.save()

        # Try to create second symbol with same conid
        symbol2 = Symbol(
            database=test_db,
            conid=265598,  # Duplicate conid
            symbol="MSFT",
            sec_type="STK",
            currency="USD",
        )

        # Should raise database error due to UNIQUE constraint
        from src.database import SQLiteError
        with pytest.raises(SQLiteError):
            symbol2.save()

    def test_save_with_full_option_data(self, test_db):
        """Test saving a symbol with full option data."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=123456,
            symbol="AAPL",
            sec_type="OPT",
            currency="USD",
            exchange="SMART",
            name="AAPL Call 150 Dec 2024",
            multiplier=100.0,
            expiry="2024-12-20",
            strike=150.0,
            right="C",
            underlying_conid=265598,
            local_symbol="AAPL  241220C00150000",
            primary_exchange="NASDAQ",
        )

        result = symbol.save()
        assert result is True

        found = Symbol.find_by_id(test_db, symbol.id)
        assert found.sec_type == "OPT"
        assert found.strike == 150.0
        assert found.right == "C"
        assert found.underlying_conid == 265598

    def test_save_validates_before_saving(self, test_db):
        """Test that save() validates before saving."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="INVALID",  # Invalid sec_type
            currency="USD",
        )

        with pytest.raises(ActiveModelError, match="sec_type must be one of"):
            symbol.save()


class TestSymbolQueries:
    """Test Symbol query methods."""

    def test_find_by_id(self, test_db):
        """Test finding symbol by ID."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        found = Symbol.find_by_id(test_db, symbol.id)
        assert found is not None
        assert found.conid == 265598
        assert found.symbol == "AAPL"

    def test_find_by_id_returns_none_if_not_found(self, test_db):
        """Test that find_by_id returns None if not found."""
        create_symbols_table(test_db)

        found = Symbol.find_by_id(test_db, 99999)
        assert found is None

    def test_find_by_conid(self, test_db):
        """Test finding symbol by IB contract ID."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        found = Symbol.find_by_conid(test_db, 265598)
        assert found is not None
        assert found.symbol == "AAPL"

    def test_find_by_conid_returns_none_if_not_found(self, test_db):
        """Test that find_by_conid returns None if not found."""
        create_symbols_table(test_db)

        found = Symbol.find_by_conid(test_db, 99999)
        assert found is None

    def test_find_by_symbol(self, test_db):
        """Test finding symbol by ticker and security type."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        found = Symbol.find_by_symbol(test_db, "AAPL", "STK")
        assert found is not None
        assert found.conid == 265598

    def test_find_by_symbol_with_sec_type(self, test_db):
        """Test finding symbol by ticker with specific sec_type."""
        create_symbols_table(test_db)

        # Create stock
        stock = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        stock.save()

        # Create option with same symbol
        option = Symbol(
            database=test_db,
            conid=123456,
            symbol="AAPL",
            sec_type="OPT",
            currency="USD",
            strike=150.0,
            expiry="2024-12-20",
            right="C",
        )
        option.save()

        # Find stock
        found_stock = Symbol.find_by_symbol(test_db, "AAPL", "STK")
        assert found_stock is not None
        assert found_stock.sec_type == "STK"

        # Find option
        found_option = Symbol.find_by_symbol(test_db, "AAPL", "OPT")
        assert found_option is not None
        assert found_option.sec_type == "OPT"

    def test_find_all(self, test_db):
        """Test finding all symbols."""
        create_symbols_table(test_db)

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
            conid=265599,
            symbol="MSFT",
            sec_type="STK",
            currency="USD",
        )
        symbol2.save()

        all_symbols = Symbol.all(test_db)
        assert len(all_symbols) == 2
        symbols_dict = {s.symbol: s for s in all_symbols}
        assert "AAPL" in symbols_dict
        assert "MSFT" in symbols_dict

    def test_where(self, test_db):
        """Test where query method."""
        create_symbols_table(test_db)

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
            conid=265599,
            symbol="MSFT",
            sec_type="STK",
            currency="USD",
        )
        symbol2.save()

        # Query by sec_type
        stocks = Symbol.where(test_db, sec_type="STK")
        assert len(stocks) == 2

        # Query by symbol
        aapl = Symbol.where(test_db, symbol="AAPL")
        assert len(aapl) == 1
        assert aapl[0].conid == 265598


class TestSymbolDelete:
    """Test Symbol delete operations."""

    def test_delete_symbol(self, test_db):
        """Test deleting a symbol."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()
        symbol_id = symbol.id

        result = symbol.delete()
        assert result is True

        # Verify it's gone
        found = Symbol.find_by_id(test_db, symbol_id)
        assert found is None

    def test_delete_without_id_raises_error(self, test_db):
        """Test that deleting a symbol without ID raises error."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        # Don't save (no ID yet)

        with pytest.raises(ValueError, match="Cannot delete"):
            symbol.delete()


class TestSymbolRepr:
    """Test Symbol string representation."""

    def test_repr_with_id(self, test_db):
        """Test __repr__ when symbol has ID."""
        create_symbols_table(test_db)

        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )
        symbol.save()

        repr_str = repr(symbol)
        assert "Symbol" in repr_str
        assert "265598" in repr_str
        assert "AAPL" in repr_str
        assert "STK" in repr_str

    def test_repr_without_id(self, test_db):
        """Test __repr__ when symbol doesn't have ID yet."""
        symbol = Symbol(
            database=test_db,
            conid=265598,
            symbol="AAPL",
            sec_type="STK",
            currency="USD",
        )

        repr_str = repr(symbol)
        assert "Symbol" in repr_str
        assert "265598" in repr_str
        assert "AAPL" in repr_str
        assert "STK" in repr_str

