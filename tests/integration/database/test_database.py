"""Integration tests for database connection management.

Tests Database class with real SQLite connections to verify actual behavior.
"""

import os
import tempfile

import pytest

from src.database import Database


class TestDatabaseIntegration:
    """Integration tests with real SQLite connections."""

    def test_connection_actually_enables_wal_mode(self, temp_db_path):
        """Test that WAL mode is actually enabled in real database."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            assert result[0] == "wal"

    def test_connection_actually_enables_foreign_keys(self, temp_db_path):
        """Test that foreign keys are actually enabled in real database."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_connection_is_usable_after_setup(self, temp_db_path):
        """Test that connection is actually usable for queries after setup."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        with db.connection() as conn:
            cursor = conn.cursor()
            # Create a test table
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )
            # Insert data
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))
            # Query data
            cursor.execute("SELECT value FROM test_table WHERE id = ?", (1,))
            result = cursor.fetchone()
            assert result[0] == "test"

    def test_pragma_syntax_is_correct(self, temp_db_path):
        """Test that PRAGMA commands use correct SQL syntax."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        with db.connection() as conn:
            cursor = conn.cursor()
            
            # Test WAL mode syntax
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            assert result[0] in ["wal", "WAL"]  # SQLite may return lowercase
            
            # Test foreign keys syntax
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_autocommit_mode_allows_immediate_writes(self, temp_db_path):
        """Test that autocommit mode allows immediate writes without explicit commit."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        # Write in first connection
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test1",))

        # Read in second connection (should see the write immediately due to autocommit)
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM test_table WHERE id = ?", (1,))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "test1"

    def test_multiple_connections_work(self, temp_db_path):
        """Test that multiple connections can be created and used."""
        db = Database(db_path=temp_db_path, encryption_key=None)

        # First connection
        with db.connection() as conn1:
            cursor1 = conn1.cursor()
            cursor1.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )
            cursor1.execute("INSERT INTO test_table (value) VALUES (?)", ("test1",))

        # Second connection
        with db.connection() as conn2:
            cursor2 = conn2.cursor()
            cursor2.execute("INSERT INTO test_table (value) VALUES (?)", ("test2",))

        # Third connection - verify both writes
        with db.connection() as conn3:
            cursor3 = conn3.cursor()
            cursor3.execute("SELECT COUNT(*) FROM test_table")
            result = cursor3.fetchone()
            assert result[0] == 2

    def test_connection_creates_database_file(self, tmp_path):
        """Test that connection creates database file."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=str(db_path), encryption_key=None)

        assert not db_path.exists()

        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

        assert db_path.exists()

    def test_connection_creates_parent_directory(self, tmp_path):
        """Test that connection creates parent directory if it doesn't exist."""
        db_path = tmp_path / "subdir" / "nested" / "test.db"
        
        # Verify parent directory doesn't exist before Database creation
        assert not db_path.parent.exists()
        assert not db_path.exists()
        
        db = Database(db_path=str(db_path), encryption_key=None)

        # Database.__init__ should have created parent directory
        assert db_path.parent.exists()
        assert not db_path.exists()  # DB file not created yet

        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

        # After connection, DB file should exist
        assert db_path.parent.exists()
        assert db_path.exists()

