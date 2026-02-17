# Auth Decision Record

Default model: cookie sessions with server-side revocation for first-party browser clients.

Use JWT access + refresh tokens only for external or third-party API clients that cannot use first-party session cookies.

If JWT is used:
- short-lived access tokens
- rotating refresh tokens
- refresh replay detection
- denylist support for logout and incident response

Baseline route protection is deny-by-default, with explicit role checks on privileged endpoints.

Implementation baseline in this repo:
- session cookies (`__Host-session`) + CSRF cookie/header double-submit for state-changing browser requests
- session revocation via `/v1/auth/logout` (server-side `sessions.revoked_at`)
- privileged routes (`/v1/settings/*`, `/v1/ingest/*`, `/v1/clusters/run`, `/v1/incidents` DELETE, `/v1/reports/generate`) require `admin`
- bootstrap admin credentials sourced from:
  - `WORKBENCH_BOOTSTRAP_ADMIN_USERNAME`
  - `WORKBENCH_BOOTSTRAP_ADMIN_PASSWORD`
