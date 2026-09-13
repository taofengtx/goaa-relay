# GCR-2026-09-13-AIKABOX-QWENPAW-MVP

**Change Record** · Aika-Box Local Console × QwenPaw AI Workspace (Gate-2 MVP)

| Field | Value |
|---|---|
| GCR ID | `GCR-2026-09-13-AIKABOX-QWENPAW-MVP` |
| Date | 2026-09-13 (PDT) |
| Issued by | Tao (Gate-2 MVP order, 04:56) |
| Prepared by | Friday (`default` agent) |
| Target Golden surface | **GOLDEN-05 only** — Aika-Box Control Center (`:5188`) |
| Change type | **ADD ONLY** (no delete, no rename, no route removal, no schema/auth/pricing change) |
| Status | **BUILT + VERIFIED on alternate port `:5198` · GO-LIVE ON `:5188` = NOT YET APPLIED (awaiting Tao approval)** |
| Affected surfaces 01–04 | **NONE** |

---

## 1. Why

Gate-1 (relay `b934c8c`) proved the link
`Aika-Box :5199 → QwenPaw → Send Message (SSE) → tool_guard approval → bridge capture → decision → same run continues → result returns`
over QwenPaw's native REST (`GET /api/console/push-messages`, `POST /api/approval/{approve,deny}`).

Gate-2 turns that verified spike into a **daily-usable minimal AI workspace inside Aika-Box**, so a human can
open one page, pick a Worker, pick a Session, chat, and answer Approve/Reject cards — without touching
QwenPaw directly.

## 2. Architecture (mandatory, as ordered)

```text
Browser → Aika-Box :5188 (Local Console, FastAPI)
        → server-side QwenPaw adapter  (/api/qwenpaw/*)
        → selected Worker QwenPaw      (console flavour: SSE + approvals; basic flavour: single-shot /chat)
```

* Browser → QwenPaw **direct is not used**. All traffic is proxied server-side, so no worker endpoint,
  token, or QwenPaw host is exposed to the browser.
* Aika-Box manages **Worker → QwenPaw only**. OpenClaw / ComfyUI / Skills / Ollama / browser-executor /
  coding-executor remain owned by each Worker's own QwenPaw and are **out of scope** this round.

## 3. Delta (add-only)

### 3.1 New files (10)

| File | sha256[0:16] | Lines |
|---|---|---|
| `local-console/qwenpaw_api.py` | `88962ccdf4ace723` | — |
| `local-console/qwenpaw_workers.json` | `c6b139343796b1de` | — |
| `local-console/integrations/__init__.py` | `727f1d9f9a8b4161` | — |
| `local-console/integrations/qwenpaw/__init__.py` | `2d0dc48da2cebaf0` | — |
| `local-console/integrations/qwenpaw/models.py` | `cb42871faba584cc` | — |
| `local-console/integrations/qwenpaw/client.py` | `b175783d7cf081f2` | — |
| `local-console/integrations/qwenpaw/events.py` | `81598b0a256e3001` | — |
| `local-console/integrations/qwenpaw/sessions.py` | `f1d1ad034e7df3c4` | — |
| `local-console/integrations/qwenpaw/approvals.py` | `3d907e0f59148aa7` | — |
| `local-console/tools/start_qwenpaw_tunnels.sh` | `b77a8739dcb40ef0` | — |

Full inventory (bytes/lines/hashes): `evidence/code-inventory.json`.

### 3.2 Modified file (1) — additive lines only

| File | sha256[0:16] (after) | What changed |
|---|---|---|
| `local-console/main.py` | `64fdc422d39a3cb9` | +4 integration lines (router import + `include_router`), 1 nav link, 1 page `<div id="p-qwenpaw">`, 1 `navTitle` key, 1 self-contained `<script>` block |

No existing route, page, handler, template, cookie name, auth rule, DB schema, price or nav item was
removed or renamed. Existing pages (`overview`, `workspace`, `taskpool`, `health`, `finance`, `stepper`,
`memory`, `logs`, `settings`, `cloud`) are untouched.

### 3.3 New HTTP endpoints — `prefix /api/qwenpaw`, 13 routes

`GET /health` · `GET /workers` · `POST /workers/{id}/probe` · `GET /sessions` · `POST /sessions` ·
`GET /sessions/{sid}` · `POST /chat` · `GET /runs/{rid}` · `GET /runs/{rid}/stream?from=` (SSE) ·
`POST /runs/{rid}/reconnect` · `POST /runs/{rid}/stop` · `GET /approvals` ·
`POST /approvals/{request_id}/approve|deny` · `GET /audit`.

**All routes require an authenticated Local Console session** (existing `goaa_console_session` cookie,
verified through the existing `auth.verify_session`). No new auth mechanism, no token in the browser.

### 3.4 New runtime files (outside the repo, no git pollution)

| Path | Purpose |
|---|---|
| `/opt/goaa/run/qwenpaw_sessions.json` | local session snapshot (survives console restart) |
| `/opt/goaa/run/qwenpaw_audit.jsonl` | append-only approval/action audit (JSONL, redacted, truncated) |

Both paths are overridable by env (`QWENPAW_SESSIONS_FILE`, `QWENPAW_AUDIT_LOG`).

### 3.5 New outbound dependencies (read-only toward workers)

| Worker | Endpoint | Transport | Flavour |
|---|---|---|---|
| `aika-core-01` (Aika-Box local runtime) | `http://100.114.37.90:8088` | Tailscale | `console` (v1.1.5.post1) |
| `do-cloud-1` (DO runtime anchor) | `http://127.0.0.1:18088` | SSH tunnel | `basic` (`QwenPaw-DO` 1.0.0) |
| `do-cloud-2` | `http://127.0.0.1:18089` | SSH tunnel | none (offline) |
| `do-cloud-3` | `http://127.0.0.1:18090` | SSH tunnel | none (offline) |

Tunnels are created idempotently by `tools/start_qwenpaw_tunnels.sh` (`ssh -f -N -L`).
**No worker configuration was modified by this change.**

## 4. Impact analysis on Golden 01–04 (C1 production)

| Surface | Impact |
|---|---|
| GOLDEN-01 `www.goaa.ai` | none — no Framer/CMS/HTML change |
| GOLDEN-02 User Portal | none — no BFF/route/env change |
| GOLDEN-03 Provider Portal | none — no worker `agent.py`, no role/rename |
| GOLDEN-04 Admin Console | none |
| C1 / C2 workers | none — read-only HTTP GET/POST to QwenPaw; no deploy, no restart, no schema, no secret rotation |
| Payments / auth / pricing | none |

## 5. Verification (before go-live)

Test matrix T1–T15 executed on **alternate port `:5198`** with a locally issued console session cookie.
Golden `:5188` was **not** restarted or modified during verification (its `MainPID` stayed unchanged).
Results summary: `GATE2-MVP-REPORT.md`; raw evidence: `evidence/`.

Notable proof points:

* **T3/T4** — `crontab -l` raised `HIGH / TOOL_CMD_SYSTEM_TAMPERING`; card rendered with the correct
  session; Approve → command really executed (`no crontab for aika`, exit 1); Reject → command really
  did not run (marker file absent).
* **T5/T9** — reconnect = replay of our own run store (`GET /runs/{id}/stream?from=`); a run interrupted
  while waiting for approval resumed on the same run after the decision, with no extra upstream turn.
* **T7** — no auto-approval anywhere: a pending card stayed `PENDING` for its whole TTL with the run
  parked in *Waiting Approval*.
* **T8** — every `/api/qwenpaw/*` route returns 401 without a valid console session (also with a forged
  cookie).
* **T15** — after a console restart, local sessions were still listed and resumable; the audit trail
  survived; audit rows contain no secret-like material.
* **UI E2E** — the whole flow (open page → pick Worker → new Session → send → card → click Approve /
  Reject → result) was executed through the real browser UI; both decisions were made by **actual UI
  clicks** (audit `source=ui-click`), which also removes the Gate-1 caveat that decisions had been
  submitted on Tao's behalf over HTTP.

## 6. Risks carried into go-live

1. `do-cloud-1` exposes a QwenPaw-flavoured service on `0.0.0.⟨0⟩:8088` (reported, **not changed** by this GCR).
2. The same `do-cloud-1` service accepted `POST /chat` but returned `{"status":"error","response":""}`
   after ~60 s — its LLM backend looks broken. The adapter therefore reports `Failed` with the upstream
   note (never a fake success).
3. `do-cloud-2` / `do-cloud-3` have no QwenPaw listener → shown `Offline`, chat returns `503` with the
   upstream reason.
4. Approval cards are scoped to the selected session using `session_id ∩ root_session_id`; a pending
   request can only be surfaced once (newest wins).
5. The workspace is a single-process, in-memory run store (bounded: 200 runs / 5000 events per run).
   Restart keeps sessions + audit, but in-flight runs are not re-attached to upstream.

## 7. Rollback

* Code: single local commit, add-only → `git revert <sha>` (or `git reset --hard <parent>`), then restart
  the console. No data migration to undo.
* Runtime: `rm /opt/goaa/run/qwenpaw_audit.jsonl /opt/goaa/run/qwenpaw_sessions.json` (audit history is
  the only local state; export first if needed).
* Tunnels: `pkill -f 'ssh -f -N -L 1808'` (idempotent start script recreates them).
* Golden `:5188`: nothing was changed, therefore nothing to roll back.

## 8. Approval

| Step | State |
|---|---|
| Build (add-only) | ✅ done |
| Verify on alternate port | ✅ T1–T15 (see report) |
| Secret scan / BOM check | ✅ 0 hits, BOM absent |
| **Apply to Golden-05 `:5188` (restart local console)** | ⛔ **NOT APPLIED — awaiting Tao approval** |

Per the standing Golden rule, changing GOLDEN-05 content requires this GCR **and** Tao's explicit
approval; the only permitted restart path is the D0 Aika-Box local console, with PID / unit / status /
rollback recorded.
