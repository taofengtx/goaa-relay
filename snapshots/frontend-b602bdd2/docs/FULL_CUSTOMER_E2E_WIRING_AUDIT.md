# GOAA Full Customer E2E Wiring Audit

Date: 2026-08-28
Branch: `feature/full-customer-e2e`
Golden baseline: `golden/phase4-commerce-stripe-20260828`

## Objective

Build one repeatable real Test Mode customer journey without rewriting the accepted Phase 4 order engine:

`Home → AI consultation → need summary → $39.90 / 30-day GOAA connection pass → Stripe Test Checkout → return/restore → match Agent → mediated communication → Agent estimate → Customer accept → Service Fee Stripe Test Checkout → service → supplement → Delivery Package → Customer confirm → Settlement Ready → Admin settlement → Stripe Connect Test Transfer → Invoice → Settled`

Golden, `main`, and Production remain untouched.

## Existing

### 1. Home + AI consultation
- `/` already renders `ChatComponent`.
- `ChatComponent` already supports guided planning topics/life stages, persistent workspace, session restore, intent/stage/known facts, and an explicit `startExecution()` transition into professional execution.
- Chat calls the real GOAA Gateway `POST /api/v1/chat` through `app/lib/openclaw.ts`; frontend does not choose model/provider.

### 2. Client authentication / resume
- `/client-login` exists.
- It stores `client_token` after real client login.
- It already has pending-purchase and auth-return concepts, so a purchase journey can resume after login instead of losing the planning workspace.

### 3. Real order / commerce API client
`app/lib/order-api.ts` already exposes the real Phase 4 operations needed for the commercial journey:
- create order
- create $39.90 connection checkout
- request match
- create/accept estimate
- create service checkout
- start service
- messages
- supplement requests/answers/files
- Delivery Package create/upload/submit/download
- customer confirm
- invoice get/generate
- admin order/payments/audit/actions

### 4. Real three-role engineering flow
- `/full-flow-live` already drives real Order API state and Stripe Test Checkout.
- It proves the back-half business sequence is wired: create → connection checkout → match → estimate → accept → service checkout → start → delivery → confirm → invoice.
- It is an engineering/debug console and exposes token inputs, so it must NOT become the formal customer journey.

### 5. Role-specific live workspaces
- `/customer-order-live`
- `/agent-order-live`
- `/admin-order-live`
- `/order-live` three-role integration center

These should be reused for order-stage execution/testing rather than rebuilt.

## Needs Wiring

### A. AI consultation → canonical service need
The planning workspace currently has enough information (`thread`, `sessionId`, `intent`, `knownFacts`, `displayTitle`, `subIntent`, `plan`) to build a need summary, but it is not yet converted into a canonical `orderApi.createOrder()` payload at the professional-execution boundary.

Required wiring:
1. When the user chooses professional execution, generate/show a concise Need Summary.
2. Require client authentication before purchase if no client session exists.
3. After auth, create one real service order using the current planning context.
4. Persist the resulting `service_order_id` in the customer journey state.

### B. Service order → $39.90 connection pass
The real API method exists, but the formal customer UI does not yet call it from the planning flow.

Required wiring:
1. Show a clear purchase card: `$39.90`, 30 days, one-time, not auto-renewing.
2. Call `createConnectCheckout(orderId, client/order customer auth)`.
3. Redirect only to the returned Stripe Test Checkout URL.
4. Preserve `service_order_id` and return target before leaving GOAA.

### C. Stripe return → restore same journey
The engineering flow can redirect to Stripe, but the formal customer flow needs deterministic restoration.

Required wiring:
1. Stripe success/cancel return must restore the same order by `service_order_id`.
2. Refresh server-side order state; never mark paid from query parameters/localStorage.
3. If `connectPaid=true`, enable/request matching.
4. If webhook has not arrived yet, show a short verifying-payment state and poll/refresh.

### D. Match → formal customer order workspace
After connection payment, customer should transition naturally into the existing order workspace rather than the debug console.

Required wiring:
- request match using the real API
- show `matching / matched / accepted` customer-friendly states
- then open/reuse `/customer-order-live?order=<id>` (or a formal wrapper around the same runtime)

### E. Customer auth token compatibility
The formal journey currently stores `client_token`, while Phase 4 debug pages use `goaa_order_customer_token`. Before implementation, backend auth compatibility for customer order endpoints must be verified. Do not copy tokens between keys as a workaround unless the backend contract explicitly supports the same token. If incompatible, add a legitimate server-side customer-auth bridge/issuance flow.

### F. Customer dashboard is still demo-backed
`/client-dashboard/orders` currently reads `goaa_order_demo_v1` from localStorage. It is not suitable as proof of the real E2E flow. It must either be migrated to the real Order API or excluded from this E2E milestone.

## Missing

### 1. Formal connection-pass purchase step
There is no dedicated production-style customer purchase state/page connected to the AI planning workspace and real service order.

### 2. Formal E2E journey coordinator
There is no single customer-side state coordinator that owns:
- planning session
- auth resume
- service_order_id
- connection checkout return
- matching transition
- handoff to customer order workspace

This can be implemented minimally with a small journey-state helper plus existing pages/components; a new large state framework is unnecessary.

### 3. User-facing payment verification state
Need a clear intermediate state after Stripe return while webhook/server state is being verified.

## Do Not Rebuild

Do NOT rebuild:
- Order Engine
- Stripe Checkout
- payment_type accounting
- matching engine
- estimate/service payment lifecycle
- supplement system
- Delivery Package/versioning
- settlement source selection
- Stripe Connect settlement
- invoice system
- Agent/Admin live workspaces

Reuse the Golden Phase 4 contracts.

## Financial invariants

1. `connection_fee` = $39.90 GOAA revenue.
2. `service_fee` = Agent professional-service payment.
3. They remain separate payments and separate business meanings.
4. Settlement source must be succeeded `service_fee`, never `connection_fee`.
5. No frontend state may manufacture `paid` or `settled`.
6. Stripe remains Test Mode for this milestone.

## Security invariants

- No bearer token inputs on formal customer UI.
- No secrets/payment secrets in URLs.
- No direct customer ↔ Agent contact information.
- Do not bypass or disable approval/security wrappers; if blocked, report the blocker.
- Do not weaken cross-order file permissions.
- Golden, main, and Production are not modified in this milestone.

## Minimal implementation plan

### Step 1 — Journey state + Need Summary
Add a small customer E2E journey helper/state object containing planning session reference, need summary, order id, and return state. Wire `ChatComponent.startExecution()` to a customer-facing Need Summary / connect-pass step.

### Step 2 — Auth-safe real order creation
Verify whether `client_token` is accepted by Order API customer endpoints. If yes, use it directly. If not, implement the legitimate backend token bridge/issuance before proceeding. No localStorage token alias hacks.

### Step 3 — $39.90 checkout + return restoration
Create the real order once, launch connection checkout, restore the same order after Stripe return, refresh until webhook-backed `connectPaid=true`, then request matching.

### Step 4 — Handoff to existing order workspace
Route the customer into the existing real customer order workspace with the same `service_order_id`. Agent and Admin continue using their existing formal/live role pages.

### Step 5 — Replace/exclude demo customer order list
For this milestone, either migrate `/client-dashboard/orders` to real API data or clearly keep it out of the E2E path. Never present its localStorage demo state as real evidence.

### Step 6 — E2E acceptance
Run three windows around one new service order:
- Customer starts at `/`, not at an order page.
- Agent starts at `/agent-login` → Agent Console.
- Admin uses Admin live console.

Acceptance requires real server state through the entire Test Mode flow and the same `service_order_id` throughout.

## Recommended first coding slice

Implement only Steps 1–3 first:

`AI consultation → Need Summary → login/resume → create real order → $39.90 Stripe Test Checkout → return → verify connectPaid → request match → handoff`

Then STOP for manual browser validation before touching the already-accepted service/settlement back half.
