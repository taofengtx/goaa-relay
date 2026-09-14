# Aika-Box · Global Approval Inbox — dev candidate + verification

**Environment:** D0 (Aika-Box local development) · dev instance `:5198` **only**
**Golden instance `:5188` : NOT touched, NOT modified, NOT restarted**
**Date:** 2026-09-14 (PDT) · **Author:** QwenPaw agent (default)
**Status:** candidate built + verified on `:5198` — **awaiting Tao's decision on whether to promote to `:5188`**

---

## 0. Deliverable artifact

| Item | Value |
|---|---|
| Candidate file | `/home/aika/gate2-ui-wt/local-console/main.py` |
| Candidate hash | `sha256[0:16] = 5763464caa9bbf88` (172,821 B) |
| Pre-change state (this round) | `deea05988031b503` (161,285 B) = worktree commit `29bd973` (scrollbar round) |
| Delta (this round) | **+255 / −39** — `global-approval-inbox.diff` (364 lines, `sha256[0:16] = d6c4b4b1d0254031`) |
| Delta vs Golden baseline | +403 / −50 — `main.py.diff.vs-golden` (vs `0c78b8e83516613a`, i.e. what `:5188` currently serves) |
| Patch scripts (auditable) | `patch/gi4-patch.py` (CSS+HTML+JS, patch 1), `patch/gi7-grouping.py` (grouping fix, patch 2) |
| Worktree / branch | `/home/aika/gate2-ui-wt`, branch `gate2-ui-patch` |
| Running dev process | PID `2494507`, `uvicorn main:app --host 100.114.37.90 --port 5198`, health `200` |

Hash chain: `deea05988031b503` → *(patch 1)* → `b8d0c8431e4c23c2` → *(patch 2: grouping fix)* → **`5763464caa9bbf88`**.

---

## 1. Order → implementation map

| Order | Implementation | Anchor |
|---|---|---|
| ① Hide the audit right-hand card (UI only; do **not** delete audit data / API / write logic) | The card stays in the DOM, gets `hidden` + `.qp-audit-off{display:none!important}`. `loadAudit()` still runs on every cycle and on reload — `GET /api/qwenpaw/audit?limit=20` was still observed on the wire. | CSS L1420, HTML L1626 |
| ② Approval becomes a **global inbox** aggregating all registered workers + all sessions (`state=PENDING ∧ clickable=true`) | `refreshInbox()` (2 s interval) → per console-flavoured worker: `GET /sessions` (10 s cache) then **one** `GET /approvals` carrying *all* session ids. Header shows `⚠ APPROVAL · 全局 Inbox（需人工點擊）` + `Pending: N`. Session picker is **not** required. | JS L2191–2233, header L1623 |
| ③ Every card shows its origin | `.qp-from` with `From Worker: <worker name>` / `Session: <session id>`, plus worker group header `<display name> · <worker_id> · <n> pending` | JS L2234–2299, L2218+ |

Non-console workers (`api_flavor != "console"`) are skipped and contribute no approval calls.

---

## 2. Endpoint + call model (measured, not assumed)

* `GET /api/qwenpaw/approvals?worker_id=<id>&session_id=<a>&session_id=<b>…`
  With **no** `session_id` the server returns 0 rows (server-side `collect_pending`: `if wanted and …`).
  ⇒ the client therefore does *sessions first, then one approvals call with every session id*. **No N×M fan-out.**
* `POST /api/qwenpaw/approvals/{request_id}/{approve|reject}` body `{worker_id, session_id}` — unchanged from the existing implementation.
* `GET /api/qwenpaw/sessions?worker_id=<id>` — cached 10 s client-side.
* `GET /api/qwenpaw/workers` — cached; note it does **not** re-read the workers config file server-side.

**Measured polling cost** (12 s window, instrumented `window.fetch`, 41 sessions known for `aika-core-01`):

| Call | Count / 12 s |
|---|---|
| `GET /approvals` | **6** (one per 2 s cycle) |
| `GET /sessions` | **1** (10 s cache) |
| `GET /workers` | **0** (cached) |
| `POST` decisions | **0** |
| total | ≈ 0.58 req/s for the whole inbox |

⇒ request rate depends on the number of **console-flavoured workers**, not on the number of sessions.

**Known bound (flagged, not fixed):** the approvals URL carries every session id as a query parameter — 41 sessions ⇒ 1,459 B URL; ~500 sessions ⇒ ~17 KB. A one-line server-side change (empty `session_id` ⇒ all) would remove this, but that would alter the existing approvals semantics, so it was **deliberately not done** this round.

---

## 3. Test matrix (re-run on `5763464caa9bbf88`, dev `:5198`, desktop 1440×813 unless stated)

| # | Test | Result | Measurement / evidence |
|---|---|---|---|
| G1 | Global aggregation without picking a session | ✅ | `Pending: 2`, 2 cards, 0 session selection needed |
| G2 | Cards come from **different sessions** | ✅ | `UI-FINAL-REJECT` + `UI-FINAL-APPROVE` in one inbox |
| G3 | Origin label | ✅ | `From Worker: aika-core-01` / `Session: UI-FINAL-REJECT` |
| G4 | Worker group header | ✅ | `Aika-Box (local runtime) · aika-core-01 · 2 pending` |
| G5 | Per-card actions | ✅ | 3 buttons per card: `Approve`, `Reject`, `Open` |
| G6 | Ordering (severity → shortest TTL first) | ✅ | TTL-left ascending `188s → 189s`; verified across 100 cards too (see G16) |
| G7 | `Open` switches worker+session | ✅ | Before: `#qp-session = UI-FINAL-REJECT`, log 5,614 chars → after clicking Open on the **other** card: `UI-FINAL-APPROVE`, log **changed to 2,079 chars**, header `⌨ QwenPaw · aika-core-01 · UI-FINAL-APPROVE` |
| G8 | Chat auto-scrolls to latest | ✅ | `scrollTop + clientHeight ≥ scrollHeight − 4` after load |
| G9 | Only the opened card is highlighted; inbox untouched | ✅ | `hl = [4daeab3b…]` only; inbox still 2 cards / `Pending: 2` |
| G10 | Decision click success path | ✅ (mock) | Card → `qp-done-reject`, label `✗ Rejected`, `Pending: 100 → 99`, group header `50 → 49 pending` |
| G11 | Card removed after decision | ✅ (mock) | node gone after ~1.7 s; DOM 99 cards |
| G12 | Expired / non-clickable cards are excluded — **automatically** | ✅ | At 00:24:48 (TTL expiry 00:24:32): inbox self-cleared to 0 cards, `Pending: 0` (`qp-zero`), text `目前無待決策。`; server side both requests `STALE / clickable=false` |
| G13 | No cross-wiring to the selected session | ✅ (mock) | POST hit `/approvals/…0016/reject` with body `{"worker_id":"do-cloud-1","session_id":"MOCK-A-016"}` = **the card's own** source (the currently selected worker was `aika-core-01`) |
| G14 | Audit hidden, data/API untouched | ✅ | `hidden=true`, `display:none`, `#qp-audit` still receiving rows; `GET /api/qwenpaw/audit?limit=20` still on the wire |
| G15 | Layout regression (desktop) | ✅ | `documentElement.scrollHeight 813 = viewport 813`, horizontal overflow `0`, inbox has its own scrollbar |
| G16 | Scale (100 pending cards, 2 console workers) | ✅ | 100 cards, `Pending: 100`, 2 group headers, group sizes 50/50, **no interleaved headers** (pattern `H C C C …`), per-group severity+TTL ordering holds, page does not overflow |
| G17 | Polling cost model | ✅ | see §2 (6 approvals + 1 sessions calls / 12 s, 0 decisions) |
| G18 | Console cleanliness | ✅ | only `/favicon.ico` 404 — pre-existing on `:5188` as well |
| G19 | Narrow viewport 420×900 | ✅ | doc = viewport (420×900), overflow 0, inbox 394×142, audit `display:none` + `offsetParent === null` |

---

## 4. Bug found and fixed during this round

**Symptom (found by G16 with two workers):** with more than one console worker, the second worker's group never appeared — cards were flattened into one list and a header was only emitted when the worker id changed between adjacent cards, which silently swallowed a group.

**Cause:** global sort + "insert header on worker change" (the second worker's segment could be unreachable / merged).

**Fix (patch 2, `gi7-grouping.py`):** group by worker **first** (each worker = one independent group, group order by its most-urgent card), then order cards inside a group (severity → shortest TTL left → oldest). Re-verified by G16 on the current artifact, and G1–G9 re-passed afterwards.

---

## 5. Server-side cross-check — zero real decisions were made in this round

| Check | Before | After |
|---|---|---|
| `:5198` access log `POST /approvals/*/approve` | 6 | **6** (unchanged) |
| `:5198` access log `POST /approvals/*/reject` | 1 | **1** (unchanged — the pre-existing `127.0.0.1` call at 23:06:52) |
| audit JSONL rows | 108 | **108** — 26 `session_create`, 64 `chat_send`, 17 `approval_decision`, 1 `run_reconnect` |
| audit last decision | 2026-09-13T23:45:37 approve `2014471c` | **unchanged**, and file mtime is `00:19:30` (before verification started) |
| audit write path | — | untouched and still exercised (audit GETs observed in the page) |

⇒ All decision-path tests (G10/G11/G13) were performed with an intercepted `window.fetch` + mock response: they prove URL/body construction, card state, count bookkeeping and removal, **and that no HTTP request left the browser**. No human Approve/Reject was performed by the agent on any real card (HITL constraint respected).

---

## 6. Honest limitations

1. **No second *real* console worker exists on `:5198`.** `do-cloud-1` is `basic` flavour and `do-cloud-2/3` are `auto`/offline, so the multi-worker inbox (G16) was verified against a **mocked** `/workers` + `/sessions` + `/approvals` response feeding the real `refreshInbox`/`renderInbox` code path — not against a second live QwenPaw. Adding a real second console worker requires a server restart (the `/workers` endpoint does not re-read the config), which was not in scope.
2. **The real `POST` path was not re-exercised this round.** Wiring was verified with a mocked response; the genuine approve/reject HTTP path was proven earlier on this same code family (round 1: real `approve` click by Tao, real `reject` auto-deny on TTL).
3. **DOM measurements only.** This model has no image input, so every visual claim above is a DOM geometry/computed-style measurement. The PNGs in `shots/` are attachments for human review, not the basis of any claim.
4. **Test IDs G1–G19 are this session's own numbering.** The 00:13 order text was truncated in transit at the point `From Worker: aika-core-01  Session: UI-FINAL-REJEC…`; if the original order listed differently-defined IDs, please re-send the full text and this matrix will be re-mapped.
5. **Audit data is still produced and still written** — consistent with the order. Where it should surface (log history / Approval History) was explicitly out of scope this round.

---

## 7. Not deployed / rollback

* `:5188` (Golden): `main.py` still `0c78b8e83516613a`, health 200, same MainPID — **no write, no restart, no config change**.
* `:5198`: candidate only; the previous artifact is recoverable as `deea05988031b503` (worktree commit `29bd973`) — patch 1+2 are reversible by restoring that file.
* No database writes, no config/secret changes, no service enable/disable in this round.

## 8. Open items for Tao

1. Promote to `:5188`? (candidate `5763464caa9bbf88`)
2. Optional server-side aggregation improvement (empty `session_id` ⇒ all) — removes the growing-URL bound in §2. Needs approval because it changes existing approvals semantics.
3. Where the hidden audit should eventually live (Approval History / log view).
