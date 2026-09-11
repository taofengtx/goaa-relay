# GOAA Agent Action Layer

> Golden protection: this layer is additive only. See `docs/golden-flow-protection.md`. It must not modify, replace, bypass, or fork the validated Golden business flow without Tao's explicit approval before the change.

## Purpose
The Agent Action Layer turns AI recommendations into bounded, reviewable actions without allowing either AI Agent to silently cross an interest, payment, professional, filing, completion, or Golden-flow boundary.

## Canonical loop
Observe → Understand → Detect → Decide → Recommend → Prepare → Propose → Human Authorizes → Execute through an already-approved canonical Order Engine action → Verify result → Track → Resolve.

## Interest boundary
- Customer AI Butler represents the customer.
- Professional AI Assistant represents the licensed professional.
- A proposal never transfers one side's authority to the other side.

## Golden boundary
The Golden business flow remains the source of business truth:

Customer consultation → useful AI planning → 30-Day Personal AI Agent Access ($39.90) → Connect / Match → licensed professional → professional estimate → customer accepts → professional service payment → service execution → supplement when needed → delivery → customer confirms completion.

The Agent layer may assist around this flow, but it may not introduce a parallel order/payment/matching/completion state machine. If an Agent feature requires changing a Golden contract, implementation stops until Tao explicitly approves that specific Golden change.

## Proposal lifecycle
`proposed → approved → executing → executed`

Execution failure is terminal for that proposal:
`executing → failed`

Cancellation is allowed before execution:
`proposed/approved → cancelled`

A failed proposal never retries silently. A retry is a new proposal linked with `retryOf` and requires a new explicit authorization.

## Current frontend proposal record
See `app/lib/agent-action-proposals.ts`.

Important fields:
- id
- orderId
- actionType
- authorizer
- scopeKey
- retryOf
- title / rationale
- willHappen / willNotHappen
- payloadPreview
- status
- createdAt / updatedAt / approvedAt / executedAt / failedAt / cancelledAt
- failureMessage

The current registry is localStorage only. It is a transparency layer, not the server audit source of truth.

## Capability boundary
See `app/lib/agent-action-capabilities.ts`.

Currently executable from the Agent layer after explicit authorization:
1. `send_message` → existing canonical Order Engine message API.
2. `request_information` → existing canonical Order Engine supplement API.

Currently NOT executable from the Agent layer:
1. `start_service` → remains a canonical professional workspace action with verified payment prerequisite.
2. `prepare_delivery` → AI may prepare only; professional controls real files and submission.
3. `connect_professional` → remains in the customer-controlled Connect Pass / matching journey.

The bounded executor in `app/lib/agent-action-executor.ts` rejects action types not explicitly enabled by this contract.

## Completion invariant
Matching is not completion.
Estimate is not authorization.
Estimate acceptance is not payment.
Payment is not completion.
Starting service is not completion.
Delivery is not completion.
Only the canonical customer-confirmed `completed` order state may close the Matter.

## Backend next step
Before production use across devices, the proposal lifecycle needs a server-side audit ledger. The backend design must preserve existing canonical business endpoints rather than introducing a generic arbitrary-action executor.

Desired backend properties:
- role-scoped proposal ownership and read visibility;
- immutable proposal identity and action type;
- validated state transitions;
- optimistic concurrency or version checks;
- idempotency for approve/execute recording;
- payload bounds and PII-safe logs;
- explicit correlation to canonical order events/actions;
- server record cannot claim `executed` unless supported by a real canonical business action/result;
- no payment, matching, filing, reassignment, professional advice, completion, or Golden-flow bypass.

Backend audit may be read-only. Production backend/database changes require separate explicit approval. A generic `continue` is not approval to alter Golden behavior.
