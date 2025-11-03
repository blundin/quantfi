"""Pytest configuration and shared fixtures."""

import os
import tempfile
from datetime import datetime

import pytest
from alembic.config import Config

from alembic import command


@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def test_db_schema(temp_db_path):
    """Create test database schema using Alembic migration."""
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option(
        "sqlalchemy.url", f"sqlite:///{os.path.abspath(temp_db_path)}"
    )
    command.upgrade(alembic_config, "head")
    yield temp_db_path


@pytest.fixture(scope="function")
def test_db(test_db_schema):
    """Create a Database instance for testing."""
    from src.database import Database

    db = Database(db_path=test_db_schema, encryption_key=None)
    return db


@pytest.fixture
def sample_account():
    """Sample account data."""
    return {
        "account_id": "U1234567",
        "title": "Individual Account",
        "base_currency": "USD",
    }


@pytest.fixture
def sample_symbol_stock():
    """Sample stock symbol data."""
    return {
        "conid": 265598,
        "symbol": "AAPL",
        "sec_type": "STK",
        "currency": "USD",
        "exchange": "NASDAQ",
        "name": "Apple Inc",
    }


@pytest.fixture
def sample_execution():
    """Sample execution data."""
    return {
        "account_id": "U1234567",
        "symbol_id": 1,  # Will be set after symbol is inserted
        "exec_id": "1234.5678",
        "order_id": 987654321,
        "side": "BUY",
        "quantity": 100.0,
        "price": 150251234,  # $150.251234 in micro-dollars
        "currency": "USD",
        "commission_amount": 100,  # $0.0001 in micro-dollars
        "commission_currency": "USD",
        "executed_at": "2025-01-15T14:30:00Z",
        "ingested_at": datetime.utcnow().isoformat() + "Z",
    }


@pytest.fixture
def sample_position():
    """Sample position snapshot data."""
    return {
        "account_id": "U1234567",
        "symbol_id": 1,  # Will be set after symbol is inserted
        "quantity": 100.0,
        "market_price": 150251234,  # $150.251234 in micro-dollars
        "market_value": 15025123400,  # $15,025.123400 in micro-dollars
        "avg_cost": 149500000,  # $149.50 in micro-dollars
        "currency": "USD",
        "snapshot_ts": datetime.utcnow().isoformat() + "Z",
    }
