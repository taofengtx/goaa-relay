# GOAA Phase 3 — Three-Role API Contract Freeze

This document is the frontend contract freeze for Customer / Agent / Admin integration with the DO Order Engine.

## Principle

All three roles operate on the same `service_order_id` and the same server-side order state. Frontend localStorage is fallback only and must not become a second source of truth.

Frontend stack:

`Customer / Agent / Admin UI -> OrderRuntimeBridge -> order-runtime.ts -> order-api.ts -> DO Order Engine -> PostgreSQL`

## Required environment

- `NEXT_PUBLIC_GOAA_ORDER_API_BASE`
- `NEXT_PUBLIC_GOAA_ALLOW_DEMO_FALLBACK=true` only during integration
- runtime tokens stored per role during test:
  - `goaa_order_customer_token`
  - `goaa_order_agent_token`
  - `goaa_order_admin_token`
- active order id:
  - URL `?order=<service_order_id>` preferred
  - fallback `goaa_active_order_id`

## Canonical frontend order stages

Frontend accepts:

- `estimate`
- `accepted`
- `paid`
- `processing`
- `waiting_customer`
- `delivered`
- `completed`

Backend may keep richer internal states. Backend DTO must map them consistently to these values.

Settlement values expected by frontend:

- `locked`
- `ready`
- `paid`

## Shared order reads

### GET `/orders/{order_id}`

Required response fields:

```json
{
  "id": "...",
  "serviceTitle": "...",
  "amount": 600,
  "stage": "processing",
  "settlement": "locked",
  "updatedAt": "ISO-8601"
}
```

### GET `/orders/{order_id}/events`

Returns ordered timeline events:

```json
[
  {
    "id": "...",
    "type": "payment_succeeded",
    "createdAt": "ISO-8601",
    "actorRole": "customer",
    "data": {}
  }
]
```

## Customer writes

### POST `/orders/{order_id}/estimate/accept`

Accept current estimate.

### POST `/orders/{order_id}/confirm`

Customer confirms delivered service. Backend must reject if no valid submitted delivery exists for file-delivery service types.

### POST `/orders/{order_id}/messages`

Body:

```json
{"content":"..."}
```

Role is inferred from auth token.

### PATCH `/orders/{order_id}/supplement/items/{item_id}`

Body:

```json
{"answer":"..."}
```

### POST `/orders/{order_id}/supplement/items/{item_id}/files`

Multipart field: `file`.

## Agent writes

### POST `/orders/{order_id}/start`

Start fulfillment after successful payment.

### POST `/orders/{order_id}/messages`

Same shared message endpoint. Role inferred from token.

### POST `/orders/{order_id}/supplement`

Body:

```json
{
  "items": [
    {"label":"最近两年 Tax Return","type":"pdf","required":true}
  ]
}
```

Supported supplement types:

- `text`
- `date`
- `amount`
- `choice`
- `image`
- `pdf`
- `file`

## Supplement read

### GET `/orders/{order_id}/supplement`

Expected shape:

```json
{
  "id": "...",
  "status": "collecting",
  "items": [
    {
      "id": "...",
      "label": "...",
      "type": "pdf",
      "required": true,
      "status": "pending",
      "answer": null,
      "files": []
    }
  ]
}
```

Request status:

- `draft`
- `collecting`
- `complete`

## Delivery Package

Delivery Package is separate from Supplement files.

### GET `/orders/{order_id}/delivery-package`

Returns current visible package, preferably latest submitted package. If current draft is returned to Agent, Customer must never see unsubmitted drafts.

### POST `/orders/{order_id}/delivery-package`

Body:

```json
{"note":"本次服务已完成，附件为最终文件及相关回执。"}
```

Response:

```json
{
  "id": "...",
  "orderId": "...",
  "version": 1,
  "status": "draft",
  "note": "...",
  "files": []
}
```

### POST `/orders/{order_id}/delivery-package/{package_id}/files`

Multipart fields:

- `file`
- `category`

Canonical categories:

- `final`
- `receipt`
- `policy_contract`
- `tax`
- `approval_notice`
- `report`
- `other`

### POST `/orders/{order_id}/delivery-package/{package_id}/submit`

Rules:

1. At least one file for service types requiring file delivery.
2. Submitted package becomes immutable.
3. Corrections create V2/V3; never overwrite submitted V1.
4. Submission can move order to `delivered` only through Order Engine validation.
5. Customer can see package only after submission.

### GET `/orders/{order_id}/delivery-package/{package_id}/download`

Authorized ZIP download of the submitted package.

## Messaging reads

### GET `/orders/{order_id}/messages`

Expected:

```json
[
  {
    "id":"...",
    "senderRole":"agent",
    "content":"...",
    "createdAt":"ISO-8601"
  }
]
```

## Admin reads

### GET `/admin/orders/{order_id}`

Returns admin-authorized order DTO.

### GET `/admin/orders/{order_id}/payments`

Returns payment events / records for this order.

### GET `/admin/orders/{order_id}/audit`

Returns admin-visible order and audit events.

## Admin writes

### POST `/admin/orders/{order_id}/actions`

Body:

```json
{
  "action": "flag",
  "reason": "..."
}
```

Supported Phase 3 actions:

- `flag`
- `unflag`
- `reassign`

All admin actions must write audit metadata. Admin UI must not directly mutate payment, settlement, or arbitrary order stage fields.

## Authorization rules

Customer:
- own orders only
- own supplement responses/files
- submitted delivery packages for own orders
- own order messages

Agent:
- assigned orders only
- can create supplement requests
- can create delivery package drafts
- cannot self-settle payouts

Admin:
- explicit admin authorization
- management actions audited
- sensitive resource access audited

## Settlement rule

Normal path:

`Customer Confirm -> settlement_ready -> Stripe Connect / system payout -> webhook -> settled`

Agent cannot directly set `settled`.

## File security

- Never expose raw server paths.
- Every individual file and ZIP download must authorize by role + order ownership/assignment.
- File access must not depend on frontend hiding links.
- Supplement uploads and Delivery Package files must remain logically separated.

## Three-role E2E acceptance test

Use one order, e.g. `GOAA-DEMO-ORDER-001`, amount `$600`.

1. Agent sees paid order.
2. Agent starts service.
3. Agent creates supplement request with text + image/PDF/file items.
4. Customer sees same request and submits answers/files.
5. Agent sees complete package.
6. Agent creates Delivery Package V1.
7. Agent uploads at least two files in different categories.
8. Agent submits package.
9. Customer sees delivery package and downloads a file + ZIP.
10. Customer confirms service complete.
11. Admin sees full timeline and settlement `ready`.
12. Admin can flag/unflag/reassign with audit trail.
13. Unauthorized Customer cannot access another order file or ZIP.
14. Assigned Agent cannot access another Agent's order.
15. Agent cannot set `settled` directly.

## Frontend routes for integration

- Customer: `/customer-order?order=<service_order_id>`
- Agent live: `/agent-order-live?order=<service_order_id>`
- Admin live: `/admin-order-live?order=<service_order_id>`

## Stop condition for backend work

After endpoint adaptation and E2E pass, stop and report:

- commit SHA
- deployed version
- migration changes if any
- final endpoint map
- DTO mapping differences
- auth test result
- file/ZIP permission test result
- three-role E2E result
- regression result
- known issues
- rollback procedure

Do not redesign frontend during this backend adaptation.