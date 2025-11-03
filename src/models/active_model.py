"""ActiveRecord-style base Model class.

Provides object-relational mapping with ActiveRecord pattern:
- Instance methods for persistence (save, delete)
- Class methods for queries (find_by_id, find_by, where, all)
"""

from datetime import datetime
from typing import Any, Optional

from src.database import Database, SQLiteError


class ActiveModelError(Exception):
    """Base exception for model errors."""

    pass


# Alias for consistency with ActiveModel naming
ActiveModelError = ActiveModelError


class ActiveModel:
    """Base class for ActiveRecord-style models.

    Subclasses must define:
    - table_name: Name of the database table
    - primary_key: Name of the primary key column
    - primary_key_type: Type of primary key ("TEXT" or "INTEGER")
    """

    table_name: str
    primary_key: str
    primary_key_type: str  # "TEXT" or "INTEGER"

    def __init__(self, database: Database, **kwargs):
        """Initialize model instance.

        Args:
            database: Database instance for connections
            **kwargs: Model attributes (column values)
        """
        # Validate required class attributes
        if not hasattr(self, "table_name"):
            raise AttributeError(
                f"{self.__class__.__name__} must define 'table_name' class attribute"
            )
        if not hasattr(self, "primary_key"):
            raise AttributeError(
                f"{self.__class__.__name__} must define 'primary_key' class attribute"
            )
        if not hasattr(self, "primary_key_type"):
            raise AttributeError(
                f"{self.__class__.__name__} must define "
                "'primary_key_type' class attribute"
            )

        self._database = database

        # Store all attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Initialize timestamps if not provided
        now = datetime.utcnow().isoformat()
        if not hasattr(self, "created_at"):
            self.created_at = now
        if not hasattr(self, "updated_at"):
            self.updated_at = now

    def _get_attributes(self) -> dict[str, Any]:
        """Get all non-private attributes for database operations.

        Returns:
            Dictionary of column names and values (excluding _database)
        """
        attrs = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                attrs[key] = value
        return attrs

    def _before_save(self) -> None:
        """Hook called before save operation.

        Subclasses can override to:
        - Validate data before saving
        - Normalize/prepare attributes
        - Raise ValidationError if data is invalid

        Raises:
            ModelError: If validation fails
        """
        pass

    def _save_to_database(self, conn, attrs: dict[str, Any], is_new: bool) -> None:
        """Perform the actual database INSERT or UPDATE.

        Subclasses can override this method to implement completely
        custom persistence logic (e.g., saving to multiple tables,
        computed fields, special constraints).

        Args:
            conn: Database connection
            attrs: Dictionary of attributes to save
            is_new: True for INSERT, False for UPDATE

        Raises:
            SQLiteError: If database operation fails
        """
        pk_value = attrs.get(self.primary_key)

        cursor = conn.cursor()

        if is_new:
            # INSERT new record
            if self.primary_key_type == "INTEGER":
                # INTEGER PRIMARY KEY auto-increments, exclude from INSERT
                attrs.pop(self.primary_key, None)
            else:
                # TEXT primary key must be provided
                if self.primary_key not in attrs or attrs.get(self.primary_key) is None:
                    raise ValueError(
                        f"{self.primary_key} is required for new "
                        f"{self.__class__.__name__} record"
                    )

            # Update timestamp
            self.updated_at = datetime.utcnow().isoformat()
            attrs["updated_at"] = self.updated_at

            # Build INSERT query
            columns = ", ".join(attrs.keys())
            placeholders = ", ".join("?" * len(attrs))
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

            cursor.execute(query, list(attrs.values()))

            # Get auto-generated ID if INTEGER PRIMARY KEY
            if self.primary_key_type == "INTEGER":
                setattr(self, self.primary_key, cursor.lastrowid)

        else:
            # UPDATE existing record
            # Update timestamp on instance
            self.updated_at = datetime.utcnow().isoformat()
            # Re-fetch attributes to include updated timestamp
            attrs = self._get_attributes()

            # Build UPDATE query - exclude primary key from SET clause
            update_cols = [col for col in attrs.keys() if col != self.primary_key]
            if not update_cols:
                raise ValueError("No fields to update")

            set_clauses = ", ".join(f"{col} = ?" for col in update_cols)
            query = (
                f"UPDATE {self.table_name} SET {set_clauses} "
                f"WHERE {self.primary_key} = ?"
            )

            # Prepare values: all attributes except primary key, then primary key value
            values = [attrs[col] for col in update_cols]
            values.append(pk_value)

            cursor.execute(query, values)

    def _after_save(self) -> None:
        """Hook called after successful save operation.

        Subclasses can override to:
        - Update related records
        - Trigger side effects (logging, notifications)
        - Clear caches
        """
        pass

    def save(self) -> bool:
        """Save record (insert or update).

        Uses template method pattern with hooks:
        1. _before_save() - validation/preparation hook
        2. _save_to_database() - actual persistence (can be overridden)
        3. _after_save() - post-save hook

        Subclasses can:
        - Override hooks for validation/side effects
        - Override _save_to_database() for custom persistence logic
        - Override save() entirely for completely different behavior

        Returns:
            True on success

        Raises:
            ModelError: If validation fails (from _before_save)
            SQLiteError: If database operation fails
        """
        # Pre-save hook (validation, preparation)
        self._before_save()

        attrs = self._get_attributes()
        pk_value = attrs.get(self.primary_key)

        # Determine if this is an insert or update
        # For INTEGER PK: None means new record
        # For TEXT PK: None means new record, but if PK is set, check if record exists
        is_new = pk_value is None
        if not is_new and self.primary_key_type == "TEXT":
            # Check if record exists in database
            existing = self.find_by_id(self._database, pk_value)
            is_new = existing is None

        try:
            with self._database.connection() as conn:
                # Delegate to customizable save logic
                self._save_to_database(conn, attrs, is_new)

            # Post-save hook (side effects, related records)
            self._after_save()

            return True

        except SQLiteError:
            raise

    def delete(self) -> bool:
        """Delete record from database.

        Returns:
            True on success

        Raises:
            ValueError: If primary key is not set
            SQLiteError: If database operation fails
        """
        pk_value = getattr(self, self.primary_key, None)
        if pk_value is None:
            raise ValueError(
                f"Cannot delete {self.__class__.__name__} without {self.primary_key}"
            )

        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
                cursor.execute(query, (pk_value,))
                return True

        except SQLiteError:
            raise

    @classmethod
    def find_by_id(cls, database: Database, pk_value: Any) -> Optional["ActiveModel"]:
        """Find record by primary key.

        Args:
            database: Database instance
            pk_value: Primary key value

        Returns:
            Model instance or None if not found
        """
        try:
            with database.connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {cls.table_name} WHERE {cls.primary_key} = ?"
                cursor.execute(query, (pk_value,))
                row = cursor.fetchone()

                if row is None:
                    return None

                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                data = dict(zip(columns, row))

                return cls(database, **data)

        except SQLiteError:
            raise

    @classmethod
    def find_by(cls, database: Database, **kwargs) -> Optional["ActiveModel"]:
        """Find first record matching criteria.

        Args:
            database: Database instance
            **kwargs: Column name and value pairs to match

        Returns:
            Model instance or None if not found
        """
        results = cls.where(database, **kwargs, _limit=1)
        return results[0] if results else None

    @classmethod
    def where(cls, database: Database, **kwargs) -> list["ActiveModel"]:
        """Find all records matching criteria.

        Args:
            database: Database instance
            **kwargs: Column name and value pairs to match
                Special: _limit parameter can be used to limit results

        Returns:
            List of Model instances
        """
        limit = kwargs.pop("_limit", None)

        try:
            with database.connection() as conn:
                cursor = conn.cursor()

                if kwargs:
                    # Build WHERE clause
                    where_clauses = " AND ".join(f"{col} = ?" for col in kwargs.keys())
                    query = f"SELECT * FROM {cls.table_name} WHERE {where_clauses}"
                else:
                    query = f"SELECT * FROM {cls.table_name}"

                if limit:
                    query += f" LIMIT {limit}"

                cursor.execute(query, list(kwargs.values()))
                rows = cursor.fetchall()

                if not rows:
                    return []

                # Convert rows to model instances
                columns = [desc[0] for desc in cursor.description]
                models = []
                for row in rows:
                    data = dict(zip(columns, row))
                    models.append(cls(database, **data))

                return models

        except SQLiteError:
            raise

    @classmethod
    def all(cls, database: Database) -> list["ActiveModel"]:
        """Get all records from table.

        Args:
            database: Database instance

        Returns:
            List of Model instances
        """
        return cls.where(database)
