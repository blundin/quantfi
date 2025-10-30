# IBKR Client Portal Web API — Authentication & Session (macOS Local Gateway)

This document details the current, supported authentication model for the Client Portal Web API using the local Client Portal Gateway (CPGW) on macOS.

References:
- Gateway & Web API overview: `https://ibkrcampus.com/campus/ibkr-api-page/cpapi-v1/?utm_source=openai`
- API reference: `https://interactivebrokers.github.io/cpwebapi/?utm_source=openai`
- Walkthrough videos: `https://www.youtube.com/watch?v=t6IsvhxwLzw&utm_source=openai`, `https://www.youtube.com/watch?v=1E0djcLjrhQ&utm_source=openai`
- Web API overview: `docs/ib_web_api.md`
- Endpoints catalog: `docs/ib_web_api_endpoints.md`
- Data model: `docs/data_model.md`
- User guide: `docs/user_guide.md`

## Prerequisites

- Java 11+ (JRE) installed
  - Verify: `java -version`
- Client Portal Gateway (Standard Release) downloaded and extracted

## Start the Gateway (operator)

From the gateway folder:
```bash
./bin/run.sh root/conf.yaml
```
- Default listen: `https://localhost:5000/`
- To change port, edit `listenPort` in `root/conf.yaml`

## Login Flow (browser)

1. Open `https://localhost:5000/`
2. Log in with IBKR credentials (2FA as required)
3. On success, a local session is established; your app can now call `https://localhost:5000/v1/api/...`

Notes:
- The gateway manages auth with IBKR. Your client uses the local session; do not implement your own OAuth/JWT flow.
- Some endpoints may require CSRF headers.

## Session Lifecycle

- Keep-alive: periodically call:
```bash
curl -k https://localhost:5000/v1/api/tickle
```
- Expiry: sessions commonly expire daily (post-midnight) or after inactivity
- Re-login: if you receive 401/403 or auth errors, instruct the user to re-auth in the browser at `https://localhost:5000/`, then retry

Recommended tickle cadence while in active use: 2–5 minutes.

## Client Considerations (TLS & Cookies)

- TLS: the gateway uses a self-signed cert
  - Development: allow insecure for curl with `-k`
  - App clients: either trust the local cert or use a per-host insecure setting in development only
- Cookies: the local session is cookie-backed; preserve cookies between requests in your HTTP client
- CSRF: some endpoints require `X-CSRF-TOKEN` header
  - Obtain token from prior response headers if presented; include the same value on subsequent modifying requests

## Common Endpoints for Auth/Status

- Keepalive: `GET /v1/api/tickle`
- Accounts context: `GET /v1/api/iserver/accounts` (often required before portfolio calls)
- Optional status: `GET /v1/api/auth/status` (if present)

## Error Handling

- 401/403 (session/auth): prompt re-login in the gateway UI; retry after success
- 5xx/network: retry with exponential backoff; cap attempts
- TLS errors: confirm gateway running; handle self-signed cert acceptance

## Troubleshooting

- "Login succeeded but API calls fail": ensure you’re hitting `https://localhost:5000/v1/api/...` and cookies are preserved
- "401/403 intermittently": session expired → re-login; add tickle during activity
- "Port in use": adjust `listenPort` in `root/conf.yaml`
- "TLS warnings": use `-k` during development or trust the cert locally

## Security Posture

- Localhost-only access; keep gateway and client on the same Mac
- Do not store IB credentials; the gateway manages login
- Treat session cookies as secrets; avoid logging sensitive headers

## Operational Checklist (macOS)

- Start gateway: `./bin/run.sh root/conf.yaml`
- Authenticate in browser: `https://localhost:5000/`
- Verify: `curl -k https://localhost:5000/v1/api/tickle`
- While active: tickle every 2–5 minutes
- On failure: re-auth then retry
