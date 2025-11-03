"""Database connection management.

Minimal database class providing connection management only.
No business logic - models handle their own persistence.
"""

import logging
import re
from contextlib import contextmanager
from pathlib import Path

try:
    from pysqlcipher3 import dbapi2 as sqlite3

    SQLCIPHER_AVAILABLE = True
except ImportError:
    import sqlite3

    SQLCIPHER_AVAILABLE = False

# Store reference to real sqlite3.Error for exception handling
# This ensures we can catch sqlite3.Error even when sqlite3 module is mocked in tests
SQLiteError = sqlite3.Error

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


def _sanitize_encryption_key(key: str) -> str:
    """Sanitize encryption key to prevent SQL injection.

    Args:
        key: Encryption key to sanitize

    Returns:
        Sanitized key safe for use in SQL PRAGMA statement

    Raises:
        ValueError: If key contains invalid characters
    """
    # Validate key format - only alphanumeric, underscore, hyphen allowed
    if not re.match(r"^[a-zA-Z0-9_-]+$", key):
        raise ValueError(
            "Encryption key contains invalid characters. "
            "Only alphanumeric, underscore, and hyphen allowed."
        )

    # Escape single quotes for SQL safety
    return key.replace("'", "''")


class Database:
    """Database connection manager.

    Provides connection management only - no business logic.
    Models use this connection for their own persistence operations.
    """

    def __init__(self, db_path: str, encryption_key: str | None = None):
        """Initialize database connection.

        Args:
            db_path: Path to database file
            encryption_key: Encryption key for SQLCipher (if enabled)

        Raises:
            DatabaseConnectionError: If directory creation or initialization fails
        """
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.encryption_enabled = encryption_key is not None and SQLCIPHER_AVAILABLE

        # Ensure data directory exists
        try:
            if db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                f"Failed to create database directory for {db_path}: {e}",
                exc_info=True,
            )
            raise DatabaseConnectionError(
                f"Cannot create database directory: {e}"
            ) from e

    @contextmanager
    def connection(self):
        """Context manager for database connections.

        Usage:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts")

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            conn = self._connect()
        except SQLiteError as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e
        except Exception as e:
            # Catch all other exceptions (including mocked sqlite3.Error in tests)
            logger.error(
                f"Unexpected error during database connection: {e}", exc_info=True
            )
            raise DatabaseConnectionError(f"Unexpected database error: {e}") from e

        try:
            yield conn
            # Note: With isolation_level=None (autocommit), commit() is a no-op
            # but we call it for clarity and in case we change the isolation level later
            conn.commit()
        except SQLiteError as e:
            conn.rollback()
            logger.error(
                f"Database transaction rolled back due to SQLite error: {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            # Catch all other exceptions (including mocked sqlite3.Error in tests)
            conn.rollback()
            logger.error(f"Database transaction rolled back: {e}", exc_info=True)
            raise
        finally:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}", exc_info=True)

    def _connect(self):
        """Create and configure database connection.

        Returns:
            sqlite3.Connection with WAL mode and foreign keys enabled

        Raises:
            sqlite3.Error: If connection or PRAGMA commands fail
            ValueError: If encryption key is invalid
        """
        # Validate and sanitize encryption key BEFORE creating connection (fail fast)
        sanitized_key = None
        if self.encryption_enabled:
            if not self.encryption_key:
                raise ValueError(
                    "Encryption key cannot be None when encryption is enabled"
                )
            # Validate key format and sanitize before attempting connection
            sanitized_key = _sanitize_encryption_key(self.encryption_key)

        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode - each statement is a transaction
                # Note: Autocommit is intentional for this use case:
                # - Read-only operations don't need complex transactions
                # - Each statement executes atomically
                # - Simpler model for single-user, local-first application
            )
        except SQLiteError as e:
            logger.error(
                f"sqlite3.connect failed for {self.db_path}: {e}", exc_info=True
            )
            raise

        try:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")

            # Set encryption key if SQLCipher is enabled
            if self.encryption_enabled:
                # Key already validated and sanitized above
                conn.execute(f"PRAGMA key = '{sanitized_key}'")

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
        except SQLiteError as e:
            conn.close()
            logger.error(f"Failed to configure database PRAGMAs: {e}", exc_info=True)
            raise

        return conn
