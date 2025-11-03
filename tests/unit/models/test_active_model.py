"""Unit tests for base ActiveModel class (ActiveRecord pattern).

Tests the base ActiveModel class that provides ActiveRecord-style persistence.
"""

from datetime import datetime

import pytest

from src.models.active_model import ActiveModel, ActiveModelError


class AccountTestActiveModel(ActiveModel):
    """Test ActiveModel class using TEXT primary key (like Account)."""

    table_name = "accounts"
    primary_key = "id"
    primary_key_type = "TEXT"


class PositionTestActiveModel(ActiveModel):
    """Test ActiveModel class using INTEGER primary key (like Position)."""

    table_name = "positions"
    primary_key = "id"
    primary_key_type = "INTEGER"


class TestActiveModelBase:
    """Test base ActiveModel class functionality."""

    def test_active_model_requires_table_name(self, test_db):
        """Test that ActiveModel subclasses must define table_name."""

        # Should fail if table_name is missing
        class InvalidActiveModel(ActiveModel):
            pass

        with pytest.raises(AttributeError, match="table_name"):
            InvalidActiveModel(test_db)

    def test_active_model_requires_primary_key(self, test_db):
        """Test that ActiveModel subclasses must define primary_key."""

        class InvalidActiveModel(ActiveModel):
            table_name = "test"

        with pytest.raises(AttributeError, match="primary_key"):
            InvalidActiveModel(test_db)

    def test_active_model_stores_database(self, test_db):
        """Test that ActiveModel stores Database instance."""
        account = AccountTestActiveModel(
            test_db, id="U1234567", title="Test", base_currency="USD"
        )
        assert account._database is test_db

    def test_save_creates_new_record(self, test_db):
        """Test that save() creates a new record when id is None (INTEGER PK)."""
        # Need schema first - skip if no schema
        # For now, test with mocked connection
        position = PositionTestActiveModel(test_db, quantity=100.0, currency="USD")
        position.id = None  # New record

        # This test will verify save() calls INSERT
        # Implementation will use parameterized queries
        with test_db.connection() as conn:
            cursor = conn.cursor()
            # Create a minimal test table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        result = position.save()
        assert result is True
        assert position.id is not None
        assert position.created_at is not None
        assert position.updated_at is not None

    def test_save_updates_existing_record(self, test_db):
        """Test that save() updates existing record when id is set."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            # Insert initial record
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO positions "
                    "(id, quantity, currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (1, 100.0, "USD", now, now),
            )
            conn.commit()

        position = PositionTestActiveModel(
            test_db, id=1, quantity=200.0, currency="USD"
        )
        original_updated_at = position.updated_at = datetime.utcnow().isoformat()

        result = position.save()
        assert result is True
        # updated_at should change
        assert position.updated_at != original_updated_at

        # Verify update in database
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM positions WHERE id = ?", (1,))
            row = cursor.fetchone()
            assert row[0] == 200.0

    def test_delete_removes_record(self, test_db):
        """Test that delete() removes the record from database."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO positions "
                    "(id, quantity, currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (1, 100.0, "USD", now, now),
            )
            conn.commit()

        position = PositionTestActiveModel(test_db, id=1)
        result = position.delete()
        assert result is True

        # Verify deleted
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM positions WHERE id = ?", (1,))
            count = cursor.fetchone()[0]
            assert count == 0

    def test_find_by_id_returns_record(self, test_db):
        """Test that find_by_id() returns a record or None."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Test Account", "USD", now, now),
            )
            conn.commit()

        # Find existing
        account = AccountTestActiveModel.find_by_id(test_db, "U1234567")
        assert account is not None
        assert account.id == "U1234567"
        assert account.title == "Test Account"

        # Find non-existent
        account = AccountTestActiveModel.find_by_id(test_db, "NOTEXIST")
        assert account is None

    def test_find_by_returns_first_match(self, test_db):
        """Test that find_by() returns first matching record."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )
            conn.commit()

        account = AccountTestActiveModel.find_by(test_db, base_currency="USD")
        assert account is not None
        assert account.base_currency == "USD"

        # Should return None if no match
        account = AccountTestActiveModel.find_by(test_db, base_currency="EUR")
        assert account is None

    def test_where_returns_list(self, test_db):
        """Test that where() returns list of matching records."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )
            conn.commit()

        accounts = AccountTestActiveModel.where(test_db, base_currency="USD")
        assert len(accounts) == 2
        assert all(acc.base_currency == "USD" for acc in accounts)

        # Empty result
        accounts = AccountTestActiveModel.where(test_db, base_currency="EUR")
        assert len(accounts) == 0

    def test_all_returns_all_records(self, test_db):
        """Test that all() returns all records from table."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1234567", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U7654321", "Account 2", "USD", now, now),
            )
            conn.commit()

        accounts = AccountTestActiveModel.all(test_db)
        assert len(accounts) == 2

        # Empty table
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts")
            conn.commit()

        accounts = AccountTestActiveModel.all(test_db)
        assert len(accounts) == 0


class TestActiveModelSaveHooks:
    """Test save() hook methods (_before_save, _save_to_database, _after_save)."""

    def test_before_save_hook_called_before_database_operation(self, test_db):
        """Test that _before_save() is called before database operations."""
        call_order = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _before_save(self):
                call_order.append("before_save")

            def _save_to_database(self, conn, attrs, is_new):
                call_order.append("save_to_database")

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        active_model.save()

        assert call_order == ["before_save", "save_to_database"]

    def test_after_save_hook_called_after_database_operation(self, test_db):
        """Test that _after_save() is called after successful save."""
        call_order = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _save_to_database(self, conn, attrs, is_new):
                call_order.append("save_to_database")
                super()._save_to_database(conn, attrs, is_new)

            def _after_save(self):
                call_order.append("after_save")

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        active_model.save()

        assert "save_to_database" in call_order
        assert "after_save" in call_order
        assert call_order.index("save_to_database") < call_order.index("after_save")

    def test_before_save_can_prevent_save_with_exception(self, test_db):
        """Test that _before_save() can raise exception to prevent saving."""
        call_order = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _before_save(self):
                call_order.append("before_save")
                raise ActiveModelError("Validation failed")

            def _save_to_database(self, conn, attrs, is_new):
                call_order.append("save_to_database")
                super()._save_to_database(conn, attrs, is_new)

            def _after_save(self):
                call_order.append("after_save")

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        with pytest.raises(ActiveModelError, match="Validation failed"):
            active_model.save()

        # Should not call _save_to_database or _after_save
        assert call_order == ["before_save"]
        assert "save_to_database" not in call_order
        assert "after_save" not in call_order

    def test_before_save_can_modify_attributes(self, test_db):
        """Test that _before_save() can modify attributes before saving."""

        class HookTestActiveModel(PositionTestActiveModel):
            def _before_save(self):
                # Normalize currency value
                if hasattr(self, "currency"):
                    self.currency = self.currency.upper()

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="usd")
        active_model.id = None  # New record

        active_model.save()

        # Verify currency was normalized to uppercase in database
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT currency FROM positions WHERE id = ?", (active_model.id,)
            )
            row = cursor.fetchone()
            assert row[0] == "USD"

    def test_after_save_hook_receives_saved_instance(self, test_db):
        """Test that _after_save() is called with saved instance."""
        saved_ids = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _after_save(self):
                saved_ids.append(getattr(self, "id", None))

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        active_model.save()

        # _after_save should see the auto-generated ID
        assert len(saved_ids) == 1
        assert saved_ids[0] is not None
        assert saved_ids[0] == active_model.id

    def test_custom_save_to_database_override(self, test_db):
        """Test that subclasses can override _save_to_database() completely."""
        custom_save_called = False

        class HookTestActiveModel(PositionTestActiveModel):
            def _save_to_database(self, conn, attrs, is_new):
                nonlocal custom_save_called
                custom_save_called = True

                # Custom save logic: insert with extra computed field
                cursor = conn.cursor()
                attrs.pop(self.primary_key, None)  # Remove id for INSERT
                attrs["computed_field"] = "computed_value"
                attrs["updated_at"] = datetime.utcnow().isoformat()

                columns = ", ".join(attrs.keys())
                placeholders = ", ".join("?" * len(attrs))
                query = (
                    f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                )
                cursor.execute(query, list(attrs.values()))

                # Set auto-generated ID
                setattr(self, self.primary_key, cursor.lastrowid)

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    computed_field TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        active_model.save()

        assert custom_save_called is True

        # Verify custom save worked
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT computed_field FROM positions WHERE id = ?", (active_model.id,)
            )
            row = cursor.fetchone()
            assert row[0] == "computed_value"

    def test_custom_save_to_database_for_update(self, test_db):
        """Test that _save_to_database() receives is_new=False for updates."""
        save_calls = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _save_to_database(self, conn, attrs, is_new):
                save_calls.append(is_new)
                super()._save_to_database(conn, attrs, is_new)

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            # Insert initial record
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO positions "
                    "(id, quantity, currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (1, 100.0, "USD", now, now),
            )
            conn.commit()

        active_model = HookTestActiveModel(
            test_db, id=1, quantity=200.0, currency="USD"
        )

        active_model.save()

        assert save_calls == [False]  # is_new should be False for update

    def test_after_save_not_called_on_database_error(self, test_db):
        """Test that _after_save() is not called if database operation fails."""
        after_save_called = False

        class HookTestActiveModel(PositionTestActiveModel):
            def _save_to_database(self, conn, attrs, is_new):
                # Force a database error
                cursor = conn.cursor()
                cursor.execute("INVALID SQL SYNTAX")  # This will fail

            def _after_save(self):
                nonlocal after_save_called
                after_save_called = True

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        with pytest.raises(Exception):  # SQLiteError or similar
            active_model.save()

        assert after_save_called is False

    def test_save_calls_all_hooks_in_order(self, test_db):
        """Test that save() calls all hooks in correct order."""
        call_order = []

        class HookTestActiveModel(PositionTestActiveModel):
            def _before_save(self):
                call_order.append("before")

            def _save_to_database(self, conn, attrs, is_new):
                call_order.append("save")
                super()._save_to_database(conn, attrs, is_new)

            def _after_save(self):
                call_order.append("after")

        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        active_model = HookTestActiveModel(test_db, quantity=100.0, currency="USD")
        active_model.id = None  # New record

        active_model.save()

        assert call_order == ["before", "save", "after"]


class TestActiveModelEdgeCases:
    """Test edge cases and error scenarios for ActiveModel."""

    def test_text_primary_key_requires_id_for_new_record(self, test_db):
        """Test that TEXT primary key must be provided for new records."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

        # Missing id should raise ValueError
        account = AccountTestActiveModel(test_db, title="Test", base_currency="USD")
        account.id = None  # Explicitly set to None

        with pytest.raises(ValueError, match="id is required for new"):
            account.save()

    def test_text_primary_key_saves_when_id_provided(self, test_db):
        """Test that TEXT primary key saves successfully when id is provided."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            conn.commit()

        account = AccountTestActiveModel(
            test_db, id="U1234567", title="Test Account", base_currency="USD"
        )

        result = account.save()
        assert result is True
        assert account.id == "U1234567"

        # Verify saved to database (use same connection context to ensure visibility)
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM accounts WHERE id = ?", ("U1234567",))
            row = cursor.fetchone()
            assert row is not None, "Record should exist in database"
            assert row[0] == "Test Account"

    def test_update_with_no_fields_raises_error(self, test_db):
        """Test that UPDATE with no fields to update raises ValueError.

        Note: updated_at is always set in UPDATE path, so we need to create
        a scenario where even updated_at is missing. This tests the edge case
        where _get_attributes() returns only the primary key.
        """
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            # Insert initial record
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO positions "
                    "(id, quantity, currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (1, 100.0, "USD", now, now),
            )
            conn.commit()

        # Create model with only primary key (no other attributes)
        position = PositionTestActiveModel(test_db, id=1)
        # Remove all attributes except id and _database
        # This simulates a scenario where only PK exists
        for key in list(position.__dict__.keys()):
            if key not in ["id", "_database"]:
                delattr(position, key)

        # Mock _get_attributes to return only primary key
        # (simulating the edge case where no other fields exist)
        original_get_attrs = position._get_attributes

        def mock_get_attrs():
            # Return only primary key - simulates worst case
            return {position.primary_key: getattr(position, position.primary_key)}

        position._get_attributes = mock_get_attrs

        with pytest.raises(ValueError, match="No fields to update"):
            position.save()

    def test_get_attributes_excludes_private_fields(self, test_db):
        """Test that _get_attributes() excludes private fields starting with _."""
        position = PositionTestActiveModel(test_db, quantity=100.0, currency="USD")
        position._private_field = "should_not_appear"
        position._another_private = "also_hidden"
        position.public_field = "should_appear"

        attrs = position._get_attributes()

        assert "_private_field" not in attrs
        assert "_another_private" not in attrs
        assert "_database" not in attrs
        assert "public_field" in attrs
        assert attrs["public_field"] == "should_appear"
        assert "quantity" in attrs
        assert "currency" in attrs

    def test_get_attributes_excludes_database_instance(self, test_db):
        """Test that _get_attributes() excludes _database instance."""
        position = PositionTestActiveModel(test_db, quantity=100.0, currency="USD")

        attrs = position._get_attributes()

        assert "_database" not in attrs
        assert position._database is test_db  # But it still exists on instance

    def test_timestamps_auto_set_on_new_instance(self, test_db):
        """Test that created_at and updated_at are auto-set on new instances."""
        position = PositionTestActiveModel(test_db, quantity=100.0, currency="USD")

        assert hasattr(position, "created_at")
        assert hasattr(position, "updated_at")
        assert position.created_at is not None
        assert position.updated_at is not None
        # Verify they are ISO format strings
        assert isinstance(position.created_at, str)
        assert isinstance(position.updated_at, str)
        assert "T" in position.created_at or position.created_at.endswith("Z")

    def test_provided_timestamps_are_preserved(self, test_db):
        """Test that provided timestamps are preserved on initialization."""
        custom_created = "2025-01-01T00:00:00Z"
        custom_updated = "2025-01-02T00:00:00Z"

        position = PositionTestActiveModel(
            test_db,
            quantity=100.0,
            currency="USD",
            created_at=custom_created,
            updated_at=custom_updated,
        )

        assert position.created_at == custom_created
        assert position.updated_at == custom_updated

    def test_delete_with_none_primary_key_raises_error(self, test_db):
        """Test that delete() raises ValueError when primary key is None."""
        position = PositionTestActiveModel(test_db, quantity=100.0, currency="USD")
        position.id = None

        with pytest.raises(ValueError, match="Cannot delete.*without.*id"):
            position.delete()

    def test_where_with_empty_kwargs_returns_all_records(self, test_db):
        """Test that where() with empty kwargs returns all records."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U2", "Account 2", "EUR", now, now),
            )
            conn.commit()

        accounts = AccountTestActiveModel.where(test_db)
        assert len(accounts) == 2
        assert {acc.id for acc in accounts} == {"U1", "U2"}

    def test_where_with_limit_parameter(self, test_db):
        """Test that where() respects _limit parameter."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            for i in range(5):
                cursor.execute(
                    (
                        "INSERT INTO accounts "
                        "(id, title, base_currency, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)"
                    ),
                    (f"U{i}", f"Account {i}", "USD", now, now),
                )
            conn.commit()

        accounts = AccountTestActiveModel.where(test_db, _limit=3)
        assert len(accounts) == 3

        accounts = AccountTestActiveModel.where(test_db, base_currency="USD", _limit=2)
        assert len(accounts) == 2

    def test_where_with_multiple_conditions(self, test_db):
        """Test that where() handles multiple WHERE conditions correctly."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1", "Account 1", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U2", "Account 2", "USD", now, now),
            )
            cursor.execute(
                (
                    "INSERT INTO accounts "
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U3", "Account 3", "EUR", now, now),
            )
            conn.commit()

        accounts = AccountTestActiveModel.where(
            test_db, base_currency="USD", title="Account 1"
        )
        assert len(accounts) == 1
        assert accounts[0].id == "U1"

    def test_where_uses_parameterized_queries(self, test_db):
        """Test that where() uses parameterized queries to prevent SQL injection."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
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
                    "(id, title, base_currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("U1", "Account 1", "USD", now, now),
            )
            conn.commit()

        # Attempt SQL injection - should be treated as literal value, not SQL
        malicious_input = "USD' OR '1'='1"
        accounts = AccountTestActiveModel.where(test_db, base_currency=malicious_input)

        # Should return empty (no match) rather than all records
        assert len(accounts) == 0

    def test_update_with_only_primary_key_works(self, test_db):
        """Test that UPDATE works when only primary key and timestamps are present."""
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    quantity REAL NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            now = datetime.utcnow().isoformat()
            cursor.execute(
                (
                    "INSERT INTO positions "
                    "(id, quantity, currency, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (1, 100.0, "USD", now, now),
            )
            conn.commit()

        # Create model with id and timestamps (which count as updateable fields)
        position = PositionTestActiveModel(test_db, id=1)
        original_updated_at = position.updated_at
        # Give it a moment to ensure timestamp changes
        import time

        time.sleep(0.01)

        result = position.save()
        assert result is True

        # updated_at should have changed
        assert position.updated_at != original_updated_at

        # Verify quantity and currency unchanged in database
        with test_db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT quantity, currency FROM positions WHERE id = ?", (1,)
            )
            row = cursor.fetchone()
            assert row[0] == 100.0
            assert row[1] == "USD"
