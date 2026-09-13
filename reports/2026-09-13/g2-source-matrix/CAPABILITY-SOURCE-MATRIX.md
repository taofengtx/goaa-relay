# GOAA Capability → Source-of-Truth Matrix (G-2)

**The single deliverable of round G-2** — one core matrix, plus the seven ordered answers.

- **Round:** G-2 — GOAA Git / Relay / Production lineage verification (READ-ONLY)
- **Date:** 2026-09-13
- **Verified judgement:** Claude's "GitHub drift is a governance problem, not a survivability problem".
- **Method:** remote ref list (`git ls-remote`, 58 heads + 1 tag), local ref graph, per-ref tree/hash profiling, relay snapshot byte-diff, read-only host inspection (C1 / C2 / D0). No writes, no deploy, no restart, no DB write, no push.
- **Legend** (matrix columns):
  - **Production Present?** = code exists in the C1 (Live/Production) deployment and is reachable/serving.
  - **Relay Snapshot?** = a byte tree of that ref exists in the relay repo (`snapshots/…`).
  - **GitHub Ref?** = the ref itself is reachable from `github.com/taofengtx/goaa-ai-frontend` (any branch/tag).
  - **Migration Cost** = effort to move that capability onto a version-controlled, off-host ref.

> **Headline:** GitHub's newest commit is `76af718` (2026-09-07 03:15). **Every commit from 2026-09-08 onward is local-only**; 13 local branches have no remote ref. The Clerk / agent-loop / golden-session / growth work survives only because the D0 repo + worktrees + relay snapshots still hold it.

---

## 1. Core matrix

| # | Capability | Best Source Ref | Backup Source Ref | Production Present? | Relay Snapshot? | GitHub Ref? | Schema Dependency | Identity Model | Confidence | Migration Cost | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Clerk auth (sign-in / session / entry rules) | `feat/c2-clerk-unified-login-v1` = **`40c8546e`** (front-end: `app/lib/clerk-entry.ts`, `app/client-login`, `app/goaa-clerk-login`, `app/components/portal/clerk-appearance.ts`, `scripts/c2-clerk/*`) | relay `snapshots/frontend-40c8546e` (635/638 byte-identical) | YES | YES | **NO** | `user_identities` (mig 0005) | external Clerk tenant `clerk.goaa.ai` + local JIT mapping | HIGH | LOW | First Clerk commit = `daecc2a` (2026-09-10 20:18, 32 files); deployed BUILD_ID `FW7iufKj5JrPAz9Kx2SkX` |
| 2 | Clerk → local identity mapping (backend) | `feat/c2-pg-agent-loop-v1` = **`dc64591`** → `services/c2_agent_loop/app/clerk_auth.py` + `clerk_identity.py` | relay `snapshots/backend-dc64591b` | YES | YES | **NO** | `user_identities`, `identity_events` | external subject → local user row | HIGH | LOW | C1 deploy is byte-identical to this ref (37/37) |
| 3 | Multi-role / RBAC / role grants | `dc64591` (`app/security.py`, `tools/grant_role.py`, mig 0003 + 0004) + `40c8546e` (`app/agent-loop/*` role gating) | relay backend + frontend snapshots | YES | YES | **NO** | `user_roles`, `agent_review_events`, mig 0004 role-grant guard | local role table (2 user / 1 agent / 1 admin) | HIGH | LOW–MED | Deployed schema has all 6 migrations applied |
| 4 | Golden business session bridge | `dc64591` (`app/golden_session.py`, mig 0006) + `40c8546e` (`app/components/GoldenSessionBridge.tsx`) | relay backend + frontend snapshots | YES | YES | **NO** | `business_subjects`, `business_subject_links`, mig 0006 | Clerk session → local business context | HIGH | LOW | |
| 5 | Agent application & review | `dc64591` (mig 0002, `app/ai_review.py`, `tests/test_application_loop.py`) | relay backend snapshot | YES | YES | **NO** | `agent_applications`, `agent_licenses`, `agent_review_events` | applicant = local user + agent role | HIGH | LOW | 1 approved application, 12 review events — all created after the 09-12 17:49 rollout |
| 6 | Agent portal | `40c8546e` (`app/agent-loop/agent/*`, 5 sections) | relay frontend snapshot | YES (gated) | YES | **NO** | `agent_licenses`, `user_roles` | Clerk + agent role | HIGH | LOW | Unauthenticated request → 307 to /client-login |
| 7 | Admin portal | `40c8546e` (`app/agent-loop/admin/*`, 6 sections) | relay frontend snapshot | YES (gated) | YES | **NO** | `user_roles` admin | Clerk + admin role | HIGH | LOW | |
| 8 | Customer portal / AI Butler | `40c8546e` (`app/agent-loop/customer/*`, `app/components/Butler*.tsx`) | `76af718` (**on GitHub**) holds a pre-Clerk Butler/Matters shell | YES (gated) | YES | **NO** | matter + agent-knowledge tables | Clerk + user role | MED–HIGH | LOW | Butler content predates Clerk (Butler tokens already present at `76af718`) |
| 9 | Matters (five-tab filter / blueprint step) | `40c8546e` (`app/components/*Matter*.tsx`, ~70 files) | **`76af718` on GitHub** (`codex/login-legal-links-20260906`) | YES | YES (40c8546e only) | NO for `40c8546e`; **YES** for `76af718` baseline | matters + order stage | role-scoped | HIGH | LOW | `76af718`'s own subject = "feat(matters): five-tab filter by blueprint step and order stage" |
| 10 | Professional handoff / Connect ($39.90) | `40c8546e` (`app/components/ProfessionalHandoff*.tsx`, `MatterProfessionalConnect.tsx`) + live runtime `stripe_checkout.py` | `c5c3c48` (`feature/professional-connect-3990`, on GitHub — older lineage) | YES (code); feature gated closed | YES (front-end only) | **NO** for `40c8546e` | service orders / payments | Clerk role + matter context | MED–HIGH | MED | Live `GOAA_PAID_CONNECTION` unset ⇒ handoff stays closed; backend half is live-only (row 11) |
| 11 | **Stripe checkout — backend / golden order runtime** | **C1 live filesystem `/opt/goaa/runtime` (NO ref)** | `codex/stripe-return-urls-20260904` = **`a532a66`** (`runtime/`, 24 files; 16/18 shared files byte-match live) | YES (130 files) | **NO** | **NO** (`a532a66` is local-only; the Sep-2 capture `02a17ff` *is* on GitHub but 0/18 shared files match live) | `goaa` DB; migrations 0006–0013 live untracked in `runtime/migrations` | `goaa_order_users` (72) | MED | **HIGH** | `main.py` + `planning_engine.py` diverged after 09-04; 55 top-level files exist in no ref; contains `orders.py` (103,486 B) |
| 12 | Order payments ledger | same as row 11 (live runtime) | `goaa` DB dump 2026-09-06 (`/opt/goaa/backups/*.dump`, custom format) | YES (`goaa_order_payments` 41 rows) | NO | NO | payments / service-orders | order user | MED | HIGH | Dump predates all 09-12 activity; 39 succeeded / 2 pending |
| 13 | Invoice PDF | `a532a66:runtime/invoice_pdf.py` (byte-matches live) | C1 live copy | YES (`goaa_order_invoices` 7) | NO | NO | invoices | order user | HIGH | LOW | Single file; live == ref |
| 14 | Connect transfers / settlements (payouts) | `a532a66:runtime/stripe_checkout.py` + `stripe_pay.py` (byte-match live) | C1 live copy | YES (`goaa_order_settlements` 14) | NO | NO | settlements, transfer ids | Connect account per agent | HIGH | LOW–MED | Self-written REST client (`create_transfer` etc.), not the Stripe SDK; `CONNECTION_FEE_CENTS=3990` |
| 15 | Refunds | live `orders.py` (admin status transition only) | none | YES (state transition only) | NO | NO | payment status | admin role | MED | MED | No Stripe refund REST call found in the runtime |
| 16 | Stripe webhook handling | **live `main.py`** (newer than any ref) | `a532a66:runtime/main.py` (2026-09-04) | YES | NO | NO | payments / order events | signature-based | MED | MED | Live `main.py` mtime 2026-09-06; webhook secret lives only in host env |
| 17 | Skills marketplace | `40c8546e` (`app/agent-loop/customer/skills`, `app/agent-dashboard/skills`) | relay frontend snapshot | YES (gated) | YES | **NO** | skills tables | role-scoped | HIGH | LOW | |
| 18 | Worker dispatch / task queue | `40c8546e:workers/*` (3 tracked files) | relay front-end snapshot (no worker tree) + router :8080 lineage | YES | NO | **NO** for `40c8546e` | `tasks` (21), `tool_invocations` (21) | worker identity | MED | MED | Router itself (`/opt/goaa/router`) has no matching ref |
| 19 | **Worker agent (`agent.py`)** | **NO ref** — D0 and C1 `/opt/goaa/workers/agent.py` (identical, 5,918 B) | `services/worker-agent/agent.py` @ `origin/main` (a *different* variant) | YES (6+ workers) | NO | **NO** | none | `WORKER_ID` | LOW | MED | Its 3 sibling files *are* on GitHub and byte-match (`memory_context_fetch.py`, `rag_context_fetch.py`, `telemetry_writer.py`) |
| 20 | RAG pipeline | `services/rag/` @ `40c8546e` (61 files) | `origin/main` (same path) | YES (D0 :5188 / C2) | NO | **YES** | knowledge chunks/docs | n/a | MED–HIGH | LOW | Path unchanged since `main` |
| 21 | Model router | `services/model-router/` @ `40c8546e` (3 files) | `origin/main` | YES (router pattern) | NO | **YES** | none | n/a | MED | LOW | Production router may be a separate deployment |
| 22 | Aika-Box local console | `local-console/` @ `40c8546e` (19 files) | `origin/main` (tree identical across 5 refs) | YES (D0 :5188) | NO | **YES** | local telemetry | n/a | HIGH | LOW | |

---

## 2. What the matrix says

1. **Three families, three survival profiles.**
   - **GitHub-anchored (safe):** everything up to `76af718` (2026-09-07) — Matters baseline, Butler shell, RAG, model router, local console, and the Sep-2 runtime *capture* branch.
   - **D0-only (fragile):** all Clerk / agent-loop / golden-session / growth work (09-08 → 09-11) — 13 local branches, 0 remote refs.
   - **C1-only (fragile, no ref at all):** the golden order runtime under `/opt/goaa/runtime` (130 files) and the deployed build artifact of the current front-end release.
2. **Best ref per family:** front-end = **`40c8546e`**; agent-loop backend = **`dc64591`** → `services/c2_agent_loop/` (37 files); commerce runtime = **`a532a66`** → `runtime/` (24 files) — nearest ref, but a partial predecessor, not a reconstruction.
3. Only `dc64591` and the Clerk-era front-end have an **independent off-host copy** (relay snapshots). The commerce runtime has none.

---

## 3. The seven ordered answers

### Q1 — Can the C1 front-end be rebuilt byte-identically?

**Source: YES. Deployed artifact: NO.**

- Deployed release = `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` (symlinked from `current`); `BUILD_ID` = `FW7iufKj5JrPAz9Kx2SkX`; **1,969 files / 28,138,994 bytes**; tree fingerprint `f8efdc333f25ef7d`.
- Source ref = **`40c8546e`** (branch `feat/c2-clerk-unified-login-v1`, 2026-09-11 11:14, 638 files). Present in (a) the D0 repo (authoritative) and (b) relay `snapshots/frontend-40c8546e` — **638/638 files present, 635 byte-identical**; the 3 exceptions are C2 test scripts whose hard-coded dummy test token was redacted in the snapshot.
- The **built tree is not bit-reproducible** (Next.js build) and no archive of it exists — the three `goaa-web-*.tar.gz` files in `/opt/goaa-frontend/` cover only the 2026-09-06 releases. The only copy of the built tree is the C1 release directory itself.
- Preserved instead: a **byte manifest of the deployed tree** (relay `reports/2026-09-11/c1fix/deployed-manifest.sha256`, 2,075 entries). ⇒ rebuild can be *verified*, not *recreated byte-for-byte*.
- The rollback baseline `76af718` **is on GitHub**, and its release directory is present on disk ⇒ rollback target is doubly covered.

### Q2 — Can the C1 backend be fully rebuilt?

Two backends; they answer differently.

**(a) agent-loop API — `/opt/goaa-platform/backend` (:3103): YES, fully.**
- 37 files; every file's sha256 matches `dc64591:services/c2_agent_loop/` — **37/37 identical**. C2's copy is the same 37 files + 5 `.pyc`.
- Off-host copy: relay `snapshots/backend-dc64591b` — **byte-identical to the same git subtree**.
- Caveat: `dc64591` is a **local-only branch** ⇒ recoverable from the D0 repo + relay, **not** from a GitHub clone. (Confirms R4: deploy source = git `dc64591b`.)

**(b) golden order runtime — `/opt/goaa/runtime` (openclaw, :18789): NO.**
- The directory is **untracked**: the enclosing repo (`/opt/goaa`, remote = the front-end monorepo) sits at `1d67bd6` (2026-06-14) with 300 tracked files and **zero tracked files under `runtime/`**.
- Nearest ref = `codex/stripe-return-urls-20260904` (`a532a66`, 2026-09-04): `runtime/` has 24 files; **16 of 18 shared basenames byte-match live**. The two that do not are `main.py` and `planning_engine.py` (live is newer). **`a532a66` is itself local-only.**
- 55 of the 79 live top-level files (incl. `auth_oauth.py`, `planning_engine.py`, every `stageb_*` / `stagec_*` script, and migrations 0010–0013) exist in **no ref at all**.
- The Sep-2 capture branch `02a17ff` (`runtime/`, 23 files) *is* on GitHub — but **0 of its 18 shared files match live**.

⇒ **Composite: PARTIAL** — backend (a) rebuildable; backend (b) not.

### Q3 — Best real source ref per capability

→ Section 1. Family picks: front-end (all Clerk-era UI) = `40c8546e`; agent-loop backend = `dc64591`; Matters baseline = `76af718` (**on GitHub**); commerce runtime = live C1 filesystem (nearest ref `a532a66`); RAG / model router / local console = `origin/main` (**on GitHub**); worker agent = no ref.

### Q4 — Capabilities whose only copy is the live node (highest risk)

1. **Golden order runtime** — 130 files under `/opt/goaa/runtime`; no ref, no snapshot; nearest ref covers 16/18 shared files and is local-only.
2. **`goaa_platform` identity data** — 15 tables, single copy in the C1 Docker PostgreSQL:
   `users 2 · user_roles 4 (user 2 / agent 1 / admin 1) · user_identities 2 (provider=clerk) · identity_events 7 · agent_applications 1 (approved 1) · agent_licenses 1 · agent_license_documents 1 · business_subjects 1 · business_subject_links 1 · agent_review_events 12 · schema_migrations 6`.
   The only dumps in `/opt/goaa/backups` target DB **`goaa`** (custom format, 5,037,681 B / 5,041,599 B, 2026-09-06) and were written **before** any identity row existed (identity rows created 2026-09-12 17:49–18:22Z). **Zero identity backups.**
3. **Worker `agent.py`** (identical on D0 and C1, 5,918 B) + D0-only `task_runner.py`, `topk_query.py`, `embed_worker.py` — no ref.
4. **13 local-only branches** (all 2026-09-04 → 09-11 work) — single copy in the D0 repo/worktrees; the relay covers 9 front-end snapshots + 1 backend snapshot + 12 patches, but **not** `a532a66`'s runtime tree.
5. **The deployed front-end build tree** (`BUILD_ID FW7iuf…`, 1,969 files) — single copy on C1.
6. **Live key surfaces** (`/etc/goaa/*`, `/opt/goaa-platform/env/*`, `/opt/goaa-frontend/env/*`, `/root/clerk-live*.env`) — by design off-git; single-host copies with stale `.bak` neighbours.

### Q5 — Are Clerk auth and agent application present on GitHub?

**NO.**

- Newest commit on any GitHub ref = **`76af718`, 2026-09-07 03:15**, branch `codex/login-legal-links-20260906`; next newest `253a78c` (09-06), `013c6b2` (09-06).
- Clerk first appears at **`daecc2a`** (2026-09-10 20:18, 32 clerk files) → `51c9914` (48) → `f93c5544` (52) → `049a0a6` (53) → `9ab1608` (54) → `f719b27` (54) → `40c8546e` (54).
- Remote-containment check (`git branch -r --contains`): **0** remote refs contain `daecc2a`, `51c9914`, `f93c5544`, `049a0a6`, `9ab1608`, `f719b27`, `40c8546e`, `dc64591`, `a532a66`, `cb57fd9`, `cd54b54`, `13ecaa8`, `b8050fc`, `a7e8b1c`, `62296fa`, `d6029f63`.
- ⇒ A clean GitHub clone today yields the **pre-Clerk, pre-agent-loop, pre-growth** state.
- Off-GitHub safety net: D0 branches/worktrees + relay snapshots (`frontend-`: `daecc2a4`, `31f7676b`, `d4ad5613`, `b602bdd2`, `718ee109`, `f93c5544`, `049a0a6e`, `f719b275`, `40c8546e` — 605–638 files each; `backend-dc64591b` — 37) + `patches/0001..0012` (C1 rounds 1 → 1.9).

### Q6 — Are env secrets / credentials / env-backup files inside any ref or snapshot?

**NO.**

- **Relay:** the 18 env-like entries are `.env.example` / `.env.production.example` placeholders inside the snapshots, plus two report files that merely *describe* key names. No real key material, no credential file.
- **Git:** `origin/main` tracks only `.env.example` and `.env.production.example`. The historical `1d67bd6:.env.production` (319 B, 9 lines) contains two **public** URLs (router + openclaw) and no secrets; it was later removed by `d8ec7d0` ("chore(security): stop tracking production env and add a safe template") and survives only in 5 old refs (`preview/*` ×3, `v4-tools-ui`, tag `v5.2b-golden-r1`).
- **Live only:** `/etc/goaa/` (openclaw + secrets envs, plus 4 older backups), `/opt/goaa-platform/env/` (API env + the platform app pg credential file, 0600), `/opt/goaa-frontend/env/web.env` (0640 root:goaa-web), `/root/` (`clerk-live.env`, `clerk-live-sk.env`, `c2-api-3103.env`, and 5 `.bak` copies — web env ×3, api-3103 env ×2). **None appear in any ref or snapshot.**
- Context (from G-1): the three live surfaces carry the *current* Clerk secret; the four stale `/root/*.env.bak.*` files still carry the **previous** production Clerk secrets — revocation/cleanup awaits Tao's authorisation.

### Q7 — `goaa_platform` schema + data — refs and backups?

- **Schema: yes, ref-anchored.** Migrations `0001_identity` → `0006_golden_business_session` (+ `rollback/`) live in `dc64591:services/c2_agent_loop/migrations/`, byte-identical to the deployed C1 backend (37/37) and to relay `snapshots/backend-dc64591b`; the DB agrees (`schema_migrations` = 6, including the 0004 role-grant guard and 0006 golden session). **Not on GitHub.**
- **Data: no ref, no usable backup.** The 15-table dataset exists once, in the C1 Docker PostgreSQL. `/opt/goaa/backups/` holds only: two custom-format dumps whose embedded database name is **`goaa`** (commerce), plus one directory holding an older `orders.py` copy (102,134 B, 2026-08-31) and a small secrets snapshot (801 B). There is **no `pg_dump` cron** (root crontab has only the Regulation-47 consistency monitor, `--dry-run`).
- C2's `goaa_c2test` (users 49 / user_roles 55 / user_identities 23) is a *different* dataset — it cannot restore C1 identity state.

---

## 4. Ref-state facts (for the record)

- **GitHub:** 58 heads + 1 tag (`v5.2b-golden-r1`); newest commit 2026-09-07. `origin/main` = `00c848d` (400 files).
- **Local repo:** 56 branches; **13 have no remote ref** — `feat/c2-clerk-unified-login-v1` (`40c8546e`), `feat/c2-pg-agent-loop-v1` (`dc64591`), `feat/portal-preview-business-loop-v1` + `feat/agent-application-loop-v1` (`b8050fc`), `feat/c2-agent-application-ui-v1` (`13ecaa8`), `feat/three-portals-v1` (`cb57fd9`), `feat/three-portals-isolated-v1` (`a7e8b1c`), `feat/customer-growth-*` (`cd54b54` / `9b95a08` / `ed894ed`), `codex/login-legal-links-20260906` @ `d6029f63` (its remote branch points at the older `76af718`), `codex/stripe-return-urls-20260904` (`a532a66`), `backup-p44b-c542977`.
- **Relay snapshots:** 9 front-end refs + 1 back-end ref (5,707 files) + 12 patches.
- **C1 releases on disk:** 22 directories, including the rollback `76af718` release and the current `40c8546e` release.
- **Runtime ref ranking** (live-match on shared basenames): `codex/stripe-return-urls-20260904` — 16/18 > `chore/c1-cors-planning-origin-*` = `codex/backend-source-capture-*` (`02a17ff`) — 15/18 > `evidence/c2-implementation-*` — 12/18. None reconstructs the live 130-file runtime.
- **Local worktrees:** 40 registered; 15 carry uncommitted edits (largest: the main worktree with 8 untracked entries, all build artefacts / `*.bak` files).

## 5. What was deliberately NOT done (per the G-2 order)

No `delete / revoke / rollback-point edit / restart / deploy / DB write / merge / rebase / force push`. Nothing was pushed to GitHub. No secrets were copied, printed, or fingerprinted outside the lengths/fingerprints already recorded in G-1. This round is a pure read + compare + document pass.
