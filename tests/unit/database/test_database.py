"""Unit tests for database connection management.

Tests Database class connection management logic only - using mocks.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.database import (
    Database,
    DatabaseConnectionError,
    SQLiteError,
    _sanitize_encryption_key,
)


class TestDatabaseInitialization:
    """Test Database initialization."""

    def test_initialization_stores_path_and_key(self):
        """Test that __init__ stores db_path and encryption_key."""
        with patch("src.database.Path"):
            with patch("src.database.sqlite3"):
                db = Database(db_path="/test/path.db", encryption_key="test-key")
                assert db.db_path == "/test/path.db"
                assert db.encryption_key == "test-key"

    def test_initialization_creates_parent_directory(self):
        """Test that __init__ creates parent directory."""
        with patch("src.database.Path") as mock_path:
            with patch("src.database.sqlite3"):
                Database(db_path="/test/path/to/db.db", encryption_key=None)
                # Verify mkdir was called on parent
                mock_path.assert_called_once()
                mock_path.return_value.parent.mkdir.assert_called_once_with(
                    parents=True, exist_ok=True
                )

    def test_initialization_skips_directory_for_memory_db(self):
        """Test that __init__ skips directory creation for :memory: database."""
        with patch("src.database.Path") as mock_path:
            with patch("src.database.sqlite3"):
                Database(db_path=":memory:", encryption_key=None)
                # Path should not be used for :memory: databases
                mock_path.assert_not_called()

    def test_initialization_handles_directory_creation_failure(self):
        """Test that __init__ raises DatabaseConnectionError on directory creation failure."""
        with patch("src.database.Path") as mock_path:
            with patch("src.database.sqlite3"):
                mock_path.return_value.parent.mkdir.side_effect = OSError(
                    "Permission denied"
                )

                with pytest.raises(
                    DatabaseConnectionError, match="Cannot create database directory"
                ):
                    Database(db_path="/test/path.db", encryption_key=None)

    def test_initialization_handles_absolute_path(self):
        """Test initialization with absolute path."""
        with patch("src.database.Path"):
            with patch("src.database.sqlite3"):
                db = Database(db_path="/absolute/path/to/db.db", encryption_key=None)
                assert db.db_path == "/absolute/path/to/db.db"

    def test_initialization_handles_relative_path(self):
        """Test initialization with relative path."""
        with patch("src.database.Path"):
            with patch("src.database.sqlite3"):
                db = Database(db_path="data/portfolio.db", encryption_key=None)
                assert db.db_path == "data/portfolio.db"

    def test_initialization_handles_path_with_parent_root(self):
        """Test initialization with path where parent is root."""
        with patch("src.database.Path") as mock_path:
            with patch("src.database.sqlite3"):
                Database(db_path="/db.db", encryption_key=None)
                # Should attempt to create parent (root)
                mock_path.assert_called_once()

    def test_encryption_enabled_with_key_and_sqlcipher_available(self):
        """Test encryption_enabled flag when key provided and SQLCipher available."""
        # Patch to make SQLCIPHER_AVAILABLE = True
        with patch("src.database.SQLCIPHER_AVAILABLE", True):
            with patch("src.database.sqlite3"):
                db = Database(db_path=":memory:", encryption_key="test-key")
                assert db.encryption_enabled is True

    def test_encryption_disabled_without_key(self):
        """Test encryption_enabled flag when no key provided."""
        with patch("src.database.sqlite3"):
            db = Database(db_path=":memory:", encryption_key=None)
            assert db.encryption_enabled is False

    def test_encryption_disabled_without_sqlcipher(self):
        """Test encryption_enabled flag when SQLCipher not available."""
        # Patch to make SQLCIPHER_AVAILABLE = False
        with patch("src.database.SQLCIPHER_AVAILABLE", False):
            with patch("src.database.sqlite3"):
                db = Database(db_path=":memory:", encryption_key="test-key")
                assert db.encryption_enabled is False


class TestSQLInjectionPrevention:
    """Test SQL injection prevention for encryption keys."""

    def test_sanitize_encryption_key_valid_key(self):
        """Test sanitization of valid encryption key."""
        key = "valid-key_123"
        sanitized = _sanitize_encryption_key(key)
        assert sanitized == "valid-key_123"

    def test_sanitize_encryption_key_escapes_quotes(self):
        """Test that single quotes are escaped."""
        key = "key'with'quotes"
        with pytest.raises(ValueError, match="invalid characters"):
            _sanitize_encryption_key(key)

    def test_sanitize_encryption_key_rejects_special_chars(self):
        """Test that special characters are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            _sanitize_encryption_key("key; DROP TABLE")

    def test_sanitize_encryption_key_rejects_sql_injection_attempt(self):
        """Test that SQL injection attempts are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            _sanitize_encryption_key("'; DROP TABLE accounts; --")

    def test_connect_rejects_invalid_encryption_key(self):
        """Test that _connect rejects invalid encryption key format before connecting."""
        with patch("src.database.sqlite3") as mock_sqlite3:
            with patch("src.database.Path"):
                with patch("src.database.SQLCIPHER_AVAILABLE", True):
                    db = Database(db_path=":memory:", encryption_key="invalid'key")

                    # ValueError should be raised during key validation BEFORE connection is created
                    with pytest.raises(ValueError, match="invalid characters"):
                        db._connect()

                    # Connection should NOT be attempted when key validation fails
                    mock_sqlite3.connect.assert_not_called()

    def test_connect_sanitizes_valid_encryption_key(self):
        """Test that _connect sanitizes valid encryption key."""
        with patch("src.database.sqlite3") as mock_sqlite3:
            with patch("src.database.Path"):
                with patch("src.database.SQLCIPHER_AVAILABLE", True):
                    mock_conn = MagicMock()
                    mock_sqlite3.connect.return_value = mock_conn

                    db = Database(db_path=":memory:", encryption_key="valid-key-123456")
                    db._connect()

                    # Verify sanitized key was used in PRAGMA
                    encryption_calls = [
                        str(call)
                        for call in mock_conn.execute.call_args_list
                        if "PRAGMA key" in str(call)
                    ]
                    assert len(encryption_calls) > 0
                    # Verify no quotes in the sanitized key (it was already valid)
                    assert "valid-key-123456" in str(encryption_calls[0])


class TestDatabaseConnection:
    """Test Database connection management with mocks."""

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connect_configures_connection(self, mock_path, mock_sqlite3):
        """Test that _connect configures connection with correct settings."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn

        db = Database(db_path=":memory:", encryption_key=None)
        conn = db._connect()

        # Verify sqlite3.connect called with correct args
        mock_sqlite3.connect.assert_called_once_with(
            ":memory:",
            check_same_thread=False,
            isolation_level=None,
        )

        # Verify PRAGMA commands executed with correct syntax
        assert mock_conn.execute.call_count == 2
        call_strings = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("PRAGMA journal_mode=WAL" in call_str for call_str in call_strings)
        assert any("PRAGMA foreign_keys=ON" in call_str for call_str in call_strings)

        assert conn == mock_conn

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connect_sets_encryption_when_enabled(self, mock_path, mock_sqlite3):
        """Test that _connect sets encryption key when encryption enabled."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn

        with patch("src.database.SQLCIPHER_AVAILABLE", True):
            db = Database(
                db_path=":memory:", encryption_key="test-key-12345678901234567890"
            )
            db._connect()

            # Verify encryption PRAGMA was called
            encryption_calls = [
                str(call)
                for call in mock_conn.execute.call_args_list
                if "PRAGMA key" in str(call)
            ]
            assert len(encryption_calls) > 0

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connect_handles_sqlite3_connect_failure(self, mock_path, mock_sqlite3):
        """Test that _connect raises Exception when connect fails (mocked sqlite3.Error)."""
        # When sqlite3 is mocked, sqlite3.Error is not a real exception
        # So we need to raise a real exception
        mock_sqlite3.connect.side_effect = Exception("Connection failed")

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(Exception, match="Connection failed"):
            db._connect()

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    @patch("src.database.logger")
    def test_connect_logs_pragma_failure(self, mock_logger, mock_path, mock_sqlite3):
        """Test that _connect logs and raises when PRAGMA fails."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        # Use real SQLiteError from module (captured before mocking)
        mock_conn.execute.side_effect = SQLiteError("PRAGMA failed")

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(SQLiteError, match="PRAGMA failed"):
            db._connect()

        # Verify connection was closed
        mock_conn.close.assert_called_once()
        # Verify error was logged
        mock_logger.error.assert_called()
        assert "PRAGMAs" in str(mock_logger.error.call_args)

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connection_context_manager_commits_on_success(
        self, mock_path, mock_sqlite3
    ):
        """Test that connection context manager commits on success."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn

        db = Database(db_path=":memory:", encryption_key=None)

        with db.connection():
            pass  # Success case

        # Verify commit was called
        mock_conn.commit.assert_called_once()
        # Verify close was called
        mock_conn.close.assert_called_once()
        # Verify rollback was NOT called
        mock_conn.rollback.assert_not_called()

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    @patch("src.database.logger")
    def test_connection_context_manager_rollbacks_on_sqlite_error(
        self, mock_logger, mock_path, mock_sqlite3
    ):
        """Test that connection context manager rollbacks on SQLite error."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        # Use Exception since mocked sqlite3.Error isn't a real exception
        test_error = Exception("SQLite error")

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(Exception, match="SQLite error"):
            with db.connection():
                raise test_error

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        # Verify close was called
        mock_conn.close.assert_called_once()
        # Verify commit was NOT called
        mock_conn.commit.assert_not_called()
        # Verify error was logged
        mock_logger.error.assert_called()
        assert "rolled back" in str(mock_logger.error.call_args)

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    @patch("src.database.logger")
    def test_connection_context_manager_rollbacks_on_error(
        self, mock_logger, mock_path, mock_sqlite3
    ):
        """Test that connection context manager rollbacks on exception."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        test_error = ValueError("Test error")

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(ValueError):
            with db.connection():
                raise test_error

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        # Verify close was called
        mock_conn.close.assert_called_once()
        # Verify commit was NOT called
        mock_conn.commit.assert_not_called()
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "rolled back" in str(mock_logger.error.call_args)

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    @patch("src.database.logger")
    def test_connection_context_manager_handles_connect_failure(
        self, mock_logger, mock_path, mock_sqlite3
    ):
        """Test that connection context manager handles _connect() failure."""
        # Use Exception since mocked sqlite3.Error isn't a real exception
        mock_sqlite3.connect.side_effect = Exception("Connection failed")

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(DatabaseConnectionError, match="Unexpected database error"):
            with db.connection():
                pass

        # Verify error was logged
        mock_logger.error.assert_called()
        assert "Unexpected error" in str(mock_logger.error.call_args)

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    @patch("src.database.logger")
    def test_connection_context_manager_handles_close_failure(
        self, mock_logger, mock_path, mock_sqlite3
    ):
        """Test that connection context manager handles close() failure gracefully."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        mock_conn.close.side_effect = Exception("Close failed")

        db = Database(db_path=":memory:", encryption_key=None)

        with db.connection():
            pass

        # Verify close was attempted
        mock_conn.close.assert_called_once()
        # Verify warning was logged
        mock_logger.warning.assert_called()
        assert "Error closing" in str(mock_logger.warning.call_args)

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connection_context_manager_closes_on_exception(
        self, mock_path, mock_sqlite3
    ):
        """Test that connection is closed even when exception occurs."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn

        db = Database(db_path=":memory:", encryption_key=None)

        with pytest.raises(ValueError, match="Test error"):
            with db.connection():
                raise ValueError("Test error")

        # Verify close was called in finally block
        mock_conn.close.assert_called_once()

    @patch("src.database.sqlite3")
    @patch("src.database.Path")
    def test_connection_context_manager_closes_on_success(
        self, mock_path, mock_sqlite3
    ):
        """Test that connection is closed even on successful completion."""
        mock_conn = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn

        db = Database(db_path=":memory:", encryption_key=None)

        with db.connection():
            pass  # Success case

        # Verify close was called in finally block
        mock_conn.close.assert_called_once()
