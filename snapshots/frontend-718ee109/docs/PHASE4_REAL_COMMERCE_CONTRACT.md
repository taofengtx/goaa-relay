# GOAA Phase 4 — Real Commerce Full Flow

Goal: replace the approved V2 browser-only demo with a real server-authoritative Test Mode flow while preserving the same UX.

## Source of truth

`Customer / Agent / Admin UI -> order-api.ts -> DO Order Engine -> PostgreSQL -> Stripe Test Mode`

No order/payment state may be written from localStorage. localStorage is allowed only for temporary test tokens and active order id.

## End-to-end business flow

1. Customer creates need/order.
2. Customer buys GOAA $39.90 one-time connection, valid 30 days.
3. Stripe webhook marks connection paid.
4. Customer requests matching; platform assigns an eligible Agent.
5. Agent independently defines service title, scope and amount.
6. Agent sends Estimate.
7. Customer accepts Estimate.
8. Customer pays Agent service fee through Stripe Test Mode.
9. Stripe webhook marks service payment paid/held.
10. Agent starts service.
11. Agent may request supplement information/files.
12. Agent uploads and submits Delivery Package.
13. Customer reviews and confirms completion.
14. Order Engine marks settlement ready.
15. Stripe Connect payout/transfer completes; webhook marks settlement paid.
16. Invoice is generated from real order/payment records and remains downloadable.

## New additive endpoints

Base: `/api/v1/order`

### Customer order creation
`POST /orders`
```json
{"need":"...","category":"insurance","serviceTitle":"..."}
```
Returns canonical `OrderSummary` with server-generated id.

### GOAA connection checkout
`POST /orders/{id}/connect/checkout`
Returns:
```json
{"checkoutUrl":"https://checkout.stripe.com/...","sessionId":"..."}
```
Frontend redirects to Stripe. Client must never mark `connectPaid=true`; only webhook/server state may do that.

### Matching
`POST /orders/{id}/match`
Requirements: connection paid, not expired, order owned by caller.

### Agent estimate
`POST /orders/{id}/estimate`
```json
{
  "serviceTitle":"家庭保障规划咨询服务",
  "amount":600,
  "scope":"需求分析\n方案比较与说明\n申请资料协助",
  "lines":[{"label":"咨询与规划","amount":600}]
}
```
Agent controls amount and scope. Backend validates positive amount, assigned agent, current stage.

### Customer accepts estimate
Existing: `POST /orders/{id}/estimate/accept`

### Service checkout
`POST /orders/{id}/payments/service/checkout`
Returns Stripe Checkout session. Client cannot directly mark payment paid.

### Invoice
`POST /orders/{id}/invoice` generates/returns invoice from canonical order/payment data.
`GET /orders/{id}/invoice` returns existing invoice or null.
Invoice minimum fields: invoice number, order id, customer display identity, agent/business identity, service title/scope, amount/currency, payment status, payment date, issue date, downloadable PDF URL.

## Existing Phase 3 endpoints remain unchanged

- GET order/events/messages/supplement/delivery
- customer estimate accept/confirm/supplement response
- agent start service/supplement/delivery
- admin order/payments/audit/actions

## Payment/security invariants

- Never expose Stripe secret keys to browser.
- Checkout sessions are created only server-side.
- Connection/service payment status changes only from verified Stripe webhook or explicit server-side test fixture.
- Agent cannot self-settle.
- Admin normal UI cannot force arbitrary paid/settled status.
- Service funds stay locked until customer confirmation and Order Engine settlement_ready.
- Stripe Connect is not described as legal escrow.
- All file/ZIP access remains order-authorized.

## Required Test Mode E2E

Create a fresh order and prove:

Customer create -> $39.9 checkout -> webhook paid -> match -> Agent Estimate custom $500 -> Customer accept -> service checkout -> webhook paid -> Agent start -> supplement -> Delivery Package -> Customer confirm -> settlement ready -> Connect Test payout -> settlement paid -> Invoice PDF.

Also prove:
- amount is Agent-defined, not hardcoded
- other customer cannot read invoice/files
- unassigned agent cannot create estimate
- payment cannot be forged by customer/agent API
- agent cannot settle
- duplicate Stripe webhook is idempotent
- invoice total equals canonical paid service amount

## Aika backend execution rule

Implement only additive Phase 4 backend changes required by this contract. Preserve Phase 3 behavior and migrations. Back up before deploy. Do not bypass or disable approval/security wrappers; if blocked, report the blocker. After deployment run full Phase 3 regression plus Phase 4 real-commerce E2E and report endpoint map, migrations, Stripe Test setup, auth/permission results, webhook idempotency, known issues, rollback and fingerprints.
