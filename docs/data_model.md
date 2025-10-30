# Data Model & SQLite Schema (Web API)

Purpose: Define durable storage for account tracking using the IBKR Client Portal Web API. Optimized for local analytics, reconciliation, and repeatable notebook views.

Notes:
- Read-only integration (no order placement). Web API responses are ephemeral; we persist normalized data needed for tracking and analytics.
- Types are SQLite affinities; enforce constraints where possible. Use Alembic for migrations.

References:
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
- `base_currency` TEXT NOT NULL  — ISO 4217 (e.g., "USD")
- `created_at` TEXT NOT NULL  — ISO-8601 insert time
- `updated_at` TEXT NOT NULL  — ISO-8601 last update time

Indices:
- PRIMARY KEY (`id`)

## Table: symbols

- `id` INTEGER PRIMARY KEY  — Internal surrogate key
- `conid` INTEGER UNIQUE NOT NULL  — IB contract id
- `symbol` TEXT NOT NULL
- `sec_type` TEXT NOT NULL  — STK, OPT, FUT, FX, etc.
- `currency` TEXT NOT NULL  — ISO 4217
- `exchange` TEXT  — Optional
- `name` TEXT  — Optional description
- `multiplier` REAL  — Optional; options/futures
- `expiry` TEXT  — Optional; YYYY or YYYY-MM or YYYY-MM-DD
- `strike` REAL  — Optional; options
- `right` TEXT  — Optional; 'C' or 'P' for options
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
- `market_price` REAL  — nullable
- `market_value` REAL  — nullable
- `avg_cost` REAL  — nullable
- `currency` TEXT NOT NULL
- `unrealized_pnl` REAL  — nullable; can compute if not provided
- `realized_pnl` REAL  — nullable; optional snapshot convenience
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
- `shares` REAL NOT NULL
- `price` REAL NOT NULL
- `currency` TEXT NOT NULL
- `commission_amount` REAL  — nullable
- `commission_currency` TEXT  — nullable
- `fee_amount` REAL  — nullable (exchange/other fees)
- `exchange` TEXT  — nullable
- `liquidity` TEXT  — nullable; e.g., ADD/REMOVE
- `order_ref` TEXT  — nullable; user ref tag
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

## Table: cash_transactions

Purpose: Cash movements (dividends, fees, interest, deposits/withdrawals).

- `id` INTEGER PRIMARY KEY
- `account_id` TEXT NOT NULL  — FK → accounts.id
- `symbol_id` INTEGER  — nullable; FK → symbols.id (e.g., dividend source)
- `txn_date` TEXT NOT NULL  — YYYY-MM-DD
- `amount` REAL NOT NULL
- `currency` TEXT NOT NULL
- `type` TEXT NOT NULL  — e.g., DIVIDEND, FEE, INTEREST, DEPOSIT, WITHDRAWAL
- `description` TEXT  — free text
- `fx_rate_used` REAL  — nullable; if converted to base
- `base_amount` REAL  — nullable; amount in account base currency
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
- `net_liquidation` REAL  — nullable
- `cash_balance` REAL  — nullable
- `gross_position_value` REAL  — nullable
- `maintenance_margin` REAL  — nullable
- `initial_margin` REAL  — nullable
- `excess_liquidity` REAL  — nullable
- `buying_power` REAL  — nullable
- `realized_pnl_period` REAL  — nullable; e.g., day-to-date
- `unrealized_pnl_snapshot` REAL  — nullable
- `currency` TEXT NOT NULL
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

## Constraints & Validation

- Enforce NOT NULL where required; CHECK enums for `side`, `type`, `status`.
- Normalize currency codes to uppercase ISO 4217.
- Use Alembic migrations for schema evolution.

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
- Options-specific fields (multileg associations) if options trading is used
- `market_data_snapshots` only if we later decide to persist quotes (currently ephemeral)
