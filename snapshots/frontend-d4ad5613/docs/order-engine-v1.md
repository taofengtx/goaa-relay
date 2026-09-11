# GOAA Order Engine V1

## Product boundary

GOAA separates a lead/opportunity from a paid service order.

1. A customer creates a professional-service need.
2. GOAA matches the opportunity to an eligible Agent.
3. The Agent may accept priority follow-up or release it for rematching.
4. Customer and Agent communicate through GOAA AI relay; direct contact details are not shown in the Agent workspace.
5. The Agent sends an Estimate.
6. The customer accepts the Estimate.
7. The customer pays through Stripe.
8. Only after successful payment does the opportunity become an active Service Order.
9. The Agent performs the work, requests documents, updates status, and submits delivery.
10. The customer confirms completion.
11. Completion unlocks settlement eligibility.
12. Stripe Connect handles the Agent payout flow.

## Commercial rules for V1

- Agent Pro subscription: $99/month.
- GOAA order commission: 0% for V1.
- Stripe processing costs are handled according to the eventual Connect configuration.
- Customer payment must not be released to the Agent before service completion.
- Direct customer phone/email are not displayed in the Agent workspace.
- GOAA keeps order, payment, message, file, delivery, and settlement audit state.

## Opportunity states

- matched
- priority_followup
- released
- rematched
- expired
- converted

A released or expired opportunity remains visible in the Agent's historical order pool so the Agent can see actual monthly order frequency.

## Service Order states

- estimate_draft
- estimate_sent
- estimate_accepted
- payment_pending
- paid
- processing
- waiting_customer
- delivered
- completed
- settlement_ready
- settled

## Estimate

An Estimate contains:

- service title
- scope of work
- amount
- currency
- created/sent timestamps
- customer acceptance timestamp

Estimate acceptance is not payment. Payment success is the gate that starts fulfillment.

## AI relay

Customer -> Customer AI -> GOAA -> Agent AI -> Agent

Agent -> Agent AI -> GOAA -> Customer AI -> Customer

Messages are bound to the order. GOAA should preserve an audit trail while not exposing direct customer contact information in the Agent UI.

## Payments and settlement

Target architecture: Stripe Connect.

- Customer pays through Stripe.
- GOAA records payment state from Stripe webhooks.
- Agent fulfillment starts after confirmed payment.
- Customer completion confirmation changes settlement eligibility.
- GOAA triggers/authorizes the Connect settlement flow only when the order is eligible.
- Refund, dispute, cancellation, and timeout policies must be defined before production money movement is enabled.

## Frontend prototype

Current dual-role prototype routes:

- `/order-demo`
- `/customer-order`
- `/agent-order-demo`

The prototype uses browser storage only and must never be treated as production order truth.

## Backend handoff gate

Do not implement production Order Engine until the dual-role UX is approved. Once approved, backend work should replace browser demo state with authenticated APIs, database state, Stripe Connect onboarding/payment/webhooks, AI relay persistence, file storage, and auditable state transitions.
