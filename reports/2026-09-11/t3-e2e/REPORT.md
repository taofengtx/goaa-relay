# Round T3 — C2 end-to-end: apply → admin approve → agent portal → logout

**Date:** 2026-09-11
**Environment:** C2 test only — Next BFF `13102` (FE `d4ad5613`) → FastAPI `3103` (BE `dc64591b`) → PostgreSQL `goaa_c2test` (5433).
**Not touched:** C1 production, 3100/3101, `goaa_c2`, Golden Flow, payments, DNS, OAuth/SSO.
**Secrets:** none printed. No Clerk secret key, no business-token value, no DB password appears in this report. Business tokens appear only as counts / length.

Flow: 申請 → 管理員核准 → 經紀人入口 → 登出, end-to-end against the isolated C2 stack with synthetic data.

---

## 0. Outcome

| Step | Result |
|---|---|
| T0 — prerequisites + backup | ✅ |
| F1 — drop-in to open the private-files dir, restart 3103 | ✅ |
| T1 — applicant: login → apply → upload → submit → pre-review | ✅ |
| T2 — admin: create → grant role → queue → approve | ✅ |
| T3 — agent portal + customer↔agent toggle | ✅ |
| T4 — logout → revoke → old token rejected | ✅ |

---

## 1. T0 — prerequisites & backup

**Expected:** FE `d4ad5613` deployed on 13102; BE `dc64591b` deployed on 3103; relay clean; a full `pg_dump` of `goaa_c2test` taken before any write.
**Actual:**
- FE HEAD `d4ad5613` ✅ (deployed), BE HEAD `dc64591b` ✅ (deployed), relay pulled clean ✅.
- Backup: `PGPASSFILE=/opt/goaa-test/env/migrate.pgpass pg_dump -h 127.0.0.1 -p 5433 -U goaa_c2_migrate --no-owner --no-privileges -f /tmp/goaa-c2test-t3-pre-20260911-011512.sql -d goaa_c2test` rc=0 — **83772 bytes**, sha256 `5b4c48a61f3aeaa58de7464fa05f67c38b35aa547e97cd5e724de3e5fde6a2dc`.

---

## 2. F1 — private-files directory write fix

**Expected:** the document-storage dir must be writable inside the service sandbox, otherwise uploads fail.

**Root cause (actual).** `goaa-c2-clerk-api-3103.service` runs with `ProtectSystem=strict`; `ReadWritePaths=/opt/goaa-test/private-files /opt/goaa-test/log`, but env `GOAA_C2_PRIVATE_FILES_DIR=/opt/goaa-test/private-files-c2test` points at a dir **not** in that list → upload →
`OSError: [Errno 30] Read-only file system: '/opt/goaa-test/private-files-c2test'` (`POST /documents → 500`).

**Fix — drop-in only; the original unit file is NOT modified.**
- File: `/etc/systemd/system/goaa-c2-clerk-api-3103.service.d/20-c2test-private-files.conf`

  ```
  [Service]
  ReadWritePaths=/opt/goaa-test/private-files-c2test
  ```

  **sha256** `c38ce2b9481d677fd90ae37c1c11b67b1e912e2ae72193b3463588905b011cdc`
- `systemctl daemon-reload` rc=0; `systemctl cat` shows the drop-in merged and the original unit content unchanged.
- Effective `ReadWritePaths`: `/opt/goaa-test/private-files /opt/goaa-test/log /opt/goaa-test/private-files-c2test`.
- `systemctl restart goaa-c2-clerk-api-3103.service` rc=0, new **MainPID 2009756**, active.

**Restart / approval note.** On Aika's side **no 🛡 approval card appeared** — the restart was submitted directly and ran immediately. **Whether that restart was in fact approved by Tao is Tao's record to state, not Aika's.**

**Post-restart verification (actual):** 3103 health HTTP 200 / `reachable=true` / `database.name=goaa_c2test`; 13102 BFF health 200; `ReadWritePaths` contains both paths.

**Rollback (documented, not executed):** delete the drop-in → `systemctl daemon-reload` → restart `goaa-c2-clerk-api-3103.service`.

---

## 3. T1 — applicant end-to-end

Account `c2e2e+clerk_test@example.com` (Clerk test email, OTP `424242`). Turnstile did not appear; nothing bypassed. Applicant `users.id` = `a429f075-b6d1-4edd-82cf-7e95cc8d65d5`.

| # | Expected | Actual |
|---|---|---|
| T1.1 | login via `/client-login?next=%2Fagent-loop%2Fcustomer` | Clerk card, email OTP, session active ✅ |
| T1.2 | customer → Become an Agent → `/agent-loop/apply` | page rendered ✅ |
| T1.3 | synthetic licence PNG uploads | **`POST /api/v1/agent-loop/documents → 201 Created`**; landed in `/opt/goaa-test/private-files-c2test` = **1 file / 38342 bytes** (count+bytes only; contents not read) ✅ |
| T1.4 | submit | **`POST /api/v1/agent-loop/applications/me/submit → 200 OK`**; status `Submitted — waiting for review` ✅ |
| pre-review | advisory only, no auto-approve | ENGINE `goaa-c2-rules-v1 · rules-only`, RECOMMENDATION `looks_complete`, **CAN AUTO-APPROVE `false`**, labelled "advisory only — never a decision" ✅ |

**Negative gates (before approval).** Expected: agent/admin panels refuse. Actual: `/agent-loop/agent` → **`agent_role_required`**; `/agent-loop/admin` → **`admin_required`** (no applicant data sent to the browser).

Screenshots: `t1-form.jpg`, `t1-submitted.jpg`, `t1-prereview.jpg`.

---

## 4. T2 — administrator review

| # | Expected | Actual |
|---|---|---|
| T2.1 | login `c2admin+clerk_test@example.com` (account created) | Clerk user created; local `users` row `923f64ad-4bf6-44ca-9639-49c82f000825` ✅ |
| T2.2 | grant admin via operator tool | `migrate` role: `python -m tools.grant_role --email c2admin+clerk_test@example.com --role admin --confirm` → rc=0, roles `['admin','user']` ✅ |
| T2.3 | `/agent-loop/admin` queue shows the T1 application | visible (Test Applicant / submitted / updated 2026/9/11 02:02:12); contact masked ✅ |
| T2.4 | detail: docs, pre-review, audit | document row `front / image/png / c2-local-private / stub`; pre-review `CAN AUTO-APPROVE false`; append-only history #87..#95, actor `user` ✅ |
| T2.5 | approve | **`POST /api/v1/agent-loop/admin/applications/59e17a01-.../approve → 200 OK`**; audit **#97 `application.approve / admin / 2026/9/11 02:10:01`** ✅ |
| T2.6 | agent role granted | DB: applicant `a429f075…` roles `agent` (granted 09:10:01Z) + `user`; application `59e17a01…` = `approved` ✅ |

Panel states "History is written by the server only. There is no edit or delete control here." Decision buttons: Approve / Request more information / Reject / Suspend / Re-run pre-review.

Screenshots: `t2-queue.jpg`, `t2-review.jpg`.

---

## 5. T3 — agent portal and customer↔agent toggle

| # | Expected | Actual |
|---|---|---|
| T3.2 | `/agent-loop/customer` status = Approved; left rail bottom has "Switch to Agent Portal" | status **`Approved — agent licence active`**; rail bottom **`⇄ Switch to Agent Portal`** ✅ |
| T3.3 | `/agent-loop/agent`: brand `AI Agent`; rail Overview/Opportunities/Service Orders/Knowledge Base/My AI; no gate | brand **`AI Agent`**; rail = Overview / Opportunities / Service Orders / Knowledge Base / My AI / ⇄ Back to Customer; **no gate** ✅ |
| T3.4 | toggle both ways | `⇄ Back to Customer` → `/agent-loop/customer` (brand `AI Butler`, Approved); `⇄ Switch to Agent Portal` → `/agent-loop/agent` (brand `AI Agent`) ✅ |
| T3.6 | applicant roles = user + agent, no admin | DB: **`agent,user`** ✅ |

Agent panel body: `licence active`; ACCOUNT ID `a429f075…`; APPLICATION `59e17a01…`; LICENCE GRANTED `2026/9/11 02:10:01`; ROLES `agent, user`; "same account / same session — you did not sign in twice and there is no second credential."

Screenshots: `t3-customer-approved.jpg`, `t3-agent-portal.jpg`.

---

## 6. T4 — logout lifecycle and old token

Token values were handled only inside shell variables on the C2 host; nothing below prints a token value.

**Expected:** logout via the real UI control revokes the business token; the client clears its credential; a revoked token is rejected server-side.

**Actual:**

| # | Check | Actual |
|---|---|---|
| T4.1 | via `business_subject_links`: `users.id` → subject id → `business_tokens` | applicant `a429f075…` → subject `4717531f-6806-49ef-8326-6185f3ea1d3d`; **total 3 / live 1** (before logout) |
| T4.2 | MY ACCOUNT → LOG OUT | landing URL **`/client-login?next=/agent-loop/customer`**; **no error message**; `client_token` **absent**; golden sessionStorage **absent**; backend **`POST /api/v1/agent-loop/golden/session/revoke → 200 OK`** |
| T4.3 | live count after logout = 0 | **total 3 / live 0** ✅ |
| T4.4 | revoked token rejected | `GET /golden/session/verify` with the revoked bearer → **HTTP 401**, error code **`invalid_business_token`** ("business token is not usable: revoked") ✅ |
| T4.5 | admin `c2admin` check | subject `31883e94-122c-4c3b-8a9d-868a99752db3`; **total 1 / live 0** (already revoked on its earlier logout) ✅ |

Screenshot: `t4-logout-menu.jpg`.

**Minor observation (recorded, not changed):** after a signed-out gated-page hit, the login entry redirects with `next=/agent-loop/customer` (the default), not the originally requested path.

---

## 7. Corrections applied

1. **`business_tokens.user_id` is the business-subject id, not `users.id`.** Correct path: `users.id → business_subject_links.subject_id → business_tokens.user_id`. Schema confirmed: `business_subject_links(user_id, subject_id, linked_via, issuer, subject, created_at)`; `business_tokens(id, user_id, token, role, created_at, issued_at, last_used_at, revoked_at)`. Mapping used: applicant `a429f075…` → subject `4717531f…`; admin `923f64ad…` → subject `31883e94…`. **The earlier statement "the applicant has no business token" is withdrawn** — the applicant did have tokens; they were simply not visible under a `users.id` join.
2. **New-account registration does not honour `next`; it lands on `/`.** Reproduced with both new accounts (`c2e2e…`, `c2admin…`) on their first (registration-branch) login. Existing accounts honour the target. With zero legacy users, **every user goes through this path → pre-launch must-fix**. Not changed this round.

---

## 8. Test technique note (not a product issue)

The browser tool's file chooser did not bind to the page's **hidden** `<input type=file>` (`style="display:none"`), so the upload was performed by fetching the synthetic PNG from a **local CORS static server** (`t3-httpserv`, `127.0.0.1:8099`, `Access-Control-Allow-Origin: *`) and injecting it via `DataTransfer` into the input, then dispatching `change`. This is a **test-harness technique only** — not a product defect. **`t3-httpserv` has been stopped**; port 8099 is no longer listening.

---

## 9. Findings / open items

- **F1** fixed the document-storage blocker (§2). Underlying mismatch: env `GOAA_C2_PRIVATE_FILES_DIR` vs unit `ReadWritePaths` disagreed; bridged by an additive drop-in rather than by aligning env+unit. Long-term, align the two.
- **§7.2** new-account `next` not honoured — pre-launch must-fix.
- **§6** signed-out redirect uses the default `next=/agent-loop/customer`.
- Token inspection requires the two-hop join (§7.1).

---

## 10. Screenshots

`t1-form.jpg`, `t1-submitted.jpg`, `t1-prereview.jpg`, `t2-queue.jpg`, `t2-review.jpg`, `t3-customer-approved.jpg`, `t3-agent-portal.jpg`, `t4-logout-menu.jpg` (all in this directory).
