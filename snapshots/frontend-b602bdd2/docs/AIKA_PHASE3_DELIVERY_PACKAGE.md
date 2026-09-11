# Aika Phase 3 Delta — Delivery Package

Scope is intentionally small. Do not redesign the existing Order Engine or frontend.

## Goal
Add a durable final Delivery Package to each service order. Customer and assigned Agent can access it after delivery and after order completion. Admin can inspect it. Supplement files remain separate.

## Required backend changes

1. Associate final delivery files with a delivery package/version.
2. Package lifecycle: `draft -> submitted -> superseded`.
3. A submitted package is immutable. Corrections create V2/V3; do not overwrite V1.
4. Add file metadata: category, package_version, original_name, mime_type, size, storage_key, created_at.
5. Categories: `final`, `receipt`, `policy_contract`, `tax`, `approval_notice`, `report`, `other`.
6. Add authorized ZIP download endpoint for all files in one submitted package.
7. Customer can read/download only packages belonging to their own order.
8. Assigned Agent can create/read/download packages for their assigned order.
9. Admin can inspect/download according to admin permission policy.
10. Every create/upload/submit/download/version event must write `order_events` / audit metadata.
11. Delivery package must remain available after customer confirms completion and after settlement.
12. Never mix Supplement Package files with Delivery Package files.

## API contract expected by frontend

- `GET /orders/{order_id}/delivery-package`
- `POST /orders/{order_id}/delivery-package`
- `POST /orders/{order_id}/delivery-package/{package_id}/files` multipart: `file`, `category`
- `POST /orders/{order_id}/delivery-package/{package_id}/submit`
- `GET /orders/{order_id}/delivery-package/{package_id}/download` -> authorized ZIP

If current backend route conventions differ, preserve existing conventions but provide an adapter-compatible mapping.

## State rule
Agent cannot move the service order to `delivered` unless at least one final delivery file exists in a submitted package (unless the service type is explicitly configured as no-file-delivery).

Customer confirmation occurs only after the submitted package is visible to the customer.

## E2E acceptance
Use `GOAA-DEMO-ORDER-001`:

Agent creates Delivery Package V1 -> uploads at least 2 test files in different categories -> submits -> Customer lists files -> Customer downloads one file -> Customer downloads ZIP -> Customer confirms service -> package remains downloadable -> Agent creates V2 to prove V1 is preserved.

Verify unauthorized customer cannot access either individual delivery files or ZIP.

## Stop condition
After backend implementation + tests, stop and report: commit SHA, migration, endpoints, E2E result, permission tests, rollback. Do not modify Customer/Agent/Admin frontend.