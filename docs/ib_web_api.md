# IBKR Client Portal Web API — macOS Local Gateway Integration

Use the IBKR Client Portal Web API via the local Client Portal Gateway (macOS, localhost-only). Live data is fetched only while a notebook is running. Responses are ephemeral and not stored.

## Scope (Web API)

- Accounts list and account summary/balances
- Portfolio/positions snapshot
- Trades/executions
- Cash transactions
- Market data snapshots (for open positions when notebook is active)

## Runtime Posture

- macOS-only, local app
- Local Client Portal Gateway (HTTPS localhost)
- Localhost-only access; no external servers
- Ephemeral responses (no persistence)

## Setup (operator)

1. Install Java (JRE 11+), verify: `java -version`
2. Download Client Portal Gateway (Standard Release)
3. Launch:
```bash
./bin/run.sh root/conf.yaml
```
4. Authenticate in browser at `https://localhost:5000/`
5. Verify:
```bash
curl -k https://localhost:5000/v1/api/tickle
```

Reference: Client Portal Web API and Gateway overview — `https://ibkrcampus.com/campus/ibkr-api-page/cpapi-v1/?utm_source=openai`
See also: Endpoint Catalog — `docs/ib_web_api_endpoints.md`
See also: Authentication & Session — `docs/ib_web_api_auth.md`
See also: Notebook UX — `docs/notebook_ux.md`
See also: Data Model — `docs/data_model.md`
See also: User Guide — `docs/user_guide.md`

## Auth & Session

- Browser login handled by the gateway (OAuth via gateway)
- Keep session alive with periodic tickle; relogin on expiry
- Self-signed TLS; client must trust local cert

## Endpoints (high level)

- Accounts list; account summary/balances
- Portfolio/positions snapshots
- Trades/executions (incremental time windows)
- Cash transactions (incremental)
- Market data snapshots (on-demand, open positions only)

## Request Cadence

- On-demand from CLI/notebook
- “Live” polling when notebook is running; stop when it stops

## Errors & Surfacing

- Surface errors in logs, CLI, or notebook (based on trigger)
- Retry transient failures with backoff; clear guidance on session issues

## Security

- Restrict to localhost
- No credential storage; treat session cookies as secrets
- Redact account identifiers in logs when appropriate


