# C1 business back-end — excerpt (read-only, no connection to C1)

**Provenance (S4):** Every excerpt below was cut from the local *golden archive* clone
`/home/aika/Projects/goaa-ai-main` at HEAD **`02a17ffef4544adb00b92ce630616a69846b8ee2`**
("archive C1 runtime source baseline (2026-09-02)").

**Not verified this round:** whether the C1 production tree at `/opt/goaa/runtime`
is byte-identical to this archive. Round C1.5 did **not** connect
to C1; no C1 host was contacted, and no C1 service was read, restarted or modified.
Line numbers are those of the archive clone. Excerpts are verbatim; nothing was paraphrased.

---

## 1. `runtime/order_db.py` — the three order-token functions

File: `runtime/order_db.py` (1040 lines).

- `issue_order_token` — lines 36–45
- `authenticate_order_token` — lines 48–58
- `revoke_order_tokens` — lines 61–65

```python
  35| # ── auth (order domain) ─────────────────────────────────────────
  36| def issue_order_token(user_id: str, role: str) -> str:
  37|     token = new_id().replace("-", "")
  38|     with connect() as conn:
  39|         with conn.cursor() as cur:
  40|             cur.execute(
  41|                 "INSERT INTO goaa_order_tokens (user_id, token, role) VALUES (%s,%s,%s) "
  42|                 "ON CONFLICT (user_id, token) DO NOTHING",
  43|                 (user_id, token, role))
  44|         conn.commit()
  45|     return token
  46| 
  47| 
  48| def authenticate_order_token(token: str):
  49|     """Return dict {user_id, role} or None."""
  50|     if not token:
  51|         return None
  52|     with connect() as conn:
  53|         with conn.cursor() as cur:
  54|             cur.execute(
  55|                 "SELECT user_id, role FROM goaa_order_tokens "
  56|                 "WHERE token=%s AND revoked_at IS NULL", (token,))
  57|             row = cur.fetchone()
  58|     return dict(row) if row else None
  59| 
  60| 
  61| def revoke_order_tokens(user_id: str):
  62|     with connect() as conn:
  63|         with conn.cursor() as cur:
  64|             cur.execute("UPDATE goaa_order_tokens SET revoked_at=now() WHERE user_id=%s", (user_id,))
  65|         conn.commit()
```

## 2. `runtime/orders.py` — `require_auth` (the Bearer verification entry point)

File: `runtime/orders.py` (1974 lines). Function at lines 46–57;
shown here with 5 lines of context above and below (lines 41–62).

```python
  41| GOAA_CUSTOMER_CONSOLE_URL = os.getenv(
  42|     "GOAA_CUSTOMER_CONSOLE_URL",
  43|     GOAA_FRONTEND_URL + "/customer-order-live").rstrip("/")
  44| 
  45| # ── auth helpers ────────────────────────────────────────────────
  46| def require_auth(authorization: str = Header(default="")):
  47|     token = authorization.replace("Bearer ", "").strip()
  48|     auth = order_db.authenticate_order_token(token)
  49|     if auth:
  50|         return auth
  51|     # Agent Console 登录走 /api/v1/agent/login（main.py），签发 goaa_agent_tokens
  52|     # 的合法 agent token（agent_api 同款验证）。允许该 token 访问 order/agents 端点，
  53|     # 实现单一 bearer token 契约：Agent 登录后无需第二套 order token。
  54|     agent_id = agent_db.get_agent_id_by_token(token)
  55|     if agent_id:
  56|         return {"user_id": agent_id, "role": "agent"}
  57|     raise HTTPException(status_code=401, detail="invalid or expired token")
  58| 
  59| 
  60| def require_role(auth: dict, *roles):
  61|     if auth["role"] not in roles:
  62|         raise HTTPException(status_code=403, detail=f"requires role {'/'.join(roles)}")
```

## 3. `runtime/migrations/0006_order_schema.sql` — `goaa_order_tokens` DDL

File: `runtime/migrations/0006_order_schema.sql` (243 lines).
`CREATE TABLE` at line 24; block lines 23–31.

The table carries its key as an inline `PRIMARY KEY (user_id, token)`; the file declares
**no separate `CREATE INDEX` for `goaa_order_tokens`** (the 13 `CREATE INDEX` statements
at lines 221–233 all target other `goaa_order_*` tables).

```sql
  23| -- Order-domain session tokens (same pattern as goaa_agent_tokens; V1.1 expiry later)
  24| CREATE TABLE IF NOT EXISTS goaa_order_tokens (
  25|     user_id    TEXT NOT NULL,
  26|     token      TEXT NOT NULL,
  27|     role       TEXT NOT NULL,
  28|     created_at TIMESTAMPTZ DEFAULT now(),
  29|     revoked_at TIMESTAMPTZ,
  30|     PRIMARY KEY (user_id, token)
  31| );
```

## 4. Routes in `runtime/orders.py` that depend on `require_auth`

Method / path / line only — no code, per the request. There are **62** such routes.
`line` is the decorator line; `def` is the handler definition line.

Paths are the decorator paths. The router is declared at orders.py line 26 as
`APIRouter(prefix="/api/v1/order")` and mounted at main.py line 110, so each full path is
`/api/v1/order` + the path shown.

| # | method | path | router | line | def | handler |
|---|--------|------|--------|------|-----|---------|
| 1 | POST | `/auth/logout` | router | 263 | 264 | `logout` |
| 2 | POST | `/opportunities` | router | 270 | 271 | `create_opportunity` |
| 3 | GET | `/opportunities` | router | 278 | 279 | `list_opportunities` |
| 4 | POST | `/opportunities/{oid}/match` | router | 284 | 285 | `match_opportunity` |
| 5 | POST | `/orders` | router | 297 | 299 | `create_order` |
| 6 | GET | `/orders` | router | 326 | 327 | `list_orders` |
| 7 | GET | `/orders/{order_id}` | router | 334 | 335 | `get_order` |
| 8 | POST | `/orders/{order_id}/handoff-context` | router | 346 | 348 | `save_handoff_context` |
| 9 | POST | `/orders/{order_id}/estimates` | router | 369 | 370 | `create_estimate` |
| 10 | POST | `/orders/{order_id}/estimates/{eid}/send` | router | 396 | 397 | `send_estimate` |
| 11 | POST | `/orders/{order_id}/estimates/{eid}/accept` | router | 412 | 413 | `accept_estimate` |
| 12 | POST | `/orders/{order_id}/estimates/{eid}/reject` | router | 435 | 436 | `reject_estimate` |
| 13 | POST | `/orders/{order_id}/payments` | router | 452 | 453 | `create_payment` |
| 14 | POST | `/payments/{pid}/confirm` | router | 472 | 473 | `confirm_payment` |
| 15 | POST | `/orders/{order_id}/start` | router | 493 | 494 | `start_service` |
| 16 | POST | `/orders/{order_id}/cancel` | router | 504 | 505 | `cancel_order` |
| 17 | POST | `/orders/{order_id}/supplements` | router | 521 | 522 | `create_supplement` |
| 18 | POST | `/supplements/{rid}/items/{iid}/answer` | router | 541 | 542 | `answer_item` |
| 19 | POST | `/orders/{order_id}/supplements/complete` | router | 563 | 564 | `complete_supplements` |
| 20 | POST | `/orders/{order_id}/deliveries` | router | 581 | 582 | `submit_delivery` |
| 21 | POST | `/deliveries/{did}/accept` | router | 596 | 597 | `accept_delivery` |
| 22 | POST | `/deliveries/{did}/reject` | router | 624 | 625 | `reject_delivery` |
| 23 | POST | `/orders/{order_id}/messages` | router | 647 | 648 | `post_message` |
| 24 | GET | `/orders/{order_id}/messages` | router | 662 | 663 | `get_messages` |
| 25 | POST | `/orders/{order_id}/files` | router | 675 | 677 | `get_messages` |
| 26 | GET | `/files/{fid}/download` | router | 693 | 694 | `download_file` |
| 27 | GET | `/admin/dashboard` | router | 713 | 714 | `admin_dashboard` |
| 28 | GET | `/admin/orders` | router | 719 | 720 | `admin_list_orders` |
| 29 | POST | `/admin/orders/{order_id}/reassign` | router | 726 | 727 | `admin_reassign` |
| 30 | POST | `/admin/orders/{order_id}/refund` | router | 746 | 747 | `admin_refund` |
| 31 | POST | `/admin/orders/{order_id}/refunded` | router | 758 | 759 | `admin_refunded` |
| 32 | GET | `/admin/settlements` | router | 768 | 769 | `admin_settlements` |
| 33 | POST | `/admin/settlements/{sid}/settle` | router | 774 | 775 | `admin_settle` |
| 34 | POST | `/orders/{order_id}/settlement` | router | 855 | 856 | `create_settlement` |
| 35 | GET | `/agents/me` | router | 900 | 901 | `agent_me` |
| 36 | GET | `/agents/me/connect-account` | router | 946 | 947 | `agent_connect_account` |
| 37 | POST | `/agents/me/connect-account/link` | router | 954 | 956 | `agent_connect_account_link` |
| 38 | POST | `/agents/me/connect-account/verify` | router | 988 | 989 | `agent_connect_account_verify` |
| 39 | GET | `/orders/{order_id}/events` | router | 1212 | 1213 | `get_order_events` |
| 40 | POST | `/orders/{order_id}/estimate/accept` | router | 1225 | 1226 | `contract_accept_estimate` |
| 41 | POST | `/orders/{order_id}/confirm` | router | 1250 | 1251 | `contract_confirm` |
| 42 | GET | `/orders/{order_id}/supplement` | router | 1308 | 1309 | `get_supplement` |
| 43 | POST | `/orders/{order_id}/supplement` | router | 1320 | 1321 | `create_supplement_adapter` |
| 44 | PATCH | `/orders/{order_id}/supplement/items/{item_id}` | router | 1341 | 1343 | `answer_supplement_item_adapter` |
| 45 | POST | `/orders/{order_id}/supplement/items/{item_id}/files` | router | 1367 | 1370 | `answer_supplement_item_adapter` |
| 46 | GET | `/orders/{order_id}/delivery-package` | router | 1409 | 1410 | `get_delivery_package` |
| 47 | POST | `/orders/{order_id}/delivery-package` | router | 1422 | 1423 | `create_delivery_package` |
| 48 | POST | `/orders/{order_id}/delivery-package/{pid}/files` | router | 1434 | 1436 | `create_delivery_package` |
| 49 | POST | `/orders/{order_id}/delivery-package/{pid}/submit` | router | 1458 | 1459 | `submit_delivery_package` |
| 50 | GET | `/orders/{order_id}/delivery-package/{pid}/files/{fid}/download` | router | 1489 | 1490 | `download_delivery_file` |
| 51 | GET | `/orders/{order_id}/delivery-package/{pid}/download` | router | 1513 | 1514 | `download_delivery_zip` |
| 52 | GET | `/admin/orders/{order_id}` | router | 1540 | 1541 | `admin_get_order` |
| 53 | POST | `/admin/orders/{order_id}/actions` | router | 1549 | 1550 | `admin_order_action` |
| 54 | GET | `/admin/orders/{order_id}/payments` | router | 1577 | 1578 | `admin_order_payments` |
| 55 | GET | `/admin/orders/{order_id}/audit` | router | 1586 | 1587 | `admin_order_audit` |
| 56 | POST | `/orders/{order_id}/connect/checkout` | router | 1618 | 1619 | `connect_checkout` |
| 57 | POST | `/orders/{order_id}/match` | router | 1651 | 1652 | `request_match` |
| 58 | POST | `/orders/{order_id}/estimate` | router | 1679 | 1681 | `agent_estimate_contract` |
| 59 | POST | `/orders/{order_id}/payments/service/checkout` | router | 1715 | 1716 | `service_checkout` |
| 60 | POST | `/orders/{order_id}/invoice` | router | 1891 | 1892 | `generate_invoice` |
| 61 | GET | `/orders/{order_id}/invoice` | router | 1935 | 1936 | `get_invoice` |
| 62 | GET | `/orders/{order_id}/invoice/pdf` | router | 1945 | 1946 | `invoice_pdf_download` |

---

Cut by Aika, 2026-09-11, round C1.5 (S3). Read-only work: the archive clone was read;
nothing was executed and no C1 or C2 service was touched.

