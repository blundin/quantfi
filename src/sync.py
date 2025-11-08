"""Incremental sync logic for fetching and storing data from IBKR Web API."""

import logging
from datetime import datetime
from typing import Any

from src.api_client import (
    APIError,
    AuthenticationError,
    ClientError,
    IBKRAPIClient,
    NetworkError,
)
from src.data_normalization import normalize_positions
from src.database import Database
from src.models.position import Position

logger = logging.getLogger(__name__)


def sync_positions(
    database: Database, account_id: str, api_client: IBKRAPIClient | None = None
) -> dict[str, Any]:
    """Sync positions from IBKR Web API to database.

    Fetches positions from the API, normalizes the data, and saves them
    using Position.create_from_api_data() which automatically creates
    Symbols if they don't exist.

    Args:
        database: Database instance
        account_id: IB account ID to sync positions for
        api_client: Optional API client (creates one if not provided)

    Returns:
        Dictionary with sync results:
        {
            "status": "success" | "partial" | "failed",
            "positions_fetched": int,
            "positions_saved": int,
            "errors": list[str],
            "snapshot_ts": str
        }

    Raises:
        AuthenticationError: If session expired
        NetworkError: If gateway not reachable
        ClientError: If client error (400, 404, etc.)
        APIError: For retryable API errors (429, 5xx)
    """
    if api_client is None:
        api_client = IBKRAPIClient()

    snapshot_ts = datetime.utcnow().isoformat() + "Z"
    positions_saved = 0
    errors = []

    try:
        # Fetch positions from API
        logger.info(f"Fetching positions for account {account_id[:3]}****")
        logger.info(f"Calling API: GET /portfolio/{account_id}/positions")
        api_response = api_client.get_positions(account_id)
        logger.info(f"Received {len(api_response) if api_response else 0} positions from API")

        if not api_response:
            logger.info("No positions returned from API")
            return {
                "status": "success",
                "positions_fetched": 0,
                "positions_saved": 0,
                "errors": [],
                "snapshot_ts": snapshot_ts,
            }

        # Normalize API response
        logger.info(f"Normalizing {len(api_response)} positions")
        normalized_positions = normalize_positions(
            api_response, account_id, snapshot_ts
        )

        # Save each position (auto-creates Symbols if needed)
        logger.info(f"Saving {len(normalized_positions)} positions to database")
        for idx, pos_data in enumerate(normalized_positions, 1):
            logger.debug(f"Processing position {idx}/{len(normalized_positions)}: {pos_data.get('symbol', 'unknown')}")
            try:
                Position.create_from_api_data(
                    database=database,
                    account_id=pos_data["account_id"],
                    conid=pos_data["conid"],
                    symbol=pos_data["symbol"],
                    sec_type=pos_data["sec_type"],
                    quantity=pos_data["quantity"],
                    snapshot_ts=pos_data["snapshot_ts"],
                    currency=pos_data.get("currency", "USD"),
                    market_price=pos_data.get("market_price"),
                    market_value=pos_data.get("market_value"),
                    avg_cost=pos_data.get("avg_cost"),
                    unrealized_pnl=pos_data.get("unrealized_pnl"),
                    realized_pnl=pos_data.get("realized_pnl"),
                    symbol_name=pos_data.get("symbol_name"),
                    exchange=pos_data.get("exchange"),
                    primary_exchange=pos_data.get("primary_exchange"),
                    local_symbol=pos_data.get("local_symbol"),
                    expiry=pos_data.get("expiry"),
                    strike=pos_data.get("strike"),
                    right=pos_data.get("right"),
                    underlying_conid=pos_data.get("underlying_conid"),
                    multiplier=pos_data.get("multiplier"),
                )
                positions_saved += 1
                logger.debug(f"Successfully saved position: {pos_data.get('symbol', 'unknown')}")
            except Exception as e:
                error_msg = (
                    f"Failed to save position for {pos_data.get('symbol', 'unknown')}: "
                    f"{str(e)}"
                )
                logger.error(error_msg)
                errors.append(error_msg)

        # Determine status
        if errors:
            status = "partial" if positions_saved > 0 else "failed"
        else:
            status = "success"

        logger.info(
            f"Sync complete: {positions_saved}/{len(normalized_positions)} "
            f"positions saved, status: {status}"
        )

        return {
            "status": status,
            "positions_fetched": len(api_response),
            "positions_saved": positions_saved,
            "errors": errors,
            "snapshot_ts": snapshot_ts,
        }

    except (AuthenticationError, NetworkError, ClientError, APIError) as e:
        logger.error(f"Sync failed with {type(e).__name__}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sync: {str(e)}", exc_info=True)
        raise
