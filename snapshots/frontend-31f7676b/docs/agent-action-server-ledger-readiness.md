# Agent Action Server Ledger Readiness

Status: **DESIGN-READY · NOT IMPLEMENTED**

This document prepares the frontend contract for a future persistent Agent Action Proposal ledger. It does **not** authorize or implement any backend, database, production, Stripe, matching, settlement, invoice, handoff, or Golden Flow change.

## Frozen boundary

Golden Flow remains the canonical business process:

Consultation → Planning → $39.90 / 30-Day Personal AI Agent Access → Connect/Match → Professional Estimate → Customer Acceptance → Professional Service Payment → Service Execution → Supplement → Delivery → Customer-Confirmed Completion.

Agent Action Layer remains an overlay.

## Current frontend truth

Proposal lifecycle:

`proposed → approved → executing → executed`

Failure:

`executing → failed`

Pre-execution terminal states:

`proposed/approved → cancelled | superseded`

Retry creates a new proposal with `retryOf`; failed proposals never silently retry.

Only two bounded actions are currently executable from the Agent Layer:

- `send_message`
- `request_information`

Every execution must pass:

1. Golden boundary
2. Proposal integrity
3. Capability whitelist
4. Canonical state preflight
5. Existing canonical Order Engine endpoint
6. Local canonical execution receipt

## Future server ledger contract

The server ledger is an audit/authorization ledger, not a second Order Engine.

The client must never be allowed to claim `executed` by sending an arbitrary status update. Server-side `executed` must be tied to a successful canonical action result such as a real message ID or supplement ID.

The ledger must preserve customer/professional authorization isolation and optimistic concurrency. Terminal records remain immutable. A retry must be a new record.

## Migration principle

When a backend implementation is separately approved, migrate from local transparency records to server records without changing Golden Flow semantics or canonical business endpoints. The frontend may use local records as a compatibility cache, but server audit becomes authoritative for proposal lifecycle only; Order Engine remains authoritative for actual business state.

## Explicitly not approved by this document

- database migration
- new production table
- new production router
- service restart
- backend deployment
- modification of existing canonical endpoints
- payment behavior change
- matching behavior change
- estimate behavior change
- service start behavior change
- delivery behavior change
- completion behavior change

Any such implementation requires a separate explicit approval before execution.
