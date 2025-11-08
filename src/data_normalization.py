"""Data normalization layer.

Converts IBKR Web API responses to normalized format for database storage.
Handles currency conversion (micro-dollars), date parsing, and field mapping.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

# Precision constants for currency conversion
MICRO_DOLLARS = 1_000_000  # 6 decimal places for subpenny precision
JPY_PRECISION = 1_000  # 3 decimal places for JPY


def currency_to_int(amount: Decimal, currency: str = "USD") -> int:
    """Convert Decimal to fixed-point integer (micro-dollars for USD).

    Args:
        amount: Decimal amount to convert
        currency: Currency code (default: USD)

    Returns:
        Integer amount in fixed-point representation

    Note:
        Phase 1 supports USD only. Other currencies use USD precision.
    """
    if currency in ["USD", "EUR", "GBP", "CAD", "AUD"]:
        return int(amount * MICRO_DOLLARS)
    elif currency == "JPY":
        return int(amount * JPY_PRECISION)
    else:
        # Default to micro-dollars for unknown currencies
        return int(amount * MICRO_DOLLARS)


def normalize_positions(
    api_response: list[dict[str, Any]], account_id: str, snapshot_ts: str | None = None
) -> list[dict[str, Any]]:
    """Normalize positions API response to database format.

    Args:
        api_response: List of position dictionaries from API
        account_id: Account ID for these positions
        snapshot_ts: ISO-8601 snapshot timestamp (default: current UTC time)

    Returns:
        List of normalized position dictionaries ready for Position.create_from_api_data()

    Example API response:
        [
            {
                "conid": 265598,
                "symbol": "AAPL",
                "secType": "STK",
                "position": 100,
                "marketPrice": 150.25,
                "marketValue": 15025.00,
                "avgCost": 140.00,
                "currency": "USD"
            }
        ]

    Example normalized output:
        [
            {
                "account_id": "U1234567",
                "conid": 265598,
                "symbol": "AAPL",
                "sec_type": "STK",
                "quantity": 100.0,
                "market_price": 150250000,  # micro-dollars
                "market_value": 15025000000,  # micro-dollars
                "avg_cost": 140000000,  # micro-dollars
                "currency": "USD",
                "snapshot_ts": "2025-01-01T00:00:00Z",
                # Optional symbol fields
                "symbol_name": None,
                "exchange": None,
                ...
            }
        ]
    """
    if snapshot_ts is None:
        snapshot_ts = datetime.utcnow().isoformat() + "Z"

    normalized = []

    for position_data in api_response:
        # Extract required fields
        conid = position_data.get("conid")
        if conid is None:
            continue  # Skip positions without conid

        symbol = position_data.get("symbol", "")
        sec_type = position_data.get("secType", "")
        currency = position_data.get("currency", "USD")
        quantity = float(position_data.get("position", 0.0))

        # Build normalized position dict
        normalized_position: dict[str, Any] = {
            "account_id": account_id,
            "conid": conid,
            "symbol": symbol,
            "sec_type": sec_type,
            "quantity": quantity,
            "currency": currency,
            "snapshot_ts": snapshot_ts,
        }

        # Convert currency amounts to micro-dollars (INTEGER)
        if "marketPrice" in position_data and position_data["marketPrice"] is not None:
            price_decimal = Decimal(str(position_data["marketPrice"]))
            normalized_position["market_price"] = currency_to_int(price_decimal, currency)

        if "marketValue" in position_data and position_data["marketValue"] is not None:
            value_decimal = Decimal(str(position_data["marketValue"]))
            normalized_position["market_value"] = currency_to_int(value_decimal, currency)

        if "avgCost" in position_data and position_data["avgCost"] is not None:
            cost_decimal = Decimal(str(position_data["avgCost"]))
            normalized_position["avg_cost"] = currency_to_int(cost_decimal, currency)

        # Optional: unrealized_pnl and realized_pnl if provided
        if (
            "unrealizedPnl" in position_data
            and position_data["unrealizedPnl"] is not None
        ):
            pnl_decimal = Decimal(str(position_data["unrealizedPnl"]))
            normalized_position["unrealized_pnl"] = currency_to_int(pnl_decimal, currency)

        if (
            "realizedPnl" in position_data
            and position_data["realizedPnl"] is not None
        ):
            pnl_decimal = Decimal(str(position_data["realizedPnl"]))
            normalized_position["realized_pnl"] = currency_to_int(pnl_decimal, currency)

        # Optional symbol fields for automatic creation
        if "name" in position_data:
            normalized_position["symbol_name"] = position_data["name"]
        if "exchange" in position_data:
            normalized_position["exchange"] = position_data["exchange"]
        if "primaryExchange" in position_data:
            normalized_position["primary_exchange"] = position_data["primaryExchange"]
        if "localSymbol" in position_data:
            normalized_position["local_symbol"] = position_data["localSymbol"]

        # Options-specific fields
        if sec_type == "OPT":
            if "expiry" in position_data:
                normalized_position["expiry"] = position_data["expiry"]
            if "strike" in position_data and position_data["strike"] is not None:
                normalized_position["strike"] = float(position_data["strike"])
            if "right" in position_data:
                normalized_position["right"] = position_data["right"]
            if "underlyingConid" in position_data:
                normalized_position["underlying_conid"] = position_data["underlyingConid"]

        # Futures-specific fields
        if sec_type in ["FUT", "FOP"]:
            if "multiplier" in position_data and position_data["multiplier"] is not None:
                normalized_position["multiplier"] = float(position_data["multiplier"])
            if "expiry" in position_data:
                normalized_position["expiry"] = position_data["expiry"]

        normalized.append(normalized_position)

    return normalized
