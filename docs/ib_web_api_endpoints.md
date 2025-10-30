# IBKR Client Portal Web API — Endpoint Catalog (Local Gateway)

This catalog lists the primary endpoints we will use via the local Client Portal Gateway on macOS.
Base URL: `https://localhost:5000`
API prefix: `/v1/api`

References:
- Web API Overview and Gateway: `https://ibkrcampus.com/campus/ibkr-api-page/cpapi-v1/?utm_source=openai`
- Official API reference: `https://interactivebrokers.github.io/cpwebapi/?utm_source=openai`
- Web API overview: `docs/ib_web_api.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Data model: `docs/data_model.md`
- User guide: `docs/user_guide.md`

## Conventions
- All requests go to `https://localhost:5000/v1/api/...`
- Some endpoints require CSRF header: `X-CSRF-TOKEN: <value>`
- Keep session warm with `GET /v1/api/tickle`
- Handle self-signed TLS locally (trust store or `-k` in curl during development)

## Health & Session

- GET `/v1/api/tickle`
  - Purpose: keep the session alive; verify gateway is running and authenticated
  - Example:
```bash
curl -k https://localhost:5000/v1/api/tickle
```
  - Example response:
```json
{"status":"ok"}
```

- GET `/v1/api/auth/status` (if available)
  - Purpose: authentication/connection status
  - Example response:
```json
{
  "authenticated": true,
  "connected": true,
  "competing": false,
  "serverInfo": {"serverName": "gdc1.ibllc.com", "serverVersion": "1.0.0"}
}
```

## User & Accounts

- GET `/v1/api/one/user`
  - Purpose: basic user/session context
  - Example:
```bash
curl -k https://localhost:5000/v1/api/one/user
```
  - Example response:
```json
{
  "userId": 123456,
  "username": "your_user",
  "email": "you@example.com"
}
```

- GET `/v1/api/portfolio/accounts`
  - Purpose: list of accessible accounts
  - Example:
```bash
curl -k https://localhost:5000/v1/api/portfolio/accounts
```
  - Example response:
```json
[
  {"accountId": "U1234567", "accountTitle": "Individual", "currency": "USD"}
]
```

- GET `/v1/api/iserver/accounts`
  - Purpose: trading session accounts context (sometimes required before portfolio calls)
  - Example response:
```json
{"accounts": ["U1234567"]}
```

## Account Summary & Balances

- GET `/v1/api/portfolio/{accountId}/summary`
  - Purpose: high-level account summary/balances snapshot
  - Path params: `accountId`
  - Example:
```bash
curl -k "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/summary"
```
  - Example response:
```json
{
  "account": "U1234567",
  "netLiquidation": 150000.12,
  "cashBalance": 12000.34,
  "grossPositionValue": 138000.00,
  "currency": "USD",
  "timestamp": "2025-10-29T15:20:00Z"
}
```

- Field reference (common keys):
  - `account` (string): IB account id (e.g., "U1234567").
  - `currency` (string): base currency, ISO 4217 (e.g., "USD").
  - `netLiquidation` (number): total account value; nullable if unavailable.
  - `cashBalance` (number): settled cash; nullable if unavailable.
  - `grossPositionValue` (number): sum of market values across positions.
  - `timestamp` (string, ISO-8601): snapshot time.

- GET `/v1/api/portfolio/{accountId}/ledger`
  - Purpose: ledger balances by currency (cash balances)
  - Path params: `accountId`
  - Example response:
```json
{
  "USD": {
    "cashbalance": 12000.34,
    "availablefunds": 11500.00,
    "excessliquidity": 20000.00
  }
}
```

- Field reference (per currency key):
  - `cashbalance` (number): cash balance in that currency.
  - `availablefunds` (number): funds available for trading.
  - `excessliquidity` (number): margin headroom; may be null for cash accounts.

## Portfolio / Positions

- GET `/v1/api/portfolio/{accountId}/positions`
  - Purpose: current positions snapshot
  - Query params: `page=0..` (pagination may apply), `sort` (optional)
  - Example:
```bash
curl -k "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/positions"
```
  - Example response:
```json
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
```

- Field reference:
  - `conid` (integer): IB contract id; primary key for market data requests.
  - `symbol` (string): ticker symbol (not unique across exchanges).
  - `secType` (string): security type, e.g., STK, OPT, FUT, FX.
  - `position` (number): quantity (negative for short); may be fractional for FX.
  - `marketPrice` (number): last/mark price used for valuation.
  - `marketValue` (number): valuation in `currency`.
  - `avgCost` (number): average cost per share/contract; may be null.
  - `currency` (string): position currency.

## Executions / Trades

- GET `/v1/api/iserver/account/trades`
  - Purpose: recent executions/trade fills
  - Notes: returns recent window; for historical, loop with time bounds where supported
  - Example:
```bash
curl -k https://localhost:5000/v1/api/iserver/account/trades
```
  - Example response:
```json
[
  {
    "execId": "1234.5678",
    "orderId": 987654321,
    "time": "2025-10-29T14:30:00Z",
    "conid": 265598,
    "symbol": "AAPL",
    "secType": "STK",
    "side": "BUY",
    "shares": 100,
    "price": 150.00,
    "currency": "USD"
  }
]
```

- Field reference:
  - `execId` (string): unique execution identifier.
  - `orderId` (integer): associated order id; useful for grouping fills.
  - `time` (string, ISO-8601): execution timestamp (UTC).
  - `conid` (integer): IB contract id of the fill.
  - `symbol` (string): ticker symbol at time of execution.
  - `secType` (string): instrument type (STK, OPT, etc.).
  - `side` (string): BUY or SELL.
  - `shares` (number): executed quantity; negative not expected.
  - `price` (number): execution price per unit.
  - `currency` (string): execution currency.

## Cash Transactions

- GET `/v1/api/portfolio/{accountId}/transactions`
  - Purpose: cash transactions and activity
  - Query params (typical): `type=cash`, `start=YYYY-MM-DD`, `end=YYYY-MM-DD`
  - Example:
```bash
curl -k "https://localhost:5000/v1/api/portfolio/ACCOUNT_ID/transactions?type=cash&start=2024-01-01&end=2024-12-31"
```
  - Example response:
```json
[
  {
    "date": "2025-10-01",
    "amount": 12.34,
    "currency": "USD",
    "type": "DIVIDEND",
    "description": "AAPL dividend"
  },
  {
    "date": "2025-10-05",
    "amount": -1.25,
    "currency": "USD",
    "type": "FEE",
    "description": "Commission"
  }
]
```

## Market Data Snapshots

- GET `/v1/api/iserver/marketdata/snapshot`
  - Purpose: snapshot quotes
  - Query params: `conids=12345,23456`, `fields=31,84,...`
  - Example:
```bash
curl -k "https://localhost:5000/v1/api/iserver/marketdata/snapshot?conids=265598&fields=31,84"
```
  - Example response:
```json
[
  {
    "conid": 265598,
    "symbol": "AAPL",
    "bidPrice": 149.50,
    "askPrice": 150.00,
    "lastPrice": 150.25,
    "volume": 1000000,
    "currency": "USD"
  }
]
```

- GET `/v1/api/iserver/marketdata/history`
  - Purpose: simple historical bars for a given contract
  - Query params: `conid=...`, `period=1d`, `bar=5min`, `exchange=SMART` (as supported)
  - Example response:
```json
{
  "bars": [
    {"t": 1698585600, "o": 148.0, "h": 151.0, "l": 147.5, "c": 149.0, "v": 2000000}
  ],
  "symbol": "AAPL",
  "conid": 265598,
  "bar": "5min",
  "period": "1d"
}
```

## Live Usage (Notebook)

- Poll positions and snapshot quotes for open positions only while notebook is running
- Stop polling when notebook stops
- Respect backoff on errors and reasonable polling intervals

## Error Handling (high-level)

- 401/403: session expired → prompt re-login in gateway UI; retry after success
- 5xx/network: retry with exponential backoff; cap attempts
- Validation errors: log and surface in CLI/notebook per trigger

## Notes

- Exact schemas/fields may evolve; consult the official reference above
- Some endpoints require calling `/v1/api/iserver/accounts` prior to account-scoped calls
- For CSRF-protected operations (rare for our read-only scope), include `X-CSRF-TOKEN`
