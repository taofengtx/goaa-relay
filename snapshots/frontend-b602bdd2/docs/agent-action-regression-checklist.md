# Post-Golden Agent Action Regression Checklist

Purpose: validate Agent Layer changes without altering Golden Flow.

## Golden Flow protection

- Consultation unchanged
- Planning unchanged
- $39.90 / 30-Day Personal AI Agent Access unchanged
- Connect/Match unchanged
- Professional Estimate unchanged
- Customer Acceptance unchanged
- Professional Service Payment unchanged
- Service Start unchanged
- Supplement canonical workflow unchanged
- Delivery unchanged
- Customer-Confirmed Completion unchanged
- No Agent Layer path creates a second payment, matching, estimate, delivery, or completion state machine

## Proposal lifecycle

- proposed → approved allowed
- proposed → cancelled allowed
- proposed → superseded allowed
- approved → executing allowed
- approved → cancelled allowed
- approved → superseded allowed
- executing → executed allowed only after successful canonical action
- executing → failed allowed on canonical failure
- failed terminal
- executed terminal
- cancelled terminal
- superseded terminal
- failed retry creates a new proposal with retryOf

## Bounded action execution

### send_message
- requires explicit authorizer action
- requires canonical auth token
- requires Golden-safe capability
- requires integrity pass
- requires canonical order preflight
- refuses completed order
- refuses stale stage-scoped proposal
- executes through existing messages endpoint only
- stores canonical message receipt ID on success

### request_information
- professional authorizer only
- requires explicit authorization
- requires canonical auth token
- requires Golden-safe capability
- requires integrity pass
- requires canonical order/supplement preflight
- refuses unreadable supplement state
- refuses duplicate existing supplement
- refuses completed order
- executes through existing supplement endpoint only
- stores canonical supplement receipt ID on success

## Reconciliation

- receipt verification is read-only
- message receipt verification uses canonical messages list
- supplement receipt verification uses canonical supplement read
- missing receipt does not mutate Golden business state
- unavailable verification fails without fabricating truth
- local verification state is labeled local, not server audit truth

## Role isolation

- Customer Butler represents customer only
- Professional AI Assistant represents licensed professional only
- customer proposal history is filtered to customer authorizer
- professional proposal history is filtered to professional authorizer
- one role cannot infer the other role's authorization from silence

## Completion invariants

- Match != completion
- Payment != completion
- Service Start != completion
- Delivery != completion
- only canonical customer-confirmed completed state closes the Matter

## Production boundary

This checklist does not approve any backend migration, database change, Stripe change, matching change, production service restart, main merge, Golden branch modification, or deployment.
