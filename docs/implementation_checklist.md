# Phase 1 Implementation Checklist (Web API, macOS-local)

This checklist guides the initial build. Keep everything local to macOS and the Client Portal Gateway. Reference:
- Tech stack: `docs/tech_stack.md`
- Web API overview: `docs/ib_web_api.md`
- Auth/session: `docs/ib_web_api_auth.md`
- Endpoints catalog: `docs/ib_web_api_endpoints.md`
- Data model: `docs/data_model.md`
- Notebook UX: `docs/notebook_ux.md`

## 1) Environment & Gateway
- Install Java 11+ (`java -version`)
- Download and extract Client Portal Gateway (Standard Release)
- Start gateway: `./bin/run.sh root/conf.yaml`
- Login in browser: `https://localhost:5000/` (2FA)
- Verify: `curl -k https://localhost:5000/v1/api/tickle`

## 2) Project Scaffolding
- Create Python package structure (src/) and tests/ with pytest
- Configure logging directory `data/logs/` and rotation policy
- Create `.env.example` for app config (no secrets)

## 3) HTTP Client & Session
- Build a small Web API client:
  - Base URL `https://localhost:5000/v1/api`
  - Cookie jar persisted in-process
  - Optional CSRF header support
  - TLS handling for self-signed cert (dev only)
- Implement `tickle()` and session status check

## 4) Endpoint Integrations (read-only)
- Accounts: `/portfolio/accounts`, `/iserver/accounts`
- Account summary/ledger: `/portfolio/{accountId}/summary`, `/ledger`
- Positions snapshot: `/portfolio/{accountId}/positions`
- Executions: `/iserver/account/trades`
- Cash transactions: `/portfolio/{accountId}/transactions?type=cash&start&end`
- Market data snapshots: `/iserver/marketdata/snapshot` (on-demand only)

## 5) Normalization Layer
- Map responses → pandas DataFrames with explicit dtypes
- Add validators for required fields and enums
- **Currency validation**: Validate all currency codes are "USD" (Phase 1 requirement)
- Convert amounts using USD-only micro-dollar conversion functions
- Emit tidy CSVs under `data/processed/` (optional)

## 6) SQLite Schema & Migrations
- Initialize SQLCipher-encrypted DB
- Apply initial schema per `docs/data_model.md`
- Record DB metadata/version

## 7) Incremental Sync & Cursors
- Implement cursors per entity with small overlap
- `sync_log` writes for every run (started_at/completed_at, records, status)
- Idempotency keys: `exec_id` (executions), compound cash key, snapshots for positions/summary

## 8) Error Handling & Retries
- Centralized retry with exponential backoff for transient errors
- Clear classification: auth/session, network, validation, API errors
- Surface errors per trigger: CLI/Notebook/logs

## 9) Data Quality Validation
- Balance reconciliation, position consistency, trades sanity, dates sanity, outlier flags
- **Currency validation**: Ensure all currency codes are "USD" (Phase 1 requirement)
- `python -m src.cli validate` command to run checks

## 10) CLI Commands (docs only now)
- `python -m src.cli status` — gateway + session + last sync
- `python -m src.cli sync --from --to [--entity]` — run incremental sync
- `python -m src.cli validate` — run data quality checks

## 11) Notebook UX Wiring
- `data_import.ipynb` controls: gateway check, sync buttons, validate, live toggle
- Panels: status, sync log, data health, errors
- Live polling for positions + quotes only while enabled

## 12) Testing Plan (outline)
- pytest config; fixtures for sample API payloads
- Unit tests for normalization/validation
- Integration tests against a mocked gateway (responses)
- Snapshot tests for schema writes

## 13) Security & Privacy
- Localhost-only access; do not store IB credentials
- Treat cookies as secrets; redact account ids in logs where appropriate
- Encrypted backups of DB/data per plan

## 14) Operations
- Operator runbook: start/stop gateway; verify; troubleshoot
- Backup job via launchd (daily incremental per plan)

## Exit Criteria for Phase 1
- One-command sync populates DB with accounts, positions, executions, cash, and summary
- Validation passes; notebooks render positions and overview
- Errors are logged and surfaced; re-login flow documented
