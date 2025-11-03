# Data Model & SQLite Schema (Web API)

Purpose: Define durable storage for account tracking using the IBKR Client Portal Web API. Optimized for local analytics, reconciliation, and repeatable notebook views.

Notes:
- Read-only integration (no order placement). Web API responses are ephemeral; we persist normalized data needed for tracking and analytics.
- Types are SQLite affinities; enforce constraints where possible. Use Alembic for migrations.
- **Currency**: USD-only in Phase 1. All positions, executions, and cash transactions are USD-denominated. Foreign currency conversion and FX rate tracking are not implemented.
- **Currency amounts**: Store as INTEGER in fixed-point representation (micro-dollars = 1,000,000x for USD) to avoid floating-point precision errors while preserving the 6-decimal precision provided by IBKR Web API float values. Use `decimal.Decimal` in Python for calculations; convert from API floats → Decimal → integer at database boundaries.

References:
- Tech stack: `docs/tech_stack.md`
- Web API overview: `docs/ib_web_api.md`
- Endpoints catalog: `docs/ib_web_api_endpoints.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- User guide: `docs/user_guide.md`

## Entities & Relationships (ERD overview)

- `accounts (1)` ──< `positions (n)`
- `accounts (1)` ──< `executions (n)`
- `accounts (1)` ──< `cash_transactions (n)`
- `symbols (1)` ──< `positions (n)` and `executions (n)`
- `sync_log (1)` records each ingestion attempt and its cursors

## Table: accounts

- `id` TEXT PRIMARY KEY  — IB Account ID (e.g., "U1234567")
- `title` TEXT NOT NULL  — Display name/title
- `base_currency` TEXT NOT NULL  — ISO 4217 currency code (must be "USD" for Phase 1)
- `created_at` TEXT NOT NULL  — ISO-8601 insert time
- `updated_at` TEXT NOT NULL  — ISO-8601 last update time

Indices:
- PRIMARY KEY (`id`)

## Table: symbols

- `id` INTEGER PRIMARY KEY  — Internal surrogate key
- `conid` INTEGER UNIQUE NOT NULL  — IB contract id
- `symbol` TEXT NOT NULL
- `sec_type` TEXT NOT NULL  — STK, OPT, FUT, FX, etc.
- `currency` TEXT NOT NULL  — ISO 4217 (informational; Phase 1 expects "USD")
- `exchange` TEXT  — Optional
- `name` TEXT  — Optional description
- `multiplier` REAL  — Optional; options/futures
- `expiry` TEXT  — Optional; YYYY or YYYY-MM or YYYY-MM-DD
- `strike` REAL  — Optional; options
- `right` TEXT  — Optional; 'C' or 'P' for options
- `underlying_conid` INTEGER  — Optional; FK to underlying contract (e.g., for options, points to stock/ETF conid)
- `local_symbol` TEXT  — Optional; IB localSymbol
- `primary_exchange` TEXT  — Optional
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

Indices:
- UNIQUE (`conid`)
- INDEX (`symbol`, `sec_type`)

Source: via market/contract lookups by `conid` or from position payloads.

## Table: positions

Purpose: Latest known snapshot per account+conid. One row per position at the time of snapshot.

- `id` INTEGER PRIMARY KEY
- `account_id` TEXT NOT NULL  — FK → accounts.id
- `symbol_id` INTEGER NOT NULL  — FK → symbols.id
- `quantity` REAL NOT NULL
- `market_price` INTEGER  — nullable; price in fixed-point (micro-dollars for USD, 6 decimal places)
- `market_value` INTEGER  — nullable; value in fixed-point
- `avg_cost` INTEGER  — nullable; average cost in fixed-point
- `currency` TEXT NOT NULL  — ISO 4217 code (informational; Phase 1 expects "USD")
- `unrealized_pnl` INTEGER  — nullable; P&L in fixed-point (can compute if not provided)
- `realized_pnl` INTEGER  — nullable; realized P&L in fixed-point
- `snapshot_ts` TEXT NOT NULL  — ISO-8601 snapshot time

Constraints:
- UNIQUE (`account_id`, `symbol_id`, `snapshot_ts`)
- FK (`account_id`) REF accounts(id) ON DELETE CASCADE
- FK (`symbol_id`) REF symbols(id) ON DELETE RESTRICT

Indices:
- INDEX (`account_id`, `snapshot_ts`)
- INDEX (`symbol_id`, `snapshot_ts`)

Notes:
- For "current" positions view, select latest `snapshot_ts` per (`account_id`,`symbol_id`).
- Source: `/v1/api/portfolio/{accountId}/positions`.

## Table: executions

Purpose: Durable record of trade fills.

- `id` INTEGER PRIMARY KEY
- `account_id` TEXT NOT NULL  — FK → accounts.id
- `symbol_id` INTEGER NOT NULL  — FK → symbols.id
- `exec_id` TEXT NOT NULL  — IB execution id
- `order_id` INTEGER  — IB order id (nullable)
- `side` TEXT NOT NULL  — BUY/SELL
- `quantity` REAL NOT NULL  — executed quantity (shares for stocks/ETFs, contracts for options/futures)
- `price` INTEGER NOT NULL  — price in fixed-point (micro-dollars for USD, 6 decimal places); for options, this is premium per contract
- `currency` TEXT NOT NULL  — ISO 4217 code (informational; Phase 1 expects "USD")
- `commission_amount` INTEGER  — nullable; commission in fixed-point
- `commission_currency` TEXT  — nullable; ISO 4217 code
- `fee_amount` INTEGER  — nullable; fees in fixed-point (exchange/other fees)
- `exchange` TEXT  — nullable
- `liquidity` TEXT  — nullable; e.g., ADD/REMOVE
- `order_ref` TEXT  — nullable; user ref tag
- `execution_type` TEXT  — nullable; e.g., 'TRADE', 'EXERCISE', 'ASSIGNMENT' (for options)
- `executed_at` TEXT NOT NULL  — ISO-8601 execution time
- `ingested_at` TEXT NOT NULL  — ISO-8601 ingest time

Constraints:
- UNIQUE (`exec_id`)  — idempotency on reruns
- CHECK (`side` IN ('BUY','SELL'))
- FK (`account_id`) REF accounts(id) ON DELETE CASCADE
- FK (`symbol_id`) REF symbols(id) ON DELETE RESTRICT

Indices:
- INDEX (`account_id`, `executed_at`)
- INDEX (`symbol_id`, `executed_at`)

Source: `/v1/api/iserver/account/trades` (fields vary; keep nullable extras).

Notes:
- IBKR API returns `shares` field in JSON response; normalize to `quantity` during ingestion to support stocks, options, and other asset types consistently.

## Table: cash_transactions

Purpose: Cash movements (dividends, fees, interest, deposits/withdrawals).

- `id` INTEGER PRIMARY KEY
- `account_id` TEXT NOT NULL  — FK → accounts.id
- `symbol_id` INTEGER  — nullable; FK → symbols.id (e.g., dividend source)
- `txn_date` TEXT NOT NULL  — YYYY-MM-DD
- `amount` INTEGER NOT NULL  — amount in fixed-point (micro-dollars for USD, 6 decimal places)
- `currency` TEXT NOT NULL  — ISO 4217 code (informational; Phase 1 expects "USD")
- `type` TEXT NOT NULL  — e.g., DIVIDEND, FEE, INTEREST, DEPOSIT, WITHDRAWAL
- `description` TEXT  — free text
- `fx_rate_used` INTEGER  — nullable; Reserved for future multi-currency support (not used in Phase 1)
- `base_amount` INTEGER  — nullable; Reserved for future multi-currency support (not used in Phase 1)
- `source_id` TEXT  — API-side id if available for idempotency
- `ingested_at` TEXT NOT NULL

Constraints:
- UNIQUE (`account_id`, `txn_date`, `amount`, `type`, `source_id`)
- FK (`account_id`) REF accounts(id) ON DELETE CASCADE
- FK (`symbol_id`) REF symbols(id) ON DELETE SET NULL

Indices:
- INDEX (`account_id`, `txn_date`)
- INDEX (`type`)

Source: `/v1/api/portfolio/{accountId}/transactions?type=cash&start&end`.

## Table: account_summaries

Purpose: Snapshots to support time-series review of balances.

- `id` INTEGER PRIMARY KEY
- `account_id` TEXT NOT NULL  — FK → accounts.id
- `net_liquidation` INTEGER  — nullable; value in fixed-point
- `cash_balance` INTEGER  — nullable; balance in fixed-point
- `gross_position_value` INTEGER  — nullable; value in fixed-point
- `maintenance_margin` INTEGER  — nullable; margin in fixed-point
- `initial_margin` INTEGER  — nullable; margin in fixed-point
- `excess_liquidity` INTEGER  — nullable; liquidity in fixed-point
- `buying_power` INTEGER  — nullable; buying power in fixed-point
- `realized_pnl_period` INTEGER  — nullable; P&L in fixed-point (e.g., day-to-date)
- `unrealized_pnl_snapshot` INTEGER  — nullable; P&L in fixed-point
- `currency` TEXT NOT NULL  — ISO 4217 code (informational; Phase 1 expects "USD")
- `snapshot_ts` TEXT NOT NULL

Constraints:
- UNIQUE (`account_id`, `snapshot_ts`)
- FK (`account_id`) REF accounts(id) ON DELETE CASCADE

Indices:
- INDEX (`account_id`, `snapshot_ts`)

Source: `/v1/api/portfolio/{accountId}/summary`, `/ledger`.

## Table: sync_log

Purpose: Audit trail and idempotency. One row per sync attempt per entity group.

- `id` INTEGER PRIMARY KEY
- `entity` TEXT NOT NULL  — e.g., 'accounts','positions','executions','cash','summary'
- `account_id` TEXT  — nullable for global entities
- `cursor_from` TEXT  — ISO-8601 or opaque cursor
- `cursor_to` TEXT  — ISO-8601 or opaque cursor
- `overlap_sec` INTEGER NOT NULL DEFAULT 0
- `status` TEXT NOT NULL  — 'success','partial','failed'
- `records_fetched` INTEGER NOT NULL DEFAULT 0
- `started_at` TEXT NOT NULL
- `completed_at` TEXT  — nullable if failed
- `reference` TEXT  — optional freeform (e.g., request ids)

Indices:
- INDEX (`entity`, `account_id`, `started_at`)

## Currency Storage & Conversion

**Principle**: Store all currency amounts as INTEGER in a fixed-point representation (micro-dollars) to avoid floating-point precision errors while supporting sub-cent precision required for trading data (e.g., subpenny pricing, options, futures).

**Currency Scope - Phase 1**: USD-only. All positions, executions, and cash transactions are USD-denominated. Foreign currency conversion and FX rate tracking are not implemented.

**Precision Requirements**:
- Trading data can require precision beyond two decimal places (e.g., subpenny pricing, options/futures)
- Must support at least 6 decimal places for USD
- Use micro-dollars (1,000,000 multiplier) for 6-decimal precision, not just cents (100 multiplier)

**Conversion (USD-only)**:
- **USD**: Store in micro-dollars (multiply by 1,000,000); $150.251234 → 150251234
- **Currency field**: Stored from IBKR API for informational purposes (will be "USD" for all holdings)
- **Price fields**: All prices stored with 6-decimal precision (micro-dollars) to support subpenny pricing
- **No FX conversion**: All values are USD; no exchange rate tracking or conversion logic needed

**Python Implementation (USD-only)**:
```python
from decimal import Decimal

# Precision constants
MICRO_DOLLARS = 1_000_000  # 6 decimal places (matches IBKR Web API float precision)

def currency_to_int(amount: Decimal) -> int:
    """Convert Decimal USD amount to fixed-point integer (micro-dollars).
    
    Conversion path: IBKR API float → Decimal → integer (micro-dollars)
    This preserves the sub-cent precision provided by IBKR Web API float values.
    
    Note: USD-only implementation. Currency parameter removed for simplicity.
    """
    return int(amount * MICRO_DOLLARS)

def int_to_currency(amount_int: int) -> Decimal:
    """Convert fixed-point integer (micro-dollars) back to Decimal USD."""
    return Decimal(amount_int) / MICRO_DOLLARS

# Example: Converting from IBKR Web API response
def normalize_api_price(api_response_float: float, currency: str) -> int:
    """Convert IBKR API float (e.g., mktPrice, avgCost, price) to integer micro-dollars.
    
    IBKR Web API returns float values like 150.25 or 150.251234.
    We convert: float → Decimal (preserves precision) → integer (micro-dollars)
    
    Args:
        api_response_float: Currency amount from IBKR API (assumed USD)
        currency: Currency code from API (stored for reference, but not used in conversion)
    
    Returns:
        Integer micro-dollars (USD amounts × 1,000,000)
    """
    # Validate USD-only (Phase 1 requirement)
    if currency != 'USD':
        raise ValueError(f"Non-USD currency {currency} not supported in Phase 1")
    
    # Convert API float to Decimal first to preserve precision
    amount_decimal = Decimal(str(api_response_float))
    return currency_to_int(amount_decimal)
```

**Rationale**:
- **Matches IBKR Web API spec**: IBKR returns monetary values as `float` with sub-cent precision; micro-dollars preserve this precision
- **Cents (100x) insufficient**: Only 2 decimal places; cannot represent subpenny pricing (0.001 cent increments)
- **Micro-dollars (1,000,000x) sufficient**: Provides 6 decimal places, supporting subpenny precision required by SEC regulations and matching IBKR's float precision
- **Integer storage**: Avoids floating-point errors while maintaining full precision from API
- **Compatible**: Works with modern trading systems that require sub-cent accuracy (options, futures, subpenny pricing)

**Database Layer**: Use INTEGER columns (not BIGINT) for all currency amounts. SQLite's INTEGER type supports 64-bit signed integers, which is sufficient for storing currency values in micro-dollars up to $9.22 trillion per value.

**Integer Overflow Considerations**:
- **SQLite INTEGER limits**: Signed 64-bit integer, max value 9,223,372,036,854,775,807
- **Maximum dollar amount**: 9,223,372,036,854,775,807 ÷ 1,000,000 = **$9.22 trillion** (in micro-dollars)
- **Practical limit for individual values**: Not a concern for typical portfolios:
  - Individual accounts: $10k - $100M ✓
  - High net worth: $100M - $1B ✓
  - Large institutional: <$10B ✓
  - All well within $9.22T limit
- **Aggregate operations (SUM)**: SQLite `SUM()` can overflow if sum exceeds max integer
  - **Risk**: Summing many large positions or long transaction histories
  - **Mitigation**: Use SQLite `TOTAL()` function (returns float, no overflow) or aggregate in Python using `Decimal`
  - **Recommendation**: For balance reconciliation and analytics, prefer Python-side aggregation with `Decimal` for safety

**Conversion Flow**:
1. **Ingestion (API → DB)**: IBKR API float → `Decimal(str(float))` → `currency_to_int()` → INTEGER
2. **Calculations**: Use `Decimal` for all arithmetic operations (Python-side, not SQL SUM)
3. **Display (DB → Notebook/CLI)**: INTEGER → `int_to_currency()` → `Decimal` → format for display

**SQL Aggregate Best Practices**:
```sql
-- ❌ Avoid: Can overflow with large sums
SELECT SUM(market_value) FROM positions WHERE account_id = 'U1234567';

-- ✅ Safe: Returns float, no overflow exception
SELECT TOTAL(market_value) FROM positions WHERE account_id = 'U1234567';

-- ✅ Recommended: Aggregate in Python for precision
-- Fetch rows, convert to Decimal, sum in Python
```

This ensures we preserve the full precision provided by IBKR Web API float values while avoiding floating-point arithmetic errors in storage and calculations.

## Constraints & Validation

- Enforce NOT NULL where required; CHECK enums for `side`, `type`, `status`.
- Normalize currency codes to uppercase ISO 4217.
- **Phase 1**: Only USD supported; validate all currency codes are "USD" on ingest.
- Use Alembic migrations for schema evolution.
- All currency amounts must be `INTEGER` (not BIGINT; SQLite INTEGER is 64-bit), fixed-point with appropriate precision, never REAL/float.
- **Data Type**: SQLite `INTEGER` provides sufficient range ($9.22T max) for all currency values; no need for BIGINT.

## Incremental Sync Policy (Web API)

- Positions & Account Summary: store periodic snapshots; latest wins; do not dedupe across time.
- Executions: dedupe by `exec_id`.
- Cash Transactions: dedupe by compound key including `source_id` when provided; otherwise by date/amount/type.
- Overlap: apply small time overlap on each run (minutes-hours) to avoid gaps; record overlap in `sync_log`.

## Indices & Performance

- Access paths emphasize (`account_id`, time) for time-series views.
- Add additional indices after profiling if needed (DuckDB can attach SQLite for heavy analytics).

## Security & Privacy

- Store only required fields for analytics.
- Keep database encrypted with SQLCipher; exclude from git.

## Future Extensions

- `corporate_actions` table if needed
- Multi-leg execution tracking (spreads) — could add `leg_group_id` to link related executions
- `market_data_snapshots` only if we later decide to persist quotes (currently ephemeral)

## Asset Type Support

**Stocks & ETFs**: Fully supported via `symbols.sec_type = 'STK'`. `executions.quantity` represents share quantity.

**Options**: Supported with the following:
- Option contract details stored in `symbols` table: `strike`, `expiry`, `right` (C/P), `multiplier`
- Underlying asset relationship via `symbols.underlying_conid` (points to stock/ETF conid)
- Execution quantity in `executions.quantity` (represents contracts for options)
- Options supported with `symbols.sec_type = OPT`
- Option premium stored in `executions.price` (fixed-point micro-dollars)
- Exercise/assignment tracking via `executions.execution_type` field

**Notes**:
- IBKR Web API returns `secType: "OPT"` and uses the `shares` field in JSON response; we normalize to `quantity` during ingestion for consistent multi-asset support
- Multi-leg spreads (e.g., call spreads) execute as separate fill records with the same `order_id`; group by `order_id` to reconstruct spreads
- Assignment/exercise events may appear as stock executions with `execution_type = 'ASSIGNMENT'` or `'EXERCISE'`
