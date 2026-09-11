# Aika Phase 3 — Backend Alignment + Delivery Package + Three-role E2E

## Project manager decision
Phase 3 frontend contracts are now frozen. Do not redesign Customer / Agent / Admin UI. Your task is to align the existing DO Order Engine to the frontend contract, add the Delivery Package delta, deploy, and run full three-role E2E.

## Frontend source of truth
Repository: `taofengtx/goaa-ai-frontend`
Branch: `feature/agent-console-v1`

Read these files first:
- `docs/PHASE3_THREE_ROLE_API_CONTRACT.md`
- `docs/AIKA_PHASE3_DELIVERY_PACKAGE.md`
- `app/lib/order-api.ts`
- `app/lib/order-runtime.ts`

Live test pages already exist:
- `/customer-order?order=GOAA-DEMO-ORDER-001`
- `/agent-order-live?order=GOAA-DEMO-ORDER-001`
- `/admin-order-live?order=GOAA-DEMO-ORDER-001`

Do NOT modify these frontend pages during this task.

## Required work

### 1. API alignment
Make the DO backend expose or adapt to the frozen frontend contract. If your existing route names differ, add a compatibility adapter/router instead of rewriting stable domain logic.

Required functional groups:
- order detail
- events/timeline
- estimate accept
- service start
- messages
- supplement create/read/answer/file upload
- delivery package create/read/file upload/submit/ZIP download
- customer completion confirm
- admin order view/actions/payments/audit

### 2. Delivery Package
Implement durable final delivery packages.

Rules:
- separate from Supplement Package
- lifecycle: `draft -> submitted -> superseded`
- submitted package is immutable
- corrections create V2/V3; never overwrite V1
- package files store metadata: category, package_version, original_name, mime_type, size, storage_key, created_at
- categories: `final`, `receipt`, `policy_contract`, `tax`, `approval_notice`, `report`, `other`
- customer can download after service completion and after settlement
- assigned Agent can read/download its assigned order package
- Admin can inspect/download according to admin policy
- all upload/submit/download/version actions write order event / audit metadata
- provide authorized ZIP download for the entire submitted package

### 3. Delivery gate
For service types requiring file delivery, Agent cannot move order to `delivered` unless at least one file exists in a submitted Delivery Package.

Allow an explicit backend service-type exception only for `no_file_delivery=true`.

### 4. Security
Re-run strict authorization tests:
- another customer cannot read/download another customer's order files
- another Agent cannot access unassigned order files
- Customer cannot call Agent/Admin actions
- Agent cannot call Admin actions
- Agent cannot mark settlement as settled
- normal settlement remains system / Stripe Connect driven

### 5. Settlement
Keep the accepted rule:
`Customer confirm -> settlement_ready -> Stripe Connect/system event -> settled`

Agent may VIEW settlement. Agent must NOT directly mark `settled` in production logic.

### 6. E2E test order
Use:
`GOAA-DEMO-ORDER-001`
Amount: `$600`

Run this exact scenario:
1. Agent views assigned order.
2. Customer accepts estimate.
3. Mock/Test payment marks paid.
4. Agent starts service.
5. Agent creates supplement request with at least 3 fields, including one file field.
6. Customer answers text/date data and uploads one test PDF/image.
7. Agent confirms supplement complete.
8. Agent creates Delivery Package V1.
9. Agent uploads at least two final files in different categories.
10. Agent submits Delivery Package V1.
11. Customer sees package and downloads one file.
12. Customer downloads package ZIP.
13. Customer confirms service complete.
14. Admin sees completed order and settlement ready.
15. Customer and Agent can still download V1 after completion.
16. Agent creates V2 and submits it.
17. Verify V1 remains immutable and downloadable.
18. Verify unauthorized customer cannot access V1/V2 files or ZIP.

### 7. Deployment
- backup runtime and DB state before changes
- additive migration only
- do not alter existing unrelated tables
- restart service and verify health
- preserve existing Agent Console / chat / planning APIs
- run regression tests after deployment

## Environment/config expected by frontend
Provide the exact value needed for:
`NEXT_PUBLIC_GOAA_ORDER_API_BASE`

Also provide test tokens or a supported test-login flow for:
- Customer
- Agent
- Admin

Frontend runtime currently reads role-specific tokens from browser localStorage. If you want a safer short-lived test mechanism, document it, but do not redesign auth in this task.

## Stop condition
After backend alignment, deployment, and E2E, STOP.

Return one report containing:
- backend commit SHA/version
- migrations added
- API endpoint mapping table: frontend contract -> actual route
- service health
- `NEXT_PUBLIC_GOAA_ORDER_API_BASE`
- Customer / Agent / Admin test auth method
- GOAA-DEMO-ORDER-001 full event timeline
- Delivery Package V1 + V2 test result
- individual file download test
- ZIP download test
- authorization matrix result
- settlement_ready result
- regression test result
- known issues
- rollback procedure

Do not modify frontend and do not continue to Stripe Production.