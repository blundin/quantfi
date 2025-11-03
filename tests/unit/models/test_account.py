"""Unit tests for Account model.

Tests the Account model's validation, persistence, and query methods.
"""

from datetime import datetime

import pytest

from src.models.account import Account
from src.models.active_model import ActiveModelError


class TestAccountFieldValidation:
    """Test Account field name validation."""

    def test_account_rejects_invalid_fields(self, test_db):
        """Test that Account rejects invalid field names in __init__."""
        with pytest.raises(ValueError, match="Invalid fields"):
            Account(
                database=test_db,
                id="U1234567",
                name="Test Account",
                base_currency="USD",
                invalid_field="should fail",  # Not in schema
            )

    def test_account_rejects_typo_in_field_name(self, test_db):
        """Test that Account catches typos in field names."""
        with pytest.raises(ValueError, match="Invalid fields"):
            Account(
                database=test_db,
                id="U1234567",
                titel="Test Account",  # Typo: should be "name"
                base_currency="USD",
            )

    def test_account_accepts_all_valid_fields(self, test_db):
        """Test that Account accepts all valid fields."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        assert account.id == "U1234567"
        assert account.name == "Test Account"
        assert account.base_currency == "USD"
        assert account.created_at is not None
        assert account.updated_at is not None


class TestAccountValidation:
    """Test Account business rule validation."""

    def test_validate_requires_base_currency_usd(self, test_db):
        """Test that validate() requires base_currency to be USD."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="EUR",  # Invalid
        )

        with pytest.raises(ActiveModelError, match="Base currency must be USD"):
            account.validate()

    def test_validate_requires_name(self, test_db):
        """Test that validate() requires name field."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="",  # Empty name
            base_currency="USD",
        )

        with pytest.raises(ActiveModelError, match="name is required"):
            account.validate()

    def test_validate_requires_id(self, test_db):
        """Test that validate() requires id field."""
        account = Account(
            database=test_db,
            id="",  # Empty id
            name="Test Account",
            base_currency="USD",
        )

        with pytest.raises(ActiveModelError, match="ID is required"):
            account.validate()

    def test_validate_passes_with_valid_data(self, test_db):
        """Test that validate() passes with valid account data."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )

        # Should not raise
        account.validate()

    def test_validate_collects_multiple_errors(self, test_db):
        """Test that validate() collects and reports all validation errors."""
        account = Account(
            database=test_db,
            id="",  # Missing
            name="",  # Missing
            base_currency="EUR",  # Invalid
        )

        with pytest.raises(ActiveModelError) as exc_info:
            account.validate()

        error_message = str(exc_info.value)
        assert "Base currency must be USD" in error_message
        assert "name is required" in error_message
        assert "ID is required" in error_message


class TestAccountSave:
    """Test Account save() method with validation."""

    def test_save_validates_before_saving(self, test_db):
        """Test that save() calls validate() before saving."""
        # Create schema first
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="EUR",  # Invalid
        )

        # Save should fail validation
        with pytest.raises(ActiveModelError, match="Base currency must be USD"):
            account.save()

    def test_save_creates_new_account(self, test_db):
        """Test that save() creates a new account record."""
        # Create schema first
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )

        result = account.save()
        assert result is True
        assert account.id == "U1234567"
        assert account.created_at is not None
        assert account.updated_at is not None

        # Verify record exists in database
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", ("U1234567",))
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "U1234567"  # id
            assert row[1] == "Test Account"  # name

    def test_save_updates_existing_account(self, test_db):
        """Test that save() updates existing account."""
        # Create schema and initial record
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Original Name", "USD", now, now),
            )

        # Load and update
        account = Account.find_by_id(test_db, "U1234567")
        assert account is not None
        assert account.name == "Original Name"

        account.name = "Updated Name"
        result = account.save()
        assert result is True

        # Verify update
        updated = Account.find_by_id(test_db, "U1234567")
        assert updated.name == "Updated Name"


class TestAccountQueries:
    """Test Account query methods (find_by_id, find_by, where, all)."""

    def test_find_by_id_returns_account(self, test_db):
        """Test that find_by_id() returns Account instance."""
        # Create schema and test data
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Test Account", "USD", now, now),
            )

        account = Account.find_by_id(test_db, "U1234567")
        assert account is not None
        assert isinstance(account, Account)
        assert account.id == "U1234567"
        assert account.name == "Test Account"
        assert account.base_currency == "USD"

    def test_find_by_id_returns_none_when_not_found(self, test_db):
        """Test that find_by_id() returns None for non-existent account."""
        # Create schema only (no data)
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        account = Account.find_by_id(test_db, "NOTEXIST")
        assert account is None

    def test_find_by_returns_first_match(self, test_db):
        """Test that find_by() returns first matching Account."""
        # Create schema and test data
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )

        account = Account.find_by(test_db, base_currency="USD")
        assert account is not None
        assert account.base_currency == "USD"

        # Should return None if no match
        account = Account.find_by(test_db, base_currency="EUR")
        assert account is None

    def test_where_returns_list_of_accounts(self, test_db):
        """Test that where() returns list of matching Accounts."""
        # Create schema and test data
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )

        accounts = Account.where(test_db, base_currency="USD")
        assert len(accounts) == 2
        assert all(isinstance(acc, Account) for acc in accounts)
        assert all(acc.base_currency == "USD" for acc in accounts)

        # Empty list if no matches
        accounts = Account.where(test_db, base_currency="EUR")
        assert accounts == []

    def test_all_returns_all_accounts(self, test_db):
        """Test that all() returns all Account records."""
        # Create schema and test data
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )

        accounts = Account.all(test_db)
        assert len(accounts) == 2
        assert all(isinstance(acc, Account) for acc in accounts)


class TestAccountDelete:
    """Test Account delete() method."""

    def test_delete_removes_account(self, test_db):
        """Test that delete() removes account from database."""
        # Create schema and test data
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, name, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Test Account", "USD", now, now),
            )

        account = Account.find_by_id(test_db, "U1234567")
        assert account is not None

        result = account.delete()
        assert result is True

        # Verify deletion
        deleted = Account.find_by_id(test_db, "U1234567")
        assert deleted is None

    def test_delete_raises_error_without_id(self, test_db):
        """Test that delete() raises error when id is not set."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )
        account.id = None  # Remove id

        with pytest.raises(ValueError, match="Cannot delete"):
            account.delete()


class TestAccountRepr:
    """Test Account __repr__ method."""

    def test_repr_returns_string_representation(self, test_db):
        """Test that __repr__() returns useful string representation."""
        account = Account(
            database=test_db,
            id="U1234567",
            name="Test Account",
            base_currency="USD",
        )

        repr_str = repr(account)
        assert "Account" in repr_str
        assert "U1234567" in repr_str
        assert "Test Account" in repr_str
