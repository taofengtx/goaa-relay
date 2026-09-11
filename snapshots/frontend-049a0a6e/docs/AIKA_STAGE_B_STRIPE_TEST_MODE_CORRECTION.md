# GOAA.ai Phase 4 — Stage B Stripe Test Mode Correction

Status: Stage A backend is green; Golden frontend must remain unchanged.

## Stripe architecture confirmed

GOAA is a two-sided service marketplace. Customer pays the platform, service provider fulfills the service, and GOAA releases funds after customer confirmation.

Use Stripe Connect **Separate Charges and Transfers** for the service-payment flow. Do not use Destination Charges for hold-and-release behavior.

### Commercial flow

1. Customer pays GOAA Connection Fee: $39.90 one-time, 30 days valid.
2. GOAA matches an eligible professional.
3. Professional defines service title/scope/price.
4. Customer accepts estimate.
5. GOAA platform creates Stripe Checkout for the accepted estimate amount.
6. `checkout.session.completed` verified webhook marks service payment paid.
7. Funds remain on platform until service completion.
8. Customer confirms completion -> settlement_ready.
9. Server creates Stripe Connect Transfer to the assigned professional.
10. Verified `transfer.created` marks GOAA settlement paid/transferred.
11. `transfer.updated` and `transfer.reversed` are tracked for audit/exception handling.
12. Future bank payout tracking may use connected-account `payout.*` events, but that is a separate layer.

## Important corrections

- Do not depend on a real `transfer.paid` event. It is not a current Connect Transfer event.
- Do not call the mechanism escrow.
- Do not mark payment from frontend redirects or client-side state.
- Canonical amounts come from server-side order/accepted estimate data only.
- Platform fee remains 0 for now; Stripe processing fees still apply.

## Stripe account setup

The GOAA Stripe Test account already has a dedicated webhook endpoint configured for:

- `checkout.session.completed`
- `transfer.created`
- `transfer.updated`
- `transfer.reversed`

Endpoint:

`https://api.goaa.ai/api/v1/order/webhook/stripe`

Do not create another duplicate webhook endpoint.

## Connected-account model

For a new marketplace integration, do not hard-code legacy Connect account `type` assumptions unless required for backward compatibility. Prefer Stripe's current recipient-account model for marketplace recipients, configured to receive transfers.

Before transferring funds, verify the connected professional is eligible to receive Stripe transfers.

## Security rules

- Stripe Test Mode only.
- Never use Live Mode during Stage B.
- Never put Stripe secrets in Git, frontend code, logs, test artifacts, or chat.
- `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` must be injected server-side only.
- Do not bypass approval/security wrappers.
- Do not merge `main`.
- Do not modify `golden/phase4-start-20260827`.

## Stage B blocker

DO currently needs secure server-side secret injection before real Stripe E2E can run.

Required server variables:

- `STRIPE_SECRET_KEY` (`sk_test_...`)
- `STRIPE_WEBHOOK_SECRET` (`whsec_...`)
- optional frontend publishable key if later needed (`pk_test_...`)

Do not ask Tao to paste secret values into normal chat. Use direct server-side secret injection or another secure secret-management path.

## Stage B real E2E acceptance

Run one brand-new order:

Customer need -> real $39.90 Stripe Test Checkout -> verified webhook -> connection paid -> match -> professional custom $500 estimate -> accept -> real $500 Stripe Test Checkout -> verified webhook -> paid -> start -> supplement -> Delivery Package -> customer confirm -> settlement_ready -> real Stripe Connect Transfer -> verified `transfer.created` -> settlement paid/transferred -> Invoice/PDF.

Also verify:

- duplicate checkout webhook idempotency
- duplicate transfer webhook idempotency
- other customer 403
- unassigned agent 403
- agent cannot settle
- Delivery Package immutability/version retention
- audit trail
- browser CORS from Vercel preview to `https://api.goaa.ai`
- Phase 3 regression remains green

Stop after Stage B Test Mode report. Do not enter Live Mode.
