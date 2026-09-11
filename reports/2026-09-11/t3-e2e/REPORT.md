# Round T3 — C2 end-to-end: apply → admin approve → agent portal → logout

**Date:** 2026-09-11
**Environment:** C2 test only — Next BFF `13102` (FE `d4ad5613`) → FastAPI `3103` (BE `dc64591b`) → PostgreSQL `goaa_c2test` (5433).
**Not touched:** C1 production, 3100/3101, `goaa_c2`, Golden Flow, payments, DNS, OAuth/SSO.
**Secrets:** none printed. No Clerk secret key, no business-token value, no DB password appears in this report. Business tokens are shown only as counts / length.

Round T3 = 申請 → 管理員核准 → 經紀人入口 → 登出, run end-to-end against the isolated C2 stack with synthetic data.

---

## 0. Outcome summary

| Step | Result |
|---|---|
| F1 — drop-in to open the private-files dir, restart 3103 | ✅ |
| T1 — applicant: login → apply → upload → submit → pre-review | ✅ |
| T1.5 — negative gates (agent / admin) | ✅ |
| T2 — admin: create → grant role → queue → approve | ✅ |
| T3 — agent portal unlocked | ✅ |
| T4 — logout → revoke → old token rejected | ✅ |

Two corrections from Tao are applied below (see §7). One product finding is recorded (see §8).

---

## 1. F1 — private-files directory write fix (C2 host)

**Root cause.** `goaa-c2-clerk-api-3103.service` runs with `ProtectSystem=strict`; `ReadWritePaths=/opt/goaa-test/private-files /opt/goaa-test/log`, but the env var `GOAA_C2_PRIVATE_FILES_DIR=/opt/goaa-test/private-files-c2test` points at a directory **not** in that list → any document upload failed with
`OSError: [Errno 30] Read-only file system: '/opt/goaa-test/private-files-c2test'` (`POST /documents → 500`).

**Fix (drop-in only; original unit file untouched).**
- New file: `/etc/systemd/system/goaa-c2-clerk-api-3103.service.d/20-c2test-private-files.conf`
  ```
  [Service]
  ReadWritePaths=/opt/goaa-test/private-files-c2test
  ```
  sha256 `c38ce2b9481d677fd90ae37c1c11b67b1e912e2ae72193b3463588905b011cdc`.
- `systemctl daemon-reload` rc=0; `systemctl cat` confirms the drop-in is merged and **the original unit content is unchanged**.
- Effective `ReadWritePaths` after reload:
  `/opt/goaa-test/private-files /opt/goaa-test/log /opt/goaa-test/private-files-c2test`.
- `systemctl restart goaa-c2-clerk-api-3103.service` rc=0, new **MainPID 2009756**, active.

**Approval note.** On Aika's side **no 🛡 approval card appeared** — the restart command was submitted directly and ran immediately; **whether this restart was in fact approved by Tao is Tao's record to state, not Aika's**.

**Post-restart verification.**
- 3103 health: HTTP 200, `reachable=true`, `database.name=goaa_c2test`.
- 13102 BFF health: HTTP 200.
- `ReadWritePaths` contains both paths (above).

**Rollback (documented, not executed):** delete the drop-in → `systemctl daemon-reload` → restart `goaa-c2-clerk-api-3103.service`.

---

## 2. T1 — applicant end-to-end

**Account:** `c2e2e+clerk_test@example.com` (Clerk test email, OTP `424242`). Turnstile did **not** appear; nothing was bypassed.
**Applicant users.id:** `a429f075-b6d1-4edd-82cf-7e95cc8d65d5`.

| # | Step | Evidence |
|---|---|---|
| T1.1 | Login via `/client-login?next=%2Fagent-loop%2Fcustomer` | Clerk card, email OTP, session active |
| T1.2 | Customer page → Become an Agent → `/agent-loop/apply` | page rendered |
| T1.3 | Synthetic licence PNG upload | **`POST /api/v1/agent-loop/documents → 201 Created`**; file landed in `/opt/goaa-test/private-files-c2test` = **1 file / 38342 bytes** (count+bytes only, contents not read) |
| T1.4 | Submit | **`POST /api/v1/agent-loop/applications/me/submit → 200 OK`**; status `Submitted — waiting for review` |
| pre-review | advisory only | ENGINE `goaa-c2-rules-v1 · rules-only`, RECOMMENDATION `looks_complete`, **CAN AUTO-APPROVE `false`**, labelled "advisory only — never a decision" |

Screenshots: `t1-form.jpg`, `t1-submitted.jpg`, `t1-prereview.jpg`.

### T1.5 — negative gates (before approval)
- `/agent-loop/agent` → **`agent_role_required`** (panel not rendered).
- `/agent-loop/admin` → **`admin_required`** (no applicant data sent to the browser).

---

## 3. T2 — administrator review

| # | Step | Evidence |
|---|---|---|
| T2.1 | Login `c2admin+clerk_test@example.com` (account created) | Clerk user created; local `users` row `923f64ad-4bf6-44ca-9639-49c82f000825` |
| T2.2 | Grant admin via operator tool | `migrate` role: `python -m tools.grant_role --email c2admin+clerk_test@example.com --role admin --confirm` → rc=0, roles now `['admin','user']` |
| T2.3 | `/agent-loop/admin` queue | T1 application visible (Test Applicant / submitted / updated 2026/9/11 02:02:12); contact masked |
| T2.4 | Open application detail | masked applicant fields; licences table; document row (`front / image/png / c2-local-private / stub`); pre-review panel (`CAN AUTO-APPROVE false`); append-only review history (#87..#95, actor `user`) |
| T2.5 | Approve | **`POST /api/v1/agent-loop/admin/applications/59e17a01-.../approve → 200 OK`**; audit row **#97 `application.approve / admin / 2026/9/11 02:10:01`** |
| T2.6 | Role granted | DB: applicant `a429f075…` now has roles **`agent`** (granted 09:10:01Z) and `user`; application `59e17a01…` = `approved` |

Admin detail panel states "History is written by the server only. There is no edit or delete control here." Decision buttons present: Approve / Request more information / Reject / Suspend / Re-run pre-review.

Screenshots: `t2-queue.jpg`, `t2-review.jpg`.

---

## 4. T3 — agent portal (after approval)

Applicant re-login (existing account) → landed on `/agent-loop/agent`.

- Rail: **Overview / Opportunities / Service Orders / Knowledge Base / My AI / ⇄ Back to Customer**.
- Header: `AGENT PORTAL`, signed in as `c2e2e+clerk_test@example.com`.
- Panel: `licence active`; ACCOUNT ID `a429f075…`; APPLICATION `59e17a01…`; LICENCE GRANTED `2026/9/11 02:10:01`; **ROLES `agent, user`**.
- Page states explicitly: same account / same session — "you did not sign in twice and there is no second credential."
- "Not in this round": quoting/delivery/invoice/payout intentionally out of scope (not stubbed with fake numbers).

Screenshot: `t3-agent-overview.jpg`.

---

## 5. T4 — logout lifecycle

Triggered via the real UI control (account menu → **LOG OUT**).

| Check | Result |
|---|---|
| Backend revoke | **`POST /api/v1/agent-loop/golden/session/revoke → 200 OK`** (a second revoke call returned 401 — already revoked/absent credential; expected) |
| Clerk session | signed out |
| `localStorage.client_token` | cleared |
| `sessionStorage.goaa_golden_business_session` | cleared |
| Gated page after logout | `/agent-loop/agent` → redirect to `/client-login?next=%2Fagent-loop%2Fcustomer` |
| **Old business token rejected** | `GET /golden/session/verify` with the revoked token → **HTTP 401** |
| DB live tokens (applicant subject) | **0 live / 2 total** |

Screenshot: `t4-logout-menu.jpg` (account menu with LOG OUT).

**Observation (minor):** after a signed-out gated-page hit, the login entry redirects with `next=/agent-loop/customer` (the default), not the originally requested path. Recorded, not changed this round.

---

## 6. Test technique note (not a product issue)

The browser tool's file chooser did not bind to the page's **hidden** `<input type=file>` (`style="display:none"`), so the upload was performed by fetching the synthetic PNG from a **local CORS static server** (`t3-httpserv`, `127.0.0.1:8099`, `Access-Control-Allow-Origin: *`) and injecting it via `DataTransfer` into the input, then dispatching `change`. This is a **test harness technique only** — not a defect in the product. **`t3-httpserv` has been stopped** after this round.

---

## 7. Corrections applied

1. **`business_tokens.user_id` is the business-subject id, not `users.id`.** Token inspection now goes `users.id → business_subject_links.subject_id → business_tokens.user_id`. Schema confirmed: `business_subject_links(user_id, subject_id, linked_via, issuer, subject, created_at)`; `business_tokens(id, user_id, token, role, created_at, issued_at, last_used_at, revoked_at)`. Mapping used in T4: user `a429f075…` → subject `4717531f-6806-49ef-8326-6185f3ea1d3d`. **The earlier statement "applicant has no business token" is withdrawn** — the applicant did have tokens; they were simply not visible under a `users.id` join.
2. **New-account registration does not honour `next`.** First login through the Clerk **registration** branch lands on `/` instead of the requested target (observed twice: applicant first login and admin first login). Existing accounts honour the target. With zero legacy users, **every user goes through this path** → **pre-launch must-fix**. Not changed this round.

---

## 8. Findings / open items

- **F1 fixed** the document-storage blocker (see §1). Note the underlying misconfiguration: the service env `GOAA_C2_PRIVATE_FILES_DIR` and the unit `ReadWritePaths` disagreed; the discrepancy is now bridged by an additive drop-in rather than by aligning env+unit. Long-term, align the two.
- **§7.2** new-account `next` not honoured — pre-launch must-fix.
- **§5** signed-out redirect uses the default `next=/agent-loop/customer`.
- Business-token inspection requires the two-hop join (§7.1).

---

## 9. Screenshots

`t1-form.jpg`, `t1-submitted.jpg`, `t1-prereview.jpg`, `t2-queue.jpg`, `t2-review.jpg`, `t3-agent-overview.jpg`, `t4-logout-menu.jpg` (all in this directory).
