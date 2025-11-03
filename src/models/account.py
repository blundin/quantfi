"""Account model class

This model represents the Account entity.

Attributes:
- id: The account ID
- name: The account display name
- base_currency: The base currency of the account
- created_at: The timestamp of the account creation
- updated_at: The timestamp of the last account update
"""

from src.database import Database
from src.models.active_model import ActiveModel, ActiveModelError


class Account(ActiveModel):
    table_name = "accounts"
    primary_key = "id"
    primary_key_type = "TEXT"

    _allowed_fields = {
        "id",
        "name",
        "base_currency",
        "created_at",
        "updated_at",
    }

    def __init__(self, database: Database, **kwargs):
        invalid_fields = set(kwargs.keys()) - self._allowed_fields

        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}")

        super().__init__(database, **kwargs)

    def __repr__(self):
        return f"Account(id={self.id}, name={self.name})"

    def _before_save(self):
        self.validate()

    def validate(self):
        """Validate the account"""
        errors = []

        if self.base_currency != "USD":
            errors.append(f"Base currency must be USD, but got {self.base_currency}")

        if not self.name:
            errors.append("name is required")

        if not self.id:
            errors.append("ID is required for Account")

        current_fields = set(self._get_attributes().keys())
        invalid_fields = current_fields - self._allowed_fields
        if invalid_fields:
            errors.append(
                f"Invalid fields detected before save: {sorted(invalid_fields)}"
            )

        if errors:
            raise ActiveModelError(f"Validation failed: {', '.join(errors)}")
