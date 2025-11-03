"""ActiveRecord-style model classes for portfolio data.

Models provide object-relational mapping with ActiveRecord pattern.
"""

# Re-export Model base class for convenient imports
from src.models.active_model import ActiveModel, ActiveModelError
from src.models.account import Account

__all__ = ["ActiveModel", "ActiveModelError", "Account"]
