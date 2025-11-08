"""Sample API response fixtures for testing."""


def sample_tickle_response():
    """Sample tickle endpoint response."""
    return {"status": "ok"}


def sample_accounts_response():
    """Sample accounts endpoint response."""
    return [{"accountId": "U1234567", "accountTitle": "Individual", "currency": "USD"}]


def sample_positions_response():
    """Sample positions endpoint response."""
    return [
        {
            "conid": 265598,
            "symbol": "AAPL",
            "secType": "STK",
            "position": 100,
            "marketPrice": 150.25,
            "marketValue": 15025.00,
            "avgCost": 140.00,
            "currency": "USD",
        },
        {
            "conid": 272093,  # Different conid for MSFT
            "symbol": "MSFT",
            "secType": "STK",
            "position": 50,
            "marketPrice": 350.50,
            "marketValue": 17525.00,
            "avgCost": 345.00,
            "currency": "USD",
            "name": "Microsoft Corporation",
            "exchange": "NASDAQ",
            "primaryExchange": "NASDAQ",
            "localSymbol": "MSFT",
        },
    ]


def sample_positions_response_with_options():
    """Sample positions response including options."""
    return [
        {
            "conid": 265598,
            "symbol": "AAPL",
            "secType": "STK",
            "position": 100,
            "marketPrice": 150.25,
            "marketValue": 15025.00,
            "avgCost": 140.00,
            "currency": "USD",
        },
        {
            "conid": 5000000,
            "symbol": "AAPL",
            "secType": "OPT",
            "position": 10,
            "marketPrice": 5.50,
            "marketValue": 550.00,
            "avgCost": 4.00,
            "currency": "USD",
            "expiry": "2025-03-21",
            "strike": 150.0,
            "right": "C",
            "underlyingConid": 265598,
        },
    ]


def sample_positions_response_empty():
    """Empty positions response."""
    return []


def sample_positions_response_with_pnl():
    """Sample positions response with P&L fields."""
    return [
        {
            "conid": 265598,
            "symbol": "AAPL",
            "secType": "STK",
            "position": 100,
            "marketPrice": 150.25,
            "marketValue": 15025.00,
            "avgCost": 140.00,
            "currency": "USD",
            "unrealizedPnl": 1025.00,
            "realizedPnl": 500.00,
        }
    ]
