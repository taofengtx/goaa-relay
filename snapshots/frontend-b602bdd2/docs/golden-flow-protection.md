# GOAA Golden Flow Protection Boundary

Status: **FROZEN BASELINE**

This document is a development guardrail. It does not modify runtime behavior.

## Golden business flow

The validated GOAA business journey remains:

**Customer consultation → useful AI planning → 30-Day Personal AI Agent Access ($39.90) → Connect / Match → licensed professional → professional estimate → customer accepts → professional service payment → service execution → information supplement when needed → delivery package → customer confirms completion.**

## Non-negotiable rule

No development phase may modify, replace, bypass, reinterpret, or silently fork the validated Golden business flow without Tao's explicit approval **before the change is made**.

Protected areas include, but are not limited to:

- Golden branches and Golden proof artifacts
- canonical Connect Pass / $39.90 access journey
- Order creation and ownership
- professional matching and role isolation
- estimate creation / acceptance
- professional service payment
- Stripe checkout / webhook truth
- service start
- supplement workflow
- delivery package workflow
- customer completion confirmation
- settlement and invoice behavior
- auth and production route guards

## Allowed post-Golden work

Post-Golden Agent work may add an intelligence / coordination layer **above** the canonical flow, for example:

- Customer AI Butler status interpretation
- Professional AI Assistant work preparation
- blocker / delay / escalation detection
- read-only canonical activity observation
- Action Proposal preparation
- explicit, narrowly scoped authorization UX
- transparent action history

Such work must reuse canonical business APIs where appropriate and must not create a second business state machine.

## Agent-layer invariant

**Agent intelligence may observe, explain, prepare, recommend, and—only after the correct explicit authorization—invoke an already-approved canonical action. It may not redefine the Golden workflow.**

The Agent layer must not infer business truth that the canonical backend has not established.

Examples:

- Match != completion
- Estimate != authorization
- Estimate acceptance != payment
- Payment != completion
- Delivery != completion
- Only canonical customer-confirmed completion closes the service Matter

## Change-control rule

If a proposed feature requires a change to a protected Golden area:

1. Stop implementation at the boundary.
2. Describe exactly which Golden behavior/file/API/state would change.
3. Explain why the change is necessary and what safer alternatives were considered.
4. Describe regression risk and rollback plan.
5. Obtain Tao's explicit approval.
6. Only then implement the approved scope.

Silence, a generic "continue", or approval of unrelated Agent-layer work is **not** approval to modify Golden behavior.

## Backend / Aika rule

Backend audits may inspect Golden behavior read-only. Any production code change, database migration, restart, Stripe/payment change, or modification to a protected Golden contract requires explicit approval for that specific change.

Do not bypass or disable approval/security wrappers.
