# Notebook UX Specification (Jupyter)

Goal: Define a clear, lightweight UX for operating the local portfolio tracker via notebooks, aligned with macOS-local, gateway-based Web API usage, and ephemeral responses.

References:
- Web API overview: `docs/ib_web_api.md`
- Endpoints catalog: `docs/ib_web_api_endpoints.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Data model: `docs/data_model.md`
- User guide: `docs/user_guide.md`

## Notebook Index

- `data_import.ipynb` — operations, sync, monitoring (primary operator UI)
- `portfolio_tracking.ipynb` — positions, P&L, performance views
- `research_analytics.ipynb` — ad‑hoc analytics and factors
- `data_exploration.ipynb` — scratchpad / EDA

## data_import.ipynb — Controls

- Run Controls
  - "Check Gateway" button: calls `/v1/api/tickle`; shows status pill (OK / NEED LOGIN)
  - "Sync Accounts" button: fetches accounts and summaries (on‑demand)
  - "Sync Positions" button: snapshot positions (on‑demand)
  - "Sync Executions" button: incremental since last cursor with overlap
  - "Sync Cash" button: incremental since last cursor with overlap
  - "Validate Data" button: run data quality checks

- Live Mode (positions + quotes)
  - Toggle: Enable live polling for open positions only
  - Interval selector: 5s / 10s / 30s (defaults to 10s)
  - Stop button: cease polling immediately

- Parameters
  - Account selector (dropdown) if multiple become available later (single account now)
  - Date range pickers for incremental sync (start/end)
  - Overlap (minutes) numeric input (default small value)

## data_import.ipynb — Panels

- Status Panel
  - Gateway status (host/port, auth state, last tickle time)
  - Session hints ("Login required at https://localhost:5000")

- Sync Log Panel
  - Table: entity, cursor_from, cursor_to, overlap_sec, status, records, started_at, completed_at
  - Filter by entity

- Data Health Panel
  - Summaries: table counts, latest snapshot_ts per entity
  - Validation results: pass/fail badges, short messages (click to expand details)

- Error Panel
  - Recent errors with timestamp, operation, short message
  - Link to full logs

## portfolio_tracking.ipynb — Views

- Overview
  - Net liquidation, cash, gross position value (from `account_summaries` latest)
  - Small trend sparkline (recent snapshots)

- Positions
  - Table (styled): symbol, qty, avg cost, market price, market value, unrealized P&L
  - Filters: symbol contains, secType, min MV
  - Live Mode indicator (if enabled in `data_import.ipynb`)

- Executions
  - Table: time, symbol, side, qty, price, commission/fees, exchange
  - Quick aggregations: trades by day, volume by symbol

- Cash Activity
  - Table: date, type, amount, currency, description, symbol (if dividend)
  - Time window filter

## Error Surfacing

- Where to show errors
  - Inline cell output for the triggering control
  - Error Panel (appends concise row)
  - Logs (structured JSON) written to disk

- Severity
  - Info (grey): non‑blocking notes
  - Warn (yellow): retried and succeeded
  - Error (red): operation failed, user action needed

- Common cases & messages
  - Session expired (401/403): "Session expired. Please re‑authenticate at https://localhost:5000, then re‑run."
  - Gateway unavailable: "Gateway not reachable on https://localhost:5000. Start gateway and retry."
  - Validation failures: show failing rule name and first 3 offending rows

## Data Quality Checks (Validate Data)

- Balance reconciliation: cash + positions ≈ account value (tolerance)
- Position consistency: negative qty only if short; currency non‑null
- Trades: shares > 0; side in {BUY, SELL}; price > 0
- Dates: no future dates; monotonic exec times per exec_id
- Outliers: large P&L changes flagged (display only)

## UX Behaviors

- Ephemeral API responses
  - No caching beyond structured logs and optional raw JSON writes
  - Reads always normalized to DB before analytics panels

- Non‑blocking design
  - Long sync actions show progress + allow cancel
  - Live polling stops automatically on kernel stop or toggle

- Accessibility & Clarity
  - Descriptive button labels, tooltips on hover
  - High‑contrast status pills (OK / WARN / ERROR)

## Implementation Notes (for build phase)

- Widgets: prefer `ipywidgets` for controls (buttons, toggles, dropdowns)
- Rendering: `pandas.Styler` for key tables; small charts via `plotly` or `matplotlib`
- State: keep current account, cursors, and live mode in a small state dict
- Logging: write JSON logs under `data/logs/` with rotation
- Testing: notebook functions factored into Python modules to enable pytest
