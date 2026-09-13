# GOAA · FINAL ROADMAP PROPOSAL — Integration Architecture Verification (G-3)

**Round:** G-3 · 2026-09-13 · **Mode:** read-only verification **+ planning only** — *nothing in this document has been executed*
**Order authority:** Tao · **Author:** Aika (GOAA infra agent)
**Prerequisites read in full this round:** `reports/2026-09-13/g1-verification/REPORT.md`, `reports/2026-09-13/g2-source-matrix/CAPABILITY-SOURCE-MATRIX.md` (not recalled from memory)
**Naming (fixed):** **D0** = Aika-Box / local dev · **C1** = Live / Production · **C2** = Test / Staging · cloud workers = W1…W6
**Discipline:** allowed = `read / hash / diff / status / DNS / systemd show / DB SELECT / manifest compare / public HTTP GET`. Executed: **no** delete, revoke, rollback-pointer edit, restart, deploy, DB write, migration, merge, force push, charge.
**Secret handling:** no secret value appears anywhere in this document. Keys are identified by **length + `sha256[0:16]`** only. Public IPv4 is masked as `a.b.c.⟨d⟩`.
**Scanner gate:** `TOTAL_HITS = 0`, `routable IPv4 unsplit = 0`, `BOM = False` (verified before commit).

---

## 0. Verdict summary — what Claude proposed, measured

| # | Claude proposition | Verdict | Basis (measured this round unless noted) |
|---|---|---|---|
| 1 | Next phase order should be: stop-bleed → freeze → staging gate → observability → identity/schema → skills/worker | **CONFIRMED (with one reordering)** | The order is right, **except** the single highest-risk asset (unbacked `goaa_platform` identity data) must be protected **inside M0**, not inside M2 — see §1/§7 |
| 2 | Stripe code itself is not the hardest part; the hard part is the old identity / client-token / `goaa_c2` → Clerk + `goaa_platform` UUID + roles mapping | **CONFIRMED** | Stripe files are *partly ref-anchored* (`invoice_pdf.py`, `stripe_checkout.py`, `stripe_pay.py` byte-match `a532a66`); the two identity stores share **zero** columns, **zero** FKs, and intersect on **exactly 1 of 72** old accounts — see §5 |
| 3 | `agent` in the data layer = licensed human; do **not** rename; avoid a big migration | **CONFIRMED — and already true today** | The commerce DB *already* uses `goaa_agent_*` for the AI side and `goaa_order_agents` for humans; the platform DB `agent_*` = licensed human. Two meanings already coexist → freeze, don't rename — see §6 |
| 4 | C2 can serve as the mandatory `ALL CHANGE → C2 → acceptance → C1` gate | **PARTIAL** | Schema parity is **perfect** (identical 119-column fingerprint) and the Clerk tenants are **isolated** (C2 = dev tenant, C1 = prod custom domain). But there is no acceptance automation, no promotion path, no C2 backups, port/build drift and disabled-but-active units — see §3 |
| 5 | Rollback baseline should move off `76af718` | **CONFIRMED** (G-1 §1) | Still pointing at the pre-Clerk build today; Clerk-capable fallback = `40c8546e` only |
| 6 | Revoke the old Clerk keys | **CONFIRMED** (G-1 §2) | 3 legacy production-instance secret keys in `/root` backups; live key differs |
| 7 | Clean up the `/root` backups | **CONFIRMED** (G-1 §3) | 4 of 5 files carry the legacy glue |
| 8 | Add automatic DB backup | **CONFIRMED — but scope is wrong as stated** | It must cover `goaa_platform` + licence documents + the private-file store, not just the commerce DB (G-1 §4) |
| 9 | 3103 does not self-heal | **CONFIRMED** (G-1 §5) | `Restart=no`; same defect exists on **two C2 units** and `nginx` |
| 10 | `www.goaa.ai` still serves the old template | **REJECTED** (G-1 §6) | Served content = new English site; 0 legacy markers |
| 11 | GitHub drift is a governance problem, not a survivability problem | **PARTIAL** (G-2) | True for the Clerk front-end + agent-loop backend; **false** for the 130-file commerce runtime and the identity data |
| 12 | A `0007` migration is needed for the identity/schema bridge | **CONFIRMED** | Draft in §5.4 — **design only, nothing applied** |

---

## 1. M0 — stop the bleeding: item-by-item timing

Classification key: **NOW** = do before any new feature work · **BEFORE STRIPE** = must exist before any real payment path is touched · **LATER** = real, but not on the critical path.

### 1.1 The four items from the order

| Item | Verdict | Why (evidence) | Executor | Risk of doing it | Risk of NOT doing it | Rollback | Effort |
|---|---|---|---|---|---|---|---|
| **a. Clerk key revoke** | **BEFORE STRIPE** *(not NOW)* | The 3 legacy keys are **same-instance** as production (publishable fp `562a0cfc245df772`), but *whether they still authenticate is UNKNOWN* and can only be established in the Clerk dashboard. Nothing in the running app depends on them (only the current key fp `45e9487a9d4bf1ea` is loaded). | **Tao**, in the Clerk dashboard | Revoking a key something still uses → auth outage for that client | Plaintext production-instance keys in `/root` are captured by any droplet image/snapshot | Re-issue a key and update the 3 env surfaces | 0.5 h (Tao) |
| **b. `/root` backup cleanup** | **BEFORE STRIPE** — strictly **after (a)** | 4 of 5 backups carry the 253-char glue (3 legacy secrets). Ordering (a)→(b) is mandatory. | Tao/Aika (change window) | Deleting the wrong file | Same as (a) | Nothing to restore from ⇒ **quarantine by `mv`, not `rm`**, for 30 days | 0.5 h |
| **c. Rollback baseline update** | **NOW** | `/root/r5b2-rollback-point.txt` + `r5b4-…` still contain the pre-Clerk release path, while `goaa_platform` already holds 2 Clerk users + 1 approved agent application. A rollback today silently removes all sign-in. | Tao approval → Aika executes (pointer edit only) | Using a **build that broke** as the new baseline | Next incident rollback causes an identity/UI mismatch with no on-disk Clerk-capable fallback | Point it back (1 command) | 5 min |
| **d. Automatic DB backup** | **NOW** — the **only** irreversible-loss item in the whole estate | `goaa_platform` (15 tables) has **no dump at all**; all existing dumps target the commerce DB `goaa` and predate every identity row. No dump cron exists on C1, C2 or D0. | Tao approval → Aika executes | Disk growth; a careless cron that archives secrets | Losing the only copy of production identity + licence documents | Delete cron; keep dumps | 2 h (including one restore drill) |

**Reordering judgement (the one correction to Claude's sequence):** the order lists "DB automatic backup" as later hygiene. It is the **only** action in M0 that addresses a *currently unrecoverable* asset, and it is **additive and zero-risk** (a dump reads; it does not change production). Therefore **M0 = (d) then (c)**, with (a)+(b) queued as a Tao-side half-hour task.

### 1.2 Three M0 items Claude did not list, discovered this round

| Item | Verdict | Evidence | Note |
|---|---|---|---|
| **e. `Restart=no` on the C2 Clerk units** | **NOW (cheap)** | `goaa-c2-clerk-api-3103` and `goaa-c2-clerk-ui-3102` are `Restart=no` **and** `disabled` yet `active`. After any reboot the entire Clerk staging surface silently disappears. | Same defect class as C1's 3103 (G-1 §5) |
| **f. Stale `/root/.cloudflared/` config on C1** | **LATER** | The unit loads `/etc/cloudflared/config.yml`; `/root` holds an older stub listing only `api.goaa.ai`. It caused one wrong conclusion already. | Mark or quarantine; never edit the live file |
| **g. Bare-value secret files exist** | **BEFORE STRIPE** | On C2, `/opt/goaa-test/env/` contains files whose entire content is a bare credential (mode `600`, root-owned) rather than `NAME=value`. These are invisible to name-based secret scanning and were only caught because a dump filter leaked one line into a tool transcript — **that value is deliberately not reproduced here and was never committed**. | Introduce a naming rule + a scanner that reads *values*, not *names* |

> **Note on (g):** this is a self-reported handling incident. The value left the host only inside my own tool output, never into a report, never to the relay, never to GitHub. It is recorded here because the future scanner must be value-based.

---

## 2. M0.5 — machine-verifiable freeze: 5 surfaces × 8 evidence types

**Definition.** A surface is *frozen* when, for each of the 8 evidence types, a value exists that a third party can re-derive **without** asking us. Anything missing is a hole, not an assumption.

**Important structural finding:** the four C1 surfaces are **one build** (`40c8546e`, BUILD_ID `FW7iufKj5JrPAz9Kx2SkX`). They therefore share source ref / BUILD_ID / manifest / migrations / units, and differ only in **route list**. Freezing them as four *separate* deliverables would be ceremony. Freeze them as **one artifact + four route contracts**.

| Evidence type | **Homepage / public entry** | **AI Butler** (customer portal) | **AI Agent** (agent portal) | **AI Admin** (admin portal) | **Aika-Box** (local console) |
|---|---|---|---|---|---|
| **Source ref** | `40c8546e` (branch `feat/c2-clerk-unified-login-v1`) — **local-only; no GitHub ref** | same `40c8546e` | same `40c8546e` | same `40c8546e` | D0 `local-console/` working tree, git path HEAD `4309b114`; tree identical across 5 refs (inherited `faa9f6ba4603ef9b`) |
| **BUILD_ID** | `FW7iufKj5JrPAz9Kx2SkX` (release dir = commit sha, symlinked from `current`) | same | same | same | n/a (Python) — app version `5.2.C-2` + unit revision |
| **Artifact manifest sha** | deployed tree fingerprint `f8efdc333f25ef7d` (1,969 files / 28,138,994 B); byte manifest `reports/2026-09-11/c1fix/deployed-manifest.sha256` (2,075 entries) | same two | same two | same two | working-tree fingerprint `018d3678c803337b` (35 files = every non-`__pycache__` file under `local-console/`, sorted path+sha256). **Must be re-cut excluding `local_user.db` / `.pytest_cache` to be meaningful** |
| **Route list** | public: `/` (200, 16,075 B, sha16 `314361aee777d01e`), `/client-login` (200, 10,893 B, sha16 `82fea21ae3411e42`), `/agent-login`, `/goaa-clerk-login` → 307 → `/client-login`, `/connect-pass`, `/planning` | `/agent-loop/customer*` (4 sub-routes) — unauth → 307 `/agent-loop/login?next=…` | `/agent-loop/agent*` (5 sections) — same 307 gate | `/agent-loop/admin*` (6 sections) — same 307 gate | 20 route decorators: `/`, `/health`, `/login` (GET+POST), `/logout`, `/session`, `/settings/{models,skills,agents}`, `/tasks/{plan,run,results,results/{id}}`, `/ai/chat`, `/rag/{chat,topk,stats}`, `/logs/recent`, `/node/health` |
| **DB migration** | none | `goaa_platform` migrations `0001_identity … 0006_golden_business_session` (all 6 applied; `schema_migrations` = 6 rows, applied 2026-09-12 06:23Z) | same | same | none (SQLite `local_user.db`) |
| **Env key names** | C1 `/opt/goaa-frontend/env/web.env` + `/opt/goaa-platform/env/api-3103.env`: `GOAA_C2_ENV`, `GOAA_C2_DB_{NAME,PORT,USER,PASSFILE}`, `GOAA_C2_PUBLIC_BASE_URL`, `CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES`, `GOAA_AGENT_LOOP_UPSTREAM` (+ Clerk keys — lengths/fingerprints only, per G-1 §2) | same files | same files | same files | `/etc/goaa/console.env`: `CONSOLE_SESSION_KEY`, `POSTGRES_{HOST,PORT,DB,USER,PASSWORD}`, `OLLAMA_URL`, `EMBED_MODEL`, `ENABLE_RAG_CHAT` |
| **Service unit** | `goaa-web.service` (production Next.js, `Restart=on-failure`, `RestartUSec=3s`, enabled, 127.0.0.1:3100) behind `cloudflared.service` (`/etc/cloudflared/config.yml`, tunnel `66ad1cc0-…`) | same | same + `goaa-platform-api-3103.service` (`Restart=no`; **no `/health` route**) | same | `goaa-local-console.service` (`User=aika`, drop-in override → `WorkingDirectory=/home/aika/Projects/goaa-ai-main/local-console`, `Restart=always`, `RestartSec=5`, 127.0.0.1:5188) + `goaa-local-console-tailscale-proxy.service` (100.114.37.90:5188) |
| **Rollback point** | `/root/r5b2-rollback-point.txt` = `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` ← **WRONG — must move to `40c8546e…`**; second-line candidate `f719b27` (needs a fresh build) | same | same | same | git `4309b114` (path-scoped) — **no pointer file exists** |

**Freeze acceptance test (proposed):** a script that, given the 5 surface names, re-derives all 40 cells and diffs them against a committed `freeze-manifest.json`; exit non-zero on any difference. That manifest is the M0.5 deliverable.

**Holes M0.5 must close:**
1. Rollback pointer (blocking — currently *wrong*, not merely missing).
2. No committed freeze manifest tied to a surface contract (the C1 deployed manifest exists but is not bound to any surface).
3. Aika-Box has no rollback pointer and no clean tree fingerprint (runtime artefacts must be excluded).
4. The three portal route lists here come from route probing only — the authoritative lists must be cut from the frozen build, not from memory.

---

## 3. Staging discipline — can C2 be the mandatory gate?

**Verdict: PARTIAL.** Two of the hardest properties are already true; eight operational properties are not.

### 3.1 What is already true (measured)

| Property | Evidence |
|---|---|
| **Schema parity C1 ↔ C2** | C1 `goaa_platform` and C2 `goaa_c2test` produce the **identical** column fingerprint: 119 columns, `sha16 = b2e18381ca5eb7cf`, same 6 migrations. A migration that passes on C2 is schema-identical on C1. |
| **Identity isolation** | C2 uses a **Clerk dev tenant** (`CLERK_ISSUER` = `https://lenient-phoenix-9847.clerk.accounts.dev`) with its own key pair (fp `9dea33a55d424704` / `f703fd4d199c08df`); C1 uses the production custom domain `clerk.goaa.ai`. **No shared tenant** ⇒ staging sign-ins cannot touch production identities. |
| **Acceptance tests exist** | `backend-clerk-20260910/tests/` holds 10 suites incl. `test_clerk_auth.py`, `test_clerk_identity_jit.py`, `test_clerk_identity_mapping.py`, `test_golden_business_contract.py`, `test_golden_session_lifecycle.py`, `test_schema_and_migrations.py`, `test_application_loop.py`, `test_auth_and_sessions.py`, plus `tools/migrate.py` and a `support/` fixture dir. |

### 3.2 What is missing (the gap list for M1)

| # | Gap | Evidence | Effect on the gate |
|---|---|---|---|
| 1 | **No automated acceptance run** | No CI config and no runner that exercises the *deployed* C2 service; tests are run by hand in a venv (`venv3103-clerk/bin/` lists an interpreter, no test runner binary). | "acceptance" is a human judgement, not a gate |
| 2 | **No promotion path** | C2's build (`28IP1GvAGURvF1PHRk8EL`) ≠ C1's (`FW7iufKj5JrPAz9Kx2SkX`); C2 carries **three** web trees (`ui`, `ui-clerk-20260910`, `p5-153-candidate`) and C1's built tree has **no tarball**. | nothing to promote *from*; re-builds are ad-hoc |
| 3 | **Port / layout drift** | C2: agent-loop **3101**, clerk-api **3103**, clerk-ui **13102**, web 3100. C1: agent-loop **3103**, web 3100. | the same test cannot be replayed unchanged on C1 |
| 4 | **Disabled-but-active units** | `goaa-c2-clerk-api-3103`, `goaa-c2-clerk-ui-3102`: `UnitFileState=disabled`, `ActiveState=active`. | a reboot silently removes staging |
| 5 | **No C2 backups** | No backup directory, no backup timer, no root crontab on C2. | staging cannot be rolled back either ⇒ a bad migration on C2 is as unrecoverable as on C1 |
| 6 | **C2 not reachable over public TLS** | nginx `server_name _` → 127.0.0.1:3100; local `https://127.0.0.1/` = **401**, http = 301. No documented acceptance URL. | human acceptance needs an ssh tunnel; Clerk redirects cannot be exercised end-to-end (`GOAA_C2_PUBLIC_BASE_URL` is **empty** on C2) |
| 7 | **Stale decoy database** | `goaa_c2` = 10 tables, **0 rows in every table**; the **enabled** `goaa-c2-agent-loop` unit (port 3101) points at it. | "which C2 is the candidate?" is ambiguous |
| 8 | **No staging data policy** | `goaa_c2test` holds 49 users / 55 roles / 12 applications on a dev tenant; three private-file dirs coexist (`private-files`, `private-files-c2test`, `private-files-e2e`). | acceptance results are not reproducible from a known fixture set |

### 3.3 Verdict on the gate

- **Gate shape justified today:** `change → C2 CLI tests (human-run) → manual smoke → C1`, with the **schema-parity** property doing the real work.
- **Gate shape Claude proposes:** `ALL CHANGE → C2 → acceptance → C1` as a *hard* gate — true after gaps 1–4 are closed (M1); *safe* after gaps 5–8 (M1.5).
- **One exemption must be stated explicitly:** the **golden commerce runtime** (`/opt/goaa/runtime`, 130 files) has **no C2 twin at all** — C2 hosts only the identity/agent-loop stack. A change to the order/payment runtime **cannot** pass through C2 today. That is the largest hole in the gate, and it is why §5/§7 put commerce linkage work in C2 *before* any C1 payment change.

---

## 4. Observability — minimum pre-launch requirements

### 4.1 Measured current state (C1 unless stated)

| Requirement | Current state | Verdict |
|---|---|---|
| **Structured logs** | `api-3103.log` = plain text, 36,678 B, `600 root:root`, actively written; **no logrotate entry for any GOAA app**; journald persistent at **4.0 GB**. | **FAIL** (unstructured + unbounded + root-only) |
| **Health check** | `/health` = 200 on openclaw `:18789` (90 B), router `:8080` (278 B), qwenpaw `:8088` (35 B). **`/health` and `/healthz` = 404 on the agent-loop API `:3103`.** Frontend `:3100` has no `/api/health` (404). cloudflared exposes no check. | **PARTIAL** |
| **Error-rate alert** | None. No monitoring unit on C1, C2 or D0. The only alerting path in the estate is `send_consistency_alert.py` (SMTP) driven by the Regulation-47 git-consistency cron (`0 7 * * *`, `--dry-run`). The lone C1 container that looks like monitoring — `goaa-heartbeat` — is `sh -c 'while true; do echo heartbeat; sleep 30; done'`, i.e. **decoration, not telemetry**. | **FAIL** |
| **Payment webhook alert** | None. The route exists (`/api/v1/order/webhook/stripe`, GET → 405; sibling `/api/v1/order/webhook/payment`), but a failed, replayed or unsigned webhook raises nothing. | **FAIL** |
| **DB backup alert** | None — and there is no backup job to alert on. | **FAIL** |
| **Service restart policy** | `goaa-web` on-failure ✅ · `openclaw` always ✅ · `qwenpaw` always ✅ · `goaa-router` on-failure ✅ (`NRestarts=1` — it *has* crashed and recovered) · **`goaa-platform-api-3103` = no ❌** · C2: `goaa-c2-agent-loop` on-failure ✅, `goaa-web-candidate` on-failure ✅, **`goaa-c2-clerk-*` = no ❌**, `nginx` = no ⚠️ · D0: `goaa-local-console` always ✅ | **PARTIAL** |
| *(existing alert channel)* | SMTP already wired: `SMTP_{HOST,PORT,USER,PASS}` + `EMAIL_TO` exist in the C1 secrets file and are used by `send_consistency_alert.py`. | **reusable building block** |

### 4.2 Proposed minimum (deliverable of M1.5)

Six items, each with an objective acceptance test — no dashboards, no new vendors:

1. **Structured logs** — one JSON line per request (`ts, service, level, route, status, duration_ms, request_id, user_ref`) for the four C1 services; logrotate 14 d; `request_id` propagated from cloudflared. *Accept:* the last 100 lines of each service's log parse with 0 failures.
2. **Health endpoints** — add `/health` (liveness: process up) and `/healthz` (readiness: DB reachable + migration count == expected) to the agent-loop API; expose a public health route through the tunnel. *Accept:* 200 while the DB is up, 503 within 5 s of the DB closing.
3. **Error-rate alert** — SMTP alert when the 5xx rate over 5 min exceeds 1 %, or when any service restarts > 3 times in 15 min. *Accept:* break one dependency in C2, receive the mail.
4. **Payment webhook alert** — alert on any webhook that fails signature verification, returns 5xx, or arrives with an already-seen event id; and alert when **no** webhook arrives for 26 h while a payment is `pending`. *Accept:* replay a captured test webhook in C2 → exactly one alert, one processing.
5. **DB backup alert** — alert if the newest `goaa_platform` dump is older than 26 h, smaller than 90 % of the previous, or fails a `pg_restore --list` check. *Accept:* point the check at a stale file → alert fires.
6. **Restart policy** — `Restart=on-failure`, `RestartSec=2` on `goaa-platform-api-3103` and both C2 Clerk units; document the exception list. *Accept:* `systemctl show … -p Restart` = `on-failure` on all four; kill one in C2 and observe recovery.

---

## 5. Stripe identity / schema — verification and the `0007` design draft

### 5.1 Verifying Claude's judgement

**CONFIRMED, with a sharper statement of why.**

- The *Stripe* surface is small and partly anchored: `stripe_checkout.py` (9,990 B, sha16 `53abfba37212c768`), `stripe_pay.py` (5,742 B, sha16 `2465f5220b11274b`) and `invoice_pdf.py` **byte-match** the local-only ref `a532a66`; the only commerce ref gaps are `main.py` (webhook host) and `planning_engine.py`. Stripe is a **hand-written REST client** (`create_checkout_session`, `create_connect_account`, `create_account_link`, `create_transfer`) — one adapter, not a platform (G-2 §Q2b).
- The *identity* surface is where the work is: the commerce DB and the platform DB have **no column, no FK and no naming link** between them:
  - commerce identity = `goaa_order_users(id text, email, password_hash, role, name, phone, status, agent_ref_id, google_sub, email_verified)` + `goaa_order_tokens(user_id text, token, role)` — **72 users** (admin 1 / agent 31 / customer 40), 69 with a password hash, 259 tokens (**0 revoked**, all 32-char);
  - platform identity = `users(id uuid, …)` + `user_identities(provider, issuer, subject, email_snapshot)` + `user_roles(user_id uuid, role, granted_by)` + `business_tokens(user_id uuid, token, role)` — **2 users**, 4 role rows, **2 identities** (both `provider='clerk'`, `issuer='https://clerk.goaa.ai'`), 3 business tokens (32-char);
  - **`goaa_platform.users.email` is NULL for every row** — the e-mail lives in `user_identities.email_snapshot`;
  - **overlap between the two identity populations = 1 e-mail of 72** (commerce 72 unique e-mails vs platform 2 snapshots → intersection 1);
  - `agent_ref_id` is NULL for all 72 commerce rows and `google_sub` is set on 3 ⇒ neither can serve as the bridge key.
- **`goaa_c2` is a decoy**: 10 tables, every count 0, superseded by `goaa_c2test`. Nothing of the "old client_token → C2" story lives there any more.

### 5.2 Old tables vs new tables

| Domain | **Old (commerce, DB `goaa`)** | **New (identity, DB `goaa_platform`)** | Bridge needed |
|---|---|---|---|
| Account | `goaa_order_users` (id **text**, role ∈ customer/agent/admin) | `users` (id **uuid**) + `user_identities` (provider/issuer/subject) | **new link** |
| Session / token | `goaa_order_tokens` (259 rows, 32-char) | `business_tokens` (3 rows, 32-char, `user_id uuid`) + `user_sessions` | extend `business_tokens` usage |
| Role | `goaa_order_users.role` | `user_roles(user_id uuid, role, granted_by)` + `agent_review_events` | **grant path exists** (`tools/grant_role.py`) |
| Provider (human) | `goaa_order_agents(agent_id text, user_id text, display_name, bio, service_areas, rating, active, stripe_connect_account_id, stripe_onboarding_status)` — **28 rows** | `agent_applications`, `agent_licenses`, `agent_license_documents`, `user_roles.role='agent'` | **new link** |
| Demand | `goaa_order_opportunities(customer_user_id text, matched_agent_id text)` — 10 rows | `business_subjects` + `business_subject_links` (golden session) | optional subject link |
| Work | `goaa_order_service_orders(customer_user_id, agent_id, connect_paid, connect_paid_at, connect_expires_at, connect_checkout_session_id, service_checkout_session_id, handoff_context jsonb)` — 36 rows, 21 with `connect_paid=true` | — (no order concept) | none (stays in commerce) |
| Money | `goaa_order_payments(service_order_id, provider, provider_payment_id, amount_cents, status, **payment_type**, idempotency_key, metadata)` — 41 rows: `connection_fee` 12 (10 succeeded / 2 pending), `service_fee` 3, legacy `unknown` 26 | — | none |
| Payout | `goaa_order_settlements(service_order_id, payment_id, agent_id, amount_cents, stripe_connect_account_id, status, transfer_id, transfer_status, settled_at)` — 14 rows (`ready\|none` 3, `processing\|pending` 1, `paid\|created` 4, `paid\|paid` 4, `paid\|none` 2) | — | none |
| Document | `goaa_order_invoices(invoice_number, service_order_id, customer_user_id, agent_id, amount_cents, payment_id, status, pdf_key)` — 7 rows | — | owner/provider link |

### 5.3 The eight required answers

**(1) How does an order owner bind to `goaa_platform.users.id`?**
Add an explicit link table (§5.4) — **never** rewrite `goaa_order_users.id` (text → uuid) in one step. Binding rules:
- `provider='clerk'`, `issuer='https://clerk.goaa.ai'`, `subject` = Clerk subject, verified against `user_identities`.
- Resolution order: (i) existing link row → reuse; (ii) `business_tokens.user_id` already present → reuse; (iii) e-mail match against `user_identities.email_snapshot` (case-insensitive) → create a **proposed** link (there is exactly **1** such production case today); (iv) no match → create the link lazily on first authenticated visit (JIT), never in bulk.

**(2) How do providers/agents bind to `user_roles` / licences?**
`order_provider_links` keyed by `goaa_order_agents.agent_id`, plus a **role grant** to `user_roles(role='agent')` executed through the existing `tools/grant_role.py` path (the only writer that records `granted_by`, with `agent_review_events` append-only per migration 0003). Licence authority stays in `agent_licenses` / `agent_license_documents` — the link must **not** copy licence numbers, because the commerce table has no licence column at all. Reconciliation to plan for: **28 commerce providers** vs **1 platform licence / 2 approved applications**.

**(3) How does a payment relate to matter/order?**
No change to the money tables' keys. `payment → service_order → opportunity/subject`:
- `goaa_order_payments.service_order_id` stays the primary relationship (all 41 rows carry it);
- add a **nullable, denormalised** `platform_owner_user_id` / `platform_provider_user_id` on `goaa_order_service_orders` only if the golden-session contract needs it (the platform's `business_subject_links` remains the authority);
- never duplicate amounts: `amount_cents` stays in commerce; the platform stores no money.

**(4) How are `connection_fee` and `service_fee` separated?**
Already separated in the data: `payment_type` ∈ {`connection_fee`, `service_fee`, legacy `unknown`} plus **two distinct checkout sessions** per order (`connect_checkout_session_id` vs `service_checkout_session_id`) and `connect_paid` (21 true / 15 false) with `connect_paid_at` / `connect_expires_at`; `CONNECTION_FEE_CENTS = 3990`. `0007` should **formalise, not invent**: add the CHECK/enum on `payment_type`, and define the 26 legacy `unknown` rows as `service_fee` **only** where the order has no `connect_*` session — otherwise leave them `unknown` (fail-closed). No amount arithmetic may be inferred from these rows in new code paths.

**(5) When is a settlement produced?**
Event-driven, on the **service_fee** path only: service-fee payment success → settlement row created `status='ready'`, `transfer_status='none'` → admin action (`/api/v1/order/admin/settlements/{sid}/settle`) → Connect transfer (`create_transfer`) → `status='paid'` with `transfer_status='created'|'paid'`. The 14 existing rows match this shape. `0007` must **not** add an auto-payout trigger; it adds only the missing constraints (e.g. `transfer_id` required once `transfer_status <> 'none'`).

**(6) How do invoice owner / provider relate?**
`goaa_order_invoices.customer_user_id` = owner, `agent_id` = provider, `payment_id` = money. Add the same two nullable link columns (owner, provider) and backfill via (1)/(2). `pdf_key` stays in the storage layer; invoices are documents, not identity.

**(7) Where does the webhook idempotency key live?**
**Not** in `goaa_platform.idempotency_keys`: that table is user-scoped (`user_id NOT NULL`) and stores API response bodies — wrong shape for Stripe. Two layers are needed:
- **existing app-level dedupe**: `goaa_order_payments.idempotency_key` is already populated on **41/41** rows — keep it;
- **new webhook layer**: `payment_webhook_events(provider, event_id PK, received_at, signature_ok, payload_sha256, processed_at, status, attempts)` with the provider's event id as primary key. Replay protection = insert-first semantics; a duplicate insert attempt raises the alert from §4 item 4.

**(8) Old business data migration strategy**
Three phases, **no big-bang**, no rename, no cross-database movement:
- **Phase A (link-only, additive):** create the link tables (nullable, unpopulated); nothing reads them.
- **Phase B (lazy dual-write):** every authenticated hit on the golden-session / agent-loop path writes or refreshes a link through the platform backend (single writer); commerce code untouched.
- **Phase C (read switch):** new endpoints read identity through the link with a fallback to the legacy text id; the legacy `goaa_order_users.role` stays the commerce-side authority. Retire fallbacks only after 30 days of zero fallback hits (logged).
- Data never moves between the two databases; they stay separate, joined by `uuid` links.

### 5.4 `0007` schema design draft — **DESIGN ONLY, NOT EXECUTED**

Name: `0007_order_identity_links`. Constraints on the design: additive only; no renames; no data movement; every new column nullable; the word `agent` keeps its licensed-human meaning.

```sql
-- 0007_order_identity_links  (DRAFT — NOT APPLIED ANYWHERE)
-- Additive only. Rollback = 0007_rollback (DROP the new objects).

-- 1. identity link: commerce order account -> platform uuid account
CREATE TABLE order_identity_links (
  order_user_id      text        PRIMARY KEY,          -- goaa_order_users.id (commerce)
  platform_user_id   uuid        NOT NULL,             -- goaa_platform.users.id
  linked_via         text        NOT NULL,             -- 'explicit' | 'business_token' | 'email_jit' | 'manual'
  issuer             text        NOT NULL,             -- e.g. the Clerk issuer URL
  subject            text        NOT NULL,             -- Clerk subject
  confidence         text        NOT NULL,             -- 'verified' | 'proposed'
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX order_identity_links_platform_idx ON order_identity_links (platform_user_id);
CREATE UNIQUE INDEX order_identity_links_subject_idx ON order_identity_links (issuer, subject);

-- 2. provider link: commerce human provider -> platform licensed user
CREATE TABLE order_provider_links (
  order_agent_id     text        PRIMARY KEY,          -- goaa_order_agents.agent_id (commerce)
  platform_user_id   uuid        NOT NULL,             -- goaa_platform.users.id (role 'agent')
  license_id         uuid        NULL,                 -- goaa_platform.agent_licenses.id
  linked_via         text        NOT NULL,             -- 'approved_application' | 'manual'
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX order_provider_links_user_idx ON order_provider_links (platform_user_id);

-- 3. payment webhook ledger (idempotency; replaces nothing)
CREATE TABLE payment_webhook_events (
  provider           text        NOT NULL,             -- 'stripe'
  event_id           text        NOT NULL,
  received_at        timestamptz NOT NULL DEFAULT now(),
  signature_ok       boolean     NOT NULL,
  payload_sha256     text        NOT NULL,
  processed_at       timestamptz NULL,
  status             text        NOT NULL,             -- 'received' | 'processed' | 'ignored' | 'failed'
  attempts           integer     NOT NULL DEFAULT 0,
  PRIMARY KEY (provider, event_id)
);

-- 4. denormalised, nullable links (commerce side) — reader convenience only
ALTER TABLE goaa_order_service_orders
  ADD COLUMN platform_owner_user_id    uuid NULL,
  ADD COLUMN platform_provider_user_id uuid NULL;
ALTER TABLE goaa_order_invoices
  ADD COLUMN platform_owner_user_id    uuid NULL,
  ADD COLUMN platform_provider_user_id uuid NULL;

-- 5. formalise the fee kind introduced by migration 0009 (no value rewriting)
ALTER TABLE goaa_order_payments
  ADD CONSTRAINT goaa_order_payments_type_chk
  CHECK (payment_type IN ('connection_fee','service_fee','unknown'));

-- 6. payout integrity: a transfer id must exist once a transfer has been created
ALTER TABLE goaa_order_settlements
  ADD CONSTRAINT goaa_order_settlements_transfer_chk
  CHECK (transfer_status = 'none' OR transfer_id IS NOT NULL);

-- 7. append-only audit for link changes (mirrors migration 0003 discipline)
CREATE TABLE order_identity_link_events (
  id             bigserial   PRIMARY KEY,
  occurred_at    timestamptz NOT NULL DEFAULT now(),
  order_user_id  text        NULL,
  order_agent_id text        NULL,
  actor_user_id  uuid        NULL,
  action         text        NOT NULL,   -- 'link_created' | 'link_proposed' | 'link_confirmed' | 'link_revoked'
  detail         jsonb       NOT NULL DEFAULT '{}'::jsonb
);
```

**Explicitly out of scope for `0007`:** any `UPDATE`/`INSERT` that copies rows between the two databases; any rename of `goaa_agent_*` or `agent_*`; any auto-payout trigger; any change to `amount_cents` semantics.

**Backfill (Phase A/B, separate work, not part of the schema migration):** derived from `user_identities` (2 rows) + `business_tokens` (3 rows) + e-mail comparison (1 candidate) ⇒ the first backfill should create roughly **1–3** verified/proposed links, not 72. Anything more must be justified row by row.

---

## 6. Skills / AI Agents / Worker — registry & adapter boundaries

### 6.1 The vocabulary problem, measured

The estate already uses the word *agent* with two meanings — so freezing is the correct move, and the freeze is **already half-true in the data**:

| Layer | AI side | Human side |
|---|---|---|
| Commerce DB `goaa` | `goaa_agent_profiles(agent_id, name, email, license_type, license_states, specialties, languages, subscription_status)`, `goaa_agent_skills(agent_id, skill_id, enabled)`, `goaa_agent_knowledge_docs`, `goaa_agent_tokens` (2 profile rows) | `goaa_order_agents(agent_id, user_id, display_name, bio, service_areas, rating, active, stripe_connect_account_id, …)` — **28 rows**, the professionals |
| Platform DB `goaa_platform` | — (no AI objects at all) | `agent_applications`, `agent_licenses`, `agent_license_documents`, `agent_review_events`, `user_roles.role='agent'` — licensed humans only |
| D0 console registry | `registry/agents.json` (4 entries with `agent_id, agent_name, agent_deployment_type, agent_category, agent_runtime, bound_skills, permission_scope, status, enabled`) = **software agents**; `registry/models.json` (4); `registry/skills.json` (5 entries with `skill_id, skill_name, executor, supported_execution_targets, permission_level, billing_mode, enabled, audit_required`) | — |

⇒ **Rule adopted (CONFIRMED with Claude):** the *data layer* keeps `agent` = licensed human. The *software* concept is expressed as **skill / software agent / worker**. UI labels may say "AI Agent"; DB columns, tables and APIs may not change meaning. No rename, no migration of these names.

### 6.2 Boundary definition (proposed contract)

| Concept | What it is | Authority / registry | Execution target | Permission unit | Billing |
|---|---|---|---|---|---|
| **Skill** | A named capability with an executor and a permission level | `local-console/registry/skills.json` (5) + platform skill tables | declared `supported_execution_targets` | `permission_level` + `audit_required` | `billing_mode` (per skill) |
| **Software agent** | A configured composition of skills with a runtime and a scope | `local-console/registry/agents.json` (4) | its `agent_runtime` | `permission_scope` + `status`/`enabled` | inherited from bound skills |
| **Human professional** | A licensed person who receives work and money | platform `agent_applications` → `agent_licenses` → `user_roles(role='agent')`; commerce `goaa_order_agents` | the professional handoff / Connect flow | role grant + licence validity | `service_fee` → settlement → Connect transfer |
| **Worker** | Anonymous compute capacity that executes tasks | router `:8080` `WORKER_ID`; `docs/runtime/worker-capabilities.json` (9 keys, **stale: 3 nodes, 2 online**) and `docs/node-registry/node-registry.json` (v1.0.3, 5 nodes: 1 active coordinator, 1 bootstrapping, 1 reserved, 1 active cloud worker, 1 decommissioned) | `/opt/goaa/workers/agent.py` (120 lines, `WORKER_ID`-keyed, **no git ref**) | none (infrastructure identity, not a business identity) | none |

**Adapter boundaries:**
- Workers talk **only** to the router (`ROUTER_API`), never to the platform DB. Router = 28 routes; openclaw = 110 routes with exactly two webhook entries (`…/webhook/payment`, `…/webhook/stripe`).
- Software agents and skills are **declared**, never self-registering; the registry files are the contract.
- Human professionals are **never** modelled as workers; the only link between the two worlds is `agent_id` on the money tables (§5).
- The registries are stale (dated 2026-05) and one node is `decommissioned` with `bootstrap_status` "pending SSH execution" ⇒ treat them as *documentation*, and place "regenerate node/capability registries" in M4 rather than trusting them.

---

## 7. Final milestone proposal

**Naming note:** M0…M5 below are **infrastructure milestones**, unrelated to the product roadmap `docs/roadmap/GOAA_V5.2.C_V5.5_ROADMAP.md` (V5.2.C-1/C-2, V5.3…V5.5). If Tao prefers, prefix them `G-M0…G-M5` in future instructions to avoid collision.

**Parallel track (mandatory, starts with M0.5):** *Survivability* — the assets whose only copy is one node (G-2 §Q4): (i) `/opt/goaa/runtime` 130 files → a ref; (ii) `goaa_platform` dump → offsite; (iii) the worker `agent.py` family; (iv) the **13 local-only branches** → GitHub (after a 0-hit secret scan and `GH013` handling). This track is not a milestone; it is a standing obligation that must not slip behind feature work.

---

### M0 — Stop the bleeding
- **Goal:** remove the only unrecoverable loss risk and the wrong rollback target.
- **Entry criteria:** Tao approval for (a)–(d); a maintenance note (no user-visible change).
- **Deliverable:** `goaa_platform` dump (schema + data + licence documents + private-file manifest) written to **two** locations, one off-host; one restore drill into a scratch database with a row-count diff; rollback pointer moved to `40c8546e…`; `Restart=on-failure` on the agent-loop unit; a written inventory of what the 3 legacy Clerk keys are for (dashboard).
- **Exit criteria:** the restore reproduces `users 2 / user_roles 4 / user_identities 2 / agent_applications 1 / agent_license_documents 1 / schema_migrations 6`; the rollback file contains the `40c8546e` path; `systemctl show` reports `on-failure`; a 26-hour-later automatic dump exists.
- **Risk:** low (additive/read-only except one pointer file and one unit field).
- **Rollback:** delete the cron; restore the pointer file's known string; revert the unit field.
- **Effort:** **0.5–1 day** (Aika) + 0.5 h (Tao, Clerk dashboard — may follow later).

### M0.5 — Machine-verifiable freeze
- **Goal:** a third party can prove what is running without asking us.
- **Entry criteria:** M0 pointer fix done (a freeze pointing at the wrong build is worse than none).
- **Deliverable:** `freeze-manifest.json` covering the **5 surfaces × 8 evidence types** of §2 (40 cells) + the re-derivation script + the four portal route contracts cut from the frozen build; Aika-Box clean tree fingerprint and its own rollback pointer.
- **Exit criteria:** the script exits 0 twice, ≥1 day apart, and exits non-zero when one byte of one release file is touched (self-test).
- **Risk:** low. The only trap is "freeze a moving target" — solved by freezing *after* M0's unit edit.
- **Rollback:** N/A (adds files only).
- **Effort:** **0.5–1 day**.

### M1 — Make C2 the real gate
- **Goal:** `change → C2 → acceptance → C1` becomes truthful for the identity/agent-loop stack.
- **Entry criteria:** M0.5 done (the freeze manifest names the current C1 build).
- **Deliverable:** one acceptance script (`accept-c2.sh`) that (a) applies migrations to a scratch DB, (b) runs the 10 C2 suites, (c) executes the frozen route contract against the deployed C2 services, (d) prints a result; C2 Clerk units enabled + `on-failure`; one authoritative C2 web tree (the other two quarantined); the `goaa_c2` decoy dropped or renamed; `GOAA_C2_PUBLIC_BASE_URL` set with a documented tunnel for human acceptance.
- **Exit criteria:** acceptance runs green from a clean SSH session in one command; a deliberately broken change makes it fail; rebooting C2 restores every surface.
- **Risk:** medium (C2 unit/port changes; must not touch C1).
- **Rollback:** unit files are additive edits; keep `.bak` copies **outside** the systemd directory (a `.bak` unit file inside it is still loaded — a known trap).
- **Effort:** **1.5–2.5 days**.

### M1.5 — Observability minimum
- **Goal:** the six §4.2 requirements are live on C1 (and mirrored on C2).
- **Entry criteria:** M1 (so alerts can be tested against a working staging).
- **Deliverable:** structured JSON logs + logrotate; `/health` + `/healthz` on the agent-loop API; four SMTP alerts (5xx rate, restart storms, webhook failures, backup staleness) reusing the existing SMTP channel; restart policy everywhere except a documented exception list.
- **Exit criteria:** for each of the four alerts, a deliberate fault in C2 produces exactly one mail within 5 minutes, and the mail names the service.
- **Risk:** low–medium (mail volume, log-format change).
- **Rollback:** alerts are additive; the log-format change keeps a plain-text mirror for 7 days.
- **Effort:** **1–1.5 days**.

### M2 — Identity & schema design sign-off
- **Goal:** `0007` and the eight answers in §5.3 are reviewed and frozen; **nothing applied to C1**.
- **Entry criteria:** M1.5 (so the design can be exercised in C2 with alerts watching).
- **Deliverable:** final `0007_order_identity_links` DDL + rollback script + backfill plan + review record; a written decision on the single overlapping e-mail and on how `unknown` legacy payments are treated.
- **Exit criteria:** Tao signs the DDL; the link model answers all eight questions without a rename and without moving data.
- **Risk:** low (no execution) — the real risk is design drift if implementation starts before sign-off.
- **Rollback:** N/A.
- **Effort:** **1 day** + review.

### M3 — Apply `0007` in C2 only; wire lazy linking
- **Goal:** the bridge exists and is exercised in staging.
- **Entry criteria:** M2 sign-off; M1 acceptance green.
- **Deliverable:** `0007` applied on C2 (auto-rolled-back on any test failure); Phase B lazy dual-write in the platform backend; `business_tokens` used as the session token for linked users; a C2 test that walks: Clerk dev sign-in → link created → business token → agent-loop page.
- **Exit criteria:** the C2 suite (including new link tests) is green; repeating the flow produces **no** duplicate link and **no** duplicate token; `order_identity_links` count matches the expected C2 fixture count exactly.
- **Risk:** medium (identity writes, staging only).
- **Rollback:** `0007_rollback` (drop the new objects); C2 restore — which *requires* M1's C2 backup fix.
- **Effort:** **2–3 days**.

### M4 — Stripe end-to-end in C2 (test mode)
- **Goal:** connection fee, service fee, settlement, invoice and webhook idempotency work as one chain — in staging, with test keys.
- **Entry criteria:** M3; a C2 twin of the order runtime (**this does not exist today** — creating a minimal one is an explicit entry task); webhook alerting live (M1.5).
- **Deliverable:** in C2 only: two checkout sessions per order (connection vs service), `payment_type` set explicitly, `payment_webhook_events` ledger with insert-first replay protection, a settlement row created on service-fee success and moved to `paid` only by the admin action, an invoice with owner/provider links, and a replayed-webhook test that is provably idempotent. Plus: regenerate the stale node/capability registries.
- **Exit criteria:** a scripted E2E — order → connect paid → service paid → settlement `paid|paid` → invoice — and replaying every webhook twice changes nothing but `attempts`/alert counters.
- **Risk:** medium–high (money semantics), mitigated by staging-only and by never touching C1's Stripe keys.
- **Rollback:** drop the C2 scratch DB; C1 untouched by construction.
- **Effort:** **3–5 days**.

### M5 — C1 promotion in a change window
- **Goal:** ship the frozen surfaces + the verified commerce bridge to production, reversibly.
- **Entry criteria:** M4 green; M0 backup + restore verified within 24 h; M0.5 freeze manifest current; M1.5 alerts live; a written change window and a named decision owner.
- **Deliverable:** promoted build (**with a build tarball created this time** and stored off-host), `0007` applied on C1 with a pre-migration dump, backfill of the 1–3 real links, post-deploy verification against the freeze manifest, and a rollback drill executed once for real (forward, then back).
- **Exit criteria:** production serves the frozen build with 0 divergence from the manifest; both accounts can sign in; the approved agent sees the agent portal; a rollback to `40c8546e` and forward again completes inside the window.
- **Risk:** **high** (production identity + money path) — mitigated by the M0 backup, M4 staging proof, and an executed rollback drill.
- **Rollback:** pointer back to `40c8546e`; DB restore from the M0 dump; `0007_rollback` if the schema must be removed.
- **Effort:** **1 day execution + 1 day verification**.

---

## 8. For Tao

### 8.1 CONFIRMED (proceed as Claude proposed)
1. Move the rollback baseline off `76af718`.
2. Revoke the three legacy production Clerk secret keys (dashboard first).
3. Clean up the `/root` env backups — **after** the rotation, by quarantine (`mv`), not deletion.
4. Add automatic DB backup — **but** scope it to `goaa_platform` + licence documents + private files, with an offsite copy and one restore drill.
5. Set `Restart=on-failure` on the agent-loop API (and the two C2 Clerk units).
6. `agent` keeps its licensed-human meaning; no rename, no big migration of that vocabulary.
7. The next-phase **order** (bleed → freeze → gate → observability → identity/schema → runtime chain), with the single reordering in §1.1.
8. A `0007` migration is required, additive-only, as drafted in §5.4.

### 8.2 PARTIAL (true with conditions)
1. **C2 as a hard gate** — schema and Clerk-tenant isolation are already gate-grade; the *process* is not (no automated acceptance, no promotion path, disabled-but-active units, no C2 backups, port drift). It becomes a hard gate after M1.
2. **"GitHub drift is governance, not survivability"** — true for the Clerk front-end and the agent-loop backend (D0 + relay copies exist); **false** for the 130-file commerce runtime and for `goaa_platform` data.
3. **"Revoke the old keys"** — the claim that one still answers 200 is **unverified**; only the Clerk dashboard can settle it.

### 8.3 REJECTED
1. "`www.goaa.ai` still serves the old template / legacy pricing / Chinese hero" — measured false (G-1 §6). The one remaining defect is the malformed `help@` contact link in Framer.
2. (Consequence) "public content is a launch blocker" — **it is not**; the launch blockers are §8.1 items 1–5.

### 8.4 NEEDS TAO'S DECISION
1. **`134.199.227.⟨10⟩` vs `134.199.227.⟨108⟩`** — DO panel vs measured egress. Which is the production anchor?
2. Approve **M0 execution** (dump + pointer + unit), and whether Aika executes or you do.
3. Approve **quarantine-not-delete** for the `/root` backups.
4. Approve the **survivability parallel track** (push the 13 local branches to GitHub after a 0-hit scan; snapshot `a532a66`'s runtime tree; offsite `goaa_platform` dump).
5. Approve **`0007` design-only** work (M2) and the "no execution before sign-off" rule.
6. Confirm the **M4 entry task**: build a minimal C2 twin of the commerce runtime — without it, no payment change can ever be staged.
7. Confirm whether **C2 must be publicly reachable over TLS** for human acceptance, or an ssh tunnel is acceptable.
8. Send the **truncated texts**: Golden Freeze §A item 4, and the full capability list after `Stripe checkout` in the G-2 order (the matrix is padded to 22 rows and would need a refill).

### 8.5 Recommended first real action (one, and only one)

> **Take a `goaa_platform` dump today, write it to a second location, and restore it into a scratch database to prove it.**

Rationale: it is the only action in this document that removes an **irreversible** risk; it changes nothing in production; it is the prerequisite of every later step (M0→M5 all assume the identity data can be recovered); and it costs about two hours. Everything else on the list can wait a day without changing the risk profile — this cannot.

Second action, same session if desired: **move the rollback pointer to `40c8546e…`** (5 minutes, and it is currently *wrong*, not merely stale).

---

## 9. What was NOT done, blockers, evidence index

**Deliberately not done (per the order):** no development, no code change, no migration, no deploy, no restart, no revoke, no delete, no DB write, no push, no charge. `0007` is a **text draft inside this report**; it has never been sent to a database.

**Blockers / open unknowns:**
1. Whether the three legacy Clerk keys still authenticate — Clerk dashboard only (Tao).
2. The commerce runtime has **no staging twin**, so the payment chain cannot be gated today.
3. `goaa_platform` data has no backup (M0 closes this).
4. The C2 Clerk units are disabled-but-active (M1 closes this).
5. Two order texts are truncated (Golden Freeze §A.4; the G-2 capability list).

**Evidence index (all read-only; hosts D0 / C1 / C2):**
- **C1 containers:** `goaa-postgres` (postgres:16-alpine, 5432), `goaa-openclaw` (nginx:alpine → 17879), `goaa-heartbeat` (alpine, `echo heartbeat` loop — decoration, not monitoring).
- **C1 units inspected:** `goaa-web`, `goaa-platform-api-3103`, `goaa-worker-agent`, `goaa-router`, `openclaw`, `qwenpaw`, `cloudflared`, `goaa-model-router` (inactive+disabled, duplicate of 8080), plus nginx (third-party `nginx` name only, no unit on C1).
- **C1 HTTP probes (10):** openclaw `/health` 200 / 90 B, router `/health` 200 / 278 B, router `/workers/status` 200 / 2,342 B, frontend `:3100/` 200 / 16,075 B, qwenpaw `:8088/health` 200 / 35 B, agent-loop `:3103/health` 404, `:3103/healthz` 404, `:3100/api/health` 404, `:18789/healthz` 404, `:8080/healthz` 404. OpenAPI: openclaw **110 paths**, router **28 paths**; payments-related and webhook paths enumerated in §5.
- **C1 logs:** `/var/log/goaa-platform/api-3103.log` (36,678 B, 600 root:root, live); journald persistent (**4.0 GB**); no GOAA logrotate entry.
- **C1 DBs (read-only SELECT / information_schema):** `goaa` 45 tables, `goaa_platform` 15 tables — full column inventories, row counts, payment/connect/settlement distributions, migration list, e-mail overlap test (1 of 72), token-length distributions.
- **Schema fingerprints:** commerce `goaa_order_*` 205 columns `e3901586fcb45a49`; platform `goaa_platform` 119 columns `b2e18381ca5eb7cf`; C2 `goaa_c2test` **identical** 119 columns `b2e18381ca5eb7cf`; C2 `goaa_c2` 82 columns `881ba06caab19ecc` (0 rows).
- **C2:** 6 units' restart/enable state; listeners (3100, 3101, 3103, 13102, 80, 443, 5433); `/opt/goaa-test` layout incl. 9 UI `.bak` copies; env **key names only**; Clerk key **fingerprints only**; dev-tenant issuer; 10 test suites; `tools/migrate.py`; no backups; no crontab.
- **D0:** 5 GOAA units (`goaa-local-console` + tailscale proxy, `goaa-telemetry-writer`, `goaa-worker-agent`, comfyui proxy, `qwenpaw`); 20 local-console routes; registries (`agents` 4 / `models` 4 / `skills` 5) with field shapes; node-registry v1.0.3 (5 nodes) and worker-capabilities (3 nodes, stale by 4 months); working-tree fingerprint `018d3678c803337b`; `/etc/goaa/console.env` key names.
- **Secrets:** only lengths + `sha256[0:16]` appear; no value, no prefix, no credential file name.

**Self-reported handling note (repeat of §1.2-g):** while dumping C2's env directory, one bare-value credential line reached my tool transcript because the filter only matched `NAME=value` lines. The value is **not** reproduced in this report, was never written to the relay, and never reached GitHub. Corrective rule adopted: env dumps must whitelist `^[A-Za-z_][A-Za-z0-9_]*=` and **drop** every other line.

**End of proposal — nothing executed. Awaiting Tao's decision on §8.4.**
