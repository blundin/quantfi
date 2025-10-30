# Local Portfolio Tracking & Research — Architecture Plan

## Purpose

* Build a local‑first system to track portfolio activity and power research workflows
* Start with notebooks for speed and then (maybe) evolve to a small Flask app for repeatable views and APIs

## Scope

* Data ingest from IBKR Client Portal Web API (via local gateway) for accounts, balances, positions, executions, cash, and snapshots
* Optional ingest of market data snapshots and third‑party research datasets
* Storage in SQLite for durable tracking and DuckDB + Parquet for analytics
* Lightweight Flask app for read‑only dashboards and JSON APIs

## Non‑Goals

* No programmatic trading or live broker APIs
* No multi‑user auth or internet‑facing deployment in phase 1

## Architectural Principles

* Local‑first, offline‑capable, no external dependencies beyond HTTPS pulls
* Clear separation: tracking ledger vs analytics lake
* Reproducible pipelines, idempotent writes, and immutable raw inputs
* Human‑inspectable artifacts: raw XML, tidy CSV, Parquet partitions
* Minimal complexity now, extensible seams for later

## Data Sources

* IBKR Client Portal Web API (local gateway) for account/portfolio, executions, cash, and market data snapshots
* Manual uploads for complementary datasets (prices, ETF holdings, fundamentals)
* Optional future connectors: Robinhood exports, Betterment CSV, crypto wallets CSV

## Storage Design

* **SQLite (system of record)**
  * Tables: accounts, symbols, executions, positions, cash_transactions, account_summaries, sync_log
  * Constraints: primary keys, foreign keys, CHECKs on enums, NOT NULL on required fields
  * Indices: executions(account_id, executed_at), positions(account_id, symbol_id), cash_transactions(account_id, txn_date), sync_log(started_at)
  * WAL mode for durability and single‑writer performance
  * **Encryption**: SQLCipher for database-level encryption at rest
  * **Schema Management**: Alembic for database migrations and schema evolution
* **Analytics lake (research)**
  * Columnar Parquet in `data/lake/` partitioned by dataset and date
  * DuckDB queries over Parquet and attached SQLite for fast ad‑hoc analysis
  * **No encryption**: Research data is not sensitive

## Data Flow

* **Incremental Sync Strategy**: Pull from Web API by last-seen timestamps/ids with small overlap; prefer latest data on conflicts
* **Sync Tracking**: Store sync metadata (start/end cursors, sync timestamp, record counts) in `sync_log` table
* **Overlap Handling**: Use small time overlap (e.g., minutes/hours) to ensure no data loss between syncs
* **Conflict Resolution**: Latest timestamp wins for duplicates; log conflicts for review
* **Data Pipeline**: Call Web API → save raw JSON in `data/raw/` with timestamped names (optional, for audit)
* **Processing**: Normalize JSON to DataFrames → write tidy CSV in `data/processed/`
* **Storage**: Upsert normalized tables into encrypted SQLite ledger with sync metadata
* **Analytics**: Materialize selected analytics to Parquet for repeated use
* **Research**: Run research queries in DuckDB joining Parquet with SQLite as needed

## Development Environment

* **Cursor**: Development environment for code editing and debugging
* **Jupyter Server**: Primary UI for normal usage - tracking and research workflows
* **IBKR Client Portal Gateway**: Local-only gateway process for Web API (HTTPS on localhost)
* **CLI Tools**: Command-line interface for automated data ingestion and batch operations
* **Notebook Structure**:
  * **data_import.ipynb**: Data import controls, sync status, error monitoring, and manual triggers
  * **portfolio_tracking.ipynb**: Portfolio overview, positions, P&L, performance metrics
  * **research_analytics.ipynb**: Research workflows, factor analysis, custom queries
  * **data_exploration.ipynb**: Ad-hoc data exploration and analysis
  * See Notebook UX spec: `docs/notebook_ux.md`

## Work Order (Phase 1)

1. **Account Data via Web API**: Get basic account/positions/balances/executions/cash ingestion working
2. **Portfolio Tracking Notebooks**: Build core portfolio tracking and analysis notebooks
3. **Public Research Data**: Figure out how to get and integrate public research datasets
4. **Research Analytics Notebooks**: Develop research workflows and analytics


## Interfaces & Contracts

* Environment variables in `.env`: optional date overrides and app settings (no long-lived API secrets)
* **CLI Commands**:
  * `python -m src.cli sync --from --to`: Incremental sync by time window
  * `python -m src.cli status`: Show sync status and last update times
  * `python -m src.cli validate`: Run data validation checks
* **Web API (via local gateway, localhost-only)**:
  * Accounts list and account summary/balances (snapshots)
  * Portfolio/positions snapshot
  * Trades/executions and cash transactions (incremental fetches)
  * Market data snapshots for open positions when notebook is running
* **Notebook Interface**: `data_import.ipynb` for interactive sync controls and error monitoring
* Stable SQLite schema and Parquet folder conventions documented in README
* See Phase 1 Implementation Checklist: `docs/implementation_checklist.md`
* See Error Handling & Retry Strategies: `docs/error_handling_retry.md`
* See Security Measures: `docs/security_measures.md`
* See Testing Plan: `docs/testing_plan.md`
* See Deployment Runbook: `docs/deployment_runbook.md`
* See User Guide: `docs/user_guide.md`

## Quality & Validation

* **Schema Validation**: Alembic migrations ensure schema consistency; required columns asserted before writes
* **Data Quality Checks**:
  * Balance reconciliation (cash + positions = account value)
  * Position consistency (no negative positions without short selling flags)
  * Trade validation (buy/sell quantities match, reasonable price ranges)
  * Date validation (no future dates, logical sequence)
  * Outlier detection (unusual P&L, extreme price movements)
* **Integrity Checks**: Checksums on raw JSON files and row counts before and after ETL (if raw saved)
* **Testing Strategy**: Comprehensive pytest suite with unit tests for all code paths
* **Validation Tools**: Use pandas-profiling, great-expectations for data quality monitoring

## Security & Privacy

* **SQLite Encryption**: SQLCipher for database-level encryption at rest
* Secrets via `.env` only, never committed
* Local disk only, gitignore `data/` and SQLite DB
* **Backup Encryption**: OS-native encryption for backup archives
* Research data (Parquet) remains unencrypted as it's not sensitive

## Observability

* **Structured Logging**: JSON logs with operation timing, row counts, and error details
* **Error Handling**: Comprehensive error catching with detailed logging and notebook error display
* **Sync Monitoring**: Track sync success/failure, data freshness, and conflict resolution
* **Run Summaries**: Small JSON manifests alongside artifacts with sync metadata
* **Health Dashboard**: `data_import.ipynb` shows latest ingest status, table counts, and error logs
* **Data Freshness**: Monitor sync timestamps and alert on stale data

## Performance

* Batch inserts into SQLite with WAL and transactions
* Parquet compression for research datasets
* Optimize queries for notebook performance

## Backup & Recovery

* **Automated Backups**: macOS-native backup using `launchd` (plist) for scheduled tasks
* **Backup Strategy**: Daily incremental backups of `portfolio.db` and `data/` to timestamped, encrypted folders
* **macOS Integration**: Use `ditto` for efficient copying and `hdiutil` for encrypted disk images
* **Backup Location**: `~/Library/Application Support/QuantFi/backups/` with 30-day retention
* **Restore Procedure**: Documented restore from latest backup or CSV reconstruction
* **Testing**: Automated restore testing in CI/CD pipeline

## Roadmap

* **Phase 1: Data Ingest and Automation for Account Data**
  * Web API pull, ETL to SQLite and CSV
  * Single data_import.ipynb for manual data updates
  * Automated data ingestion pipeline

* **Phase 2: Portfolio Tracking Notebook**
  * Portfolio overview, positions, P&L, performance metrics
  * Notebook-based UI for tracking workflows

* **Phase 3: Data Ingest and Automation for Research Data on Account Positions**
  * Price history and ETF holdings in Parquet
  * Factor and options analytics data
  * Automated research data pipeline

* **Phase 4: Research Notebook**
  * Research workflows, factor analysis, custom queries
  * Data exploration and analysis

* **Phase 5: Research Data for Targets**
  * Target identification and analysis
  * Research-driven portfolio decisions

* **Phase 6: Maybe MAYBE a Flask app** (Long-term)

## Success Criteria

* **Incremental Sync**: One-command sync produces consistent JSON→CSV and SQLite writes with conflict resolution
* **Error Handling**: All errors logged and surfaced in `data_import.ipynb` with clear resolution steps
* **Data Quality**: 100% of data passes validation rules; outliers flagged for review
* **Testing**: 90%+ test coverage with comprehensive unit and integration tests
* **Performance**: Notebooks load from local data with reasonable latency on typical views
* **Extensibility**: Adding new Web API endpoints requires only parser and mapping changes

## Risks & Mitigations

* **Web API Session Issues**: Session expiration or gateway issues → retries with backoff, structured logging, and clear re-login guidance
* **Schema Drift**: API field changes → schema validation, versioned parsers, and Alembic migrations
* **Data Conflicts**: Duplicate records on reruns → idempotent upserts with conflict resolution (latest wins)
* **Database Corruption**: Data loss → automated encrypted backups and documented restore procedures
* **Sync Failures**: Partial sync failures → comprehensive error logging and manual retry capabilities
* **Data Quality**: Invalid data → comprehensive validation rules and outlier detection

## Open Questions

* Do we need historical price coverage inline or keep it external to research only
* Which research datasets to prioritize for Phase 3
* Any need for mobile‑friendly notebook views

## Implementation Notes

* **Single Account Focus**: Architecture supports multiple accounts but implementation focuses on single account for Phase 1
* **CLI + Notebook**: CLI for automation and batch jobs; notebooks for interactive control and monitoring
* **macOS Native**: Backup automation uses `launchd` and native macOS tools (`ditto`, `hdiutil`)
* **Testing Strategy**: pytest for all code with appropriate data validation tools (pandas-profiling, great-expectations)
