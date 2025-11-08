"""Unit tests for data normalization."""

from datetime import datetime
from decimal import Decimal

from src.data_normalization import currency_to_int, normalize_positions


class TestCurrencyToInt:
    """Test currency conversion to integer."""

    def test_usd_conversion(self):
        """Test USD conversion to micro-dollars."""
        amount = Decimal("150.25")
        result = currency_to_int(amount, "USD")
        assert result == 150250000  # 150.25 * 1,000,000

    def test_usd_with_decimals(self):
        """Test USD conversion with 6 decimal places."""
        amount = Decimal("150.251234")
        result = currency_to_int(amount, "USD")
        assert result == 150251234  # Preserves 6 decimal places

    def test_eur_conversion(self):
        """Test EUR conversion uses micro-dollars precision."""
        amount = Decimal("100.50")
        result = currency_to_int(amount, "EUR")
        assert result == 100500000

    def test_jpy_conversion(self):
        """Test JPY conversion uses 3 decimal places."""
        amount = Decimal("15000.50")
        result = currency_to_int(amount, "JPY")
        assert result == 15000500  # 15000.50 * 1,000

    def test_unknown_currency_defaults_to_micro_dollars(self):
        """Test unknown currency defaults to micro-dollars."""
        amount = Decimal("100.00")
        result = currency_to_int(amount, "XYZ")
        assert result == 100000000

    def test_zero_amount(self):
        """Test zero amount conversion."""
        amount = Decimal("0")
        result = currency_to_int(amount, "USD")
        assert result == 0

    def test_negative_amount(self):
        """Test negative amount conversion."""
        amount = Decimal("-100.50")
        result = currency_to_int(amount, "USD")
        assert result == -100500000


class TestNormalizePositions:
    """Test position data normalization."""

    def test_normalize_basic_position(self):
        """Test normalization of basic position."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "marketPrice": 150.25,
                "marketValue": 15025.00,
                "avgCost": 140.00,
                "currency": "USD",
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert len(result) == 1
        pos = result[0]
        assert pos["account_id"] == "U1234567"
        assert pos["conid"] == 265598
        assert pos["symbol"] == "AAPL"
        assert pos["sec_type"] == "STK"
        assert pos["quantity"] == 100.0
        assert pos["currency"] == "USD"
        assert pos["market_price"] == 150250000  # micro-dollars
        assert pos["market_value"] == 15025000000  # micro-dollars
        assert pos["avg_cost"] == 140000000  # micro-dollars
        assert "snapshot_ts" in pos

    def test_normalize_position_with_custom_snapshot_ts(self):
        """Test normalization with custom snapshot timestamp."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
            }
        ]

        snapshot_ts = "2025-01-15T10:30:00Z"
        result = normalize_positions(api_response, "U1234567", snapshot_ts)

        assert result[0]["snapshot_ts"] == snapshot_ts

    def test_normalize_position_with_optional_fields(self):
        """Test normalization with optional symbol fields."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "primaryExchange": "NASDAQ",
                "localSymbol": "AAPL",
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert result[0]["symbol_name"] == "Apple Inc."
        assert result[0]["exchange"] == "NASDAQ"
        assert result[0]["primary_exchange"] == "NASDAQ"
        assert result[0]["local_symbol"] == "AAPL"

    def test_normalize_position_with_pnl(self):
        """Test normalization with unrealized and realized P&L."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
                "unrealizedPnl": 1025.50,
                "realizedPnl": 500.25,
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert result[0]["unrealized_pnl"] == 1025500000  # micro-dollars
        assert result[0]["realized_pnl"] == 500250000  # micro-dollars

    def test_normalize_option_position(self):
        """Test normalization of option position."""
        api_response = [
            {
                "conid": 5000000,
                "symbol": "AAPL",
                "secType": "OPT",
                "position": 10,
                "currency": "USD",
                "expiry": "2025-03-21",
                "strike": 150.0,
                "right": "C",
                "underlyingConid": 265598,
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert result[0]["sec_type"] == "OPT"
        assert result[0]["expiry"] == "2025-03-21"
        assert result[0]["strike"] == 150.0
        assert result[0]["right"] == "C"
        assert result[0]["underlying_conid"] == 265598

    def test_normalize_future_position(self):
        """Test normalization of future position."""
        api_response = [
            {
                "conid": 6000000,
                "symbol": "ES",
                "secType": "FUT",
                "position": 2,
                "currency": "USD",
                "multiplier": 50.0,
                "expiry": "2025-03-21",
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert result[0]["sec_type"] == "FUT"
        assert result[0]["multiplier"] == 50.0
        assert result[0]["expiry"] == "2025-03-21"

    def test_normalize_multiple_positions(self):
        """Test normalization of multiple positions."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
            },
            {
                "conid": 272093,
                "symbol": "MSFT",
                "secType": "STK",
                "position": 50,
                "currency": "USD",
            },
        ]

        result = normalize_positions(api_response, "U1234567")

        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[1]["symbol"] == "MSFT"

    def test_normalize_skips_position_without_conid(self):
        """Test that positions without conid are skipped."""
        api_response = [
            {
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
                # Missing conid
            },
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
            },
        ]

        result = normalize_positions(api_response, "U1234567")

        # Should only include position with conid
        assert len(result) == 1
        assert result[0]["conid"] == 265598

    def test_normalize_handles_null_prices(self):
        """Test normalization handles null price fields."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
                # marketPrice, marketValue, avgCost are None/missing
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        assert "market_price" not in result[0]
        assert "market_value" not in result[0]
        assert "avg_cost" not in result[0]

    def test_normalize_empty_response(self):
        """Test normalization of empty response."""
        result = normalize_positions([], "U1234567")
        assert result == []

    def test_normalize_auto_generates_snapshot_ts(self):
        """Test that snapshot_ts is auto-generated if not provided."""
        api_response = [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "currency": "USD",
            }
        ]

        result = normalize_positions(api_response, "U1234567")

        # Should have snapshot_ts
        assert "snapshot_ts" in result[0]
        # Should be valid ISO-8601 with Z suffix
        assert result[0]["snapshot_ts"].endswith("Z")
        # Should be parseable
        parsed = datetime.fromisoformat(result[0]["snapshot_ts"].replace("Z", "+00:00"))
        assert parsed is not None
