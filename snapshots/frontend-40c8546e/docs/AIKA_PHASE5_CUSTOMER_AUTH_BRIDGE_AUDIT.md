# AIKA — Phase 5 Customer Auth Bridge Audit

Date: 2026-08-28
Frontend branch: `feature/full-customer-e2e`
Golden baseline: `golden/phase4-commerce-stripe-20260828`

## Scope

READ-ONLY AUDIT FIRST. Do not deploy, migrate, restart services, change Stripe config, or mutate production/test order data in this audit.

Do not bypass or disable approval/security wrappers; if blocked, report the blocker.

## Why this audit is required

The formal customer login stores `client_token`, while the accepted Phase 4 order runtime currently reads `goaa_order_customer_token` / `customer_token` for customer order API access.

The new `/connect-pass` page intentionally uses the authenticated `client_token` directly when calling:

- `POST /api/v1/order/orders`
- `GET /api/v1/order/orders/{order_id}`
- `POST /api/v1/order/orders/{order_id}/connect/checkout`

We must establish whether the DO Order API already accepts the formal client-login token. Do NOT solve this by copying/aliasing tokens in localStorage unless the backend contract proves they are the same authenticated token type.

## Read-only checks on DigitalOcean

Workspace/runtime references from the accepted system:
- backend workspace: `/home/aika/.qwenpaw/workspaces/default/work/goaa-order/`
- deployed runtime: `/opt/goaa/runtime/`
- public API: `https://api.goaa.ai`

Inspect only; do not edit yet.

### 1. Client login token issuance
Find the handler for:

`POST /api/v1/client/login`

Report:
- module/file/function
- token table/storage used
- token schema/claims (do not print any real token)
- associated user id / role semantics
- expiration/revocation behavior if present

### 2. Order API authentication
Find the auth path used by:

`POST /api/v1/order/orders`

and the shared `require_auth` used by customer order endpoints.

Report:
- token table(s) checked
- accepted roles
- whether formal `client_token` is accepted today
- how authenticated `user_id` maps to the customer owner of a service order

### 3. Existing compatibility behavior
Check whether the earlier Agent auth compatibility fix has an equivalent Customer fallback/bridge.

Specifically compare:
- agent login token → order API agent role compatibility
- client login token → order API customer role compatibility

Do not change code in this step.

### 4. Safe live verification
Using an existing dedicated Test Mode customer account/token from server-side test fixtures or a freshly issued test login token **without printing the token**, make read-only/minimal-auth requests only.

Preferred verification sequence:
1. obtain/issue formal client login token in Test context
2. call a harmless authenticated customer endpoint if one exists
3. if no harmless endpoint exists, use a temporary transaction/rollback or existing owned test order to verify `GET /api/v1/order/orders/{id}`

Do NOT create a Stripe Checkout, PaymentIntent, Transfer, settlement, or invoice during this audit.

Record only HTTP status and sanitized identity/result. Never print credentials or bearer tokens.

## Decision

Return exactly one of these outcomes:

### A — ALREADY COMPATIBLE
Formal `client_token` is accepted by Order API customer endpoints and resolves to the correct customer identity.

Then recommend frontend wiring only:
- customer runtime may safely fall back to `client_token`
- `/connect-pass` may continue using `client_token`

### B — BRIDGE REQUIRED
Formal `client_token` is not accepted by Order API customer endpoints.

Then propose the smallest backend correction mirroring the accepted Agent compatibility pattern:
1. Order `require_auth` first checks existing order token auth.
2. If invalid, validate formal client-login token using the authoritative client auth store/helper.
3. Return normalized `{user_id: <client user id>, role: "customer"}`.
4. Preserve all existing ownership/role guards.
5. Customer token must remain forbidden from agent/admin endpoints.
6. No token copying, token minting in frontend, or bearer token URL parameters.

DO NOT IMPLEMENT OR RESTART until Tao approves the proposed backend change.

## Required report

Create:

`docs/PHASE5_CUSTOMER_AUTH_BRIDGE_AUDIT_RESULT.md`

Include:
- files/functions inspected
- auth stores involved
- sanitized test result/status codes
- outcome A or B
- exact minimal change proposal if B
- regression tests required
- explicit statement that no Stripe/DB/order mutation/deployment/restart occurred during audit
