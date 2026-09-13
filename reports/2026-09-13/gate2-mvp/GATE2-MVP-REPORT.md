# Gate-2 MVP — Aika-Box × QwenPaw AI Workspace

**Report** · 2026-09-13 · Friday (`default`) · order issued by Tao 04:56 PDT
**Box**: Expected ≤ 15 h · Hard stop 16 h — finished inside the box (no blocker).
**Verification port**: `:5198` (alternate). **Golden `:5188` untouched.**
**Change record**: `GCR-2026-09-13-AIKABOX-QWENPAW-MVP.md`

---

## 1. Deliverable

A minimal AI workspace **inside the existing Aika-Box Local Console** (`local-console/`):

> open the page → select a Worker → select/create a Session → send a message →
> streamed answer → Approve/Reject card for guarded tools → the same run continues →
> final result returns → reconnect/replay any time.

New nav entry `⚡ AI 工作區（QwenPaw）` (`#p-qwenpaw`), service side under `/api/qwenpaw/*` (13 routes,
all session-authenticated). Ten new files + additive lines in `main.py`; nothing removed or renamed.

Browser never talks to QwenPaw directly: `Browser → Local Console → adapter → Worker QwenPaw`.

## 2. Test matrix (T1–T15)

| # | Test | Result | Evidence |
|---|---|---|---|
| T1 | Send message, SSE stream | ✅ | 19 SSE events → `AIKA_QWENPAW_GATE2_T1_OK`, state `Completed` (1.0 s) |
| T2 | Session continuity (2nd turn) | ✅ | 2nd turn answered in same session; history = 4 messages, clean |
| T3 | Approve (guarded tool) | ✅ | `crontab -l` → `HIGH` card, correct session → approve → same run continued (142 SSE events) → **command really ran** (`no crontab for aika`, exit 1) |
| T4 | Reject (guarded tool) | ✅ | `crontab -l ; touch <marker>` → reject → **marker absent** (command did not run) → run continued to `Completed` |
| T5 | Reconnect / replay | ✅ | interrupt after 4 events → replay `from=0` → 36 events → `Completed`; on a finished run `POST /reconnect` → `200 run already closed` |
| T6 | `basic` flavour worker (`do-cloud-1`) | ✅ (after fix) | honest `Failed` + upstream note (`status:error`), no fake success, no stuck `Running` |
| T7 | Offline worker (`do-cloud-2`) | ✅ | `503 worker do-cloud-2 has no known QwenPaw API: ConnectError: [Errno 111] Connection refused` |
| T8 | Auth on every route | ✅ | no cookie / forged cookie → 401 on `/health`, `/workers`, `/sessions`, `/approvals`, `/audit` |
| T9 | Reconnect while a run waits for approval | ✅ | interrupt in `Waiting Approval` → reconnect `200` (1 replay), still `Reconnecting` → decision made → `Completed`; 1306 replayed SSE events, 6 state transitions; repeated assistant turns proved to be QwenPaw's own reasoning segments |
| T10 | Audit trail integrity | ✅ | JSONL append-only; rows for session create / chat send / approval decision; no secret-like material |
| T11 | Stale leftovers from the Gate-1 spike | ✅ | surfaced as `state=EXPIRED`, `clickable=false`, age reported |
| T12 | Cross-session isolation | ✅ | another session → 0 cards (`scanned_raw:1, filtered_out:1`); no session selected → 0 cards |
| T13 | UI shell (nav, page, panels) | ✅ | page renders; Worker roster with status/flavour/version/latency; audit panel; approval panel |
| T14 | No auto-decision (negative control) | ✅ | a pending card stayed untouched for 30 s+ with the run parked in `Waiting Approval`; nothing was auto-approved — decisions only happen on a click |
| T15 | Restart resilience | ✅ | after console restart: 6 local `abx-*` sessions still listed and resumable, history clean; audit file survived (17 rows: 5 session_create / 9 chat_send / 3 approval_decision at that point) |

Extra, executed through the **real browser UI** (not scripts):

| # | Test | Result | Evidence |
|---|---|---|---|
| U1 | UI end-to-end: nav → Worker → new Session → send → answer | ✅ | `shots/qwenpaw-workspace-page.png`, `shots/qwenpaw-workspace-completed.png`; `AIKA_QWENPAW_GATE2_UI_OK` echoed, state `Completed` |
| U2 | Human-in-the-loop card, **Approve** clicked in the UI | ✅ | `shots/qwenpaw-approval-card-ui.png`; audit `approve · actor=tao · source=ui-click · ok`; run `Completed`; the real `crontab -l` output came back |
| U3 | Human-in-the-loop card, **Reject** clicked in the UI | ✅ | audit `reject · actor=tao · source=ui-click · ok`; answer states the command was denied before execution |

This also closes the Gate-1 caveat: both decisions were made by **actual UI clicks** in a browser,
`source=ui-click`, not by an HTTP call on Tao's behalf.

Raw evidence: `evidence/` — `t3-send-and-continuity.json`, `t4-approve.json`, `t5-reject.json`,
`t6-reconnect-basic-offline-auth.json`, `t8-live-reconnect-resume.json`,
`t9-stale-isolation-no-auto-decision.json`, `approval-audit-decisions.json`, `code-inventory.json`.

## 3. Worker roster as seen by the workspace

| Worker | Role | Endpoint | Transport | Flavour | Status |
|---|---|---|---|---|---|
| `aika-core-01` | Aika-Box local runtime | `http://100.114.37.90:8088` | Tailscale | `console` v1.1.5.post1 | Online (~5–55 ms) |
| `do-cloud-1` | DO runtime anchor | `http://127.0.0.1:18088` | SSH tunnel | `basic` (`QwenPaw-DO` 1.0.0) | Online, **LLM backend broken** |
| `do-cloud-2` | DO worker 2 | `http://127.0.0.1:18089` | SSH tunnel | — | Offline (no listener) |
| `do-cloud-3` | DO worker 3 | `http://127.0.0.1:18090` | SSH tunnel | — | Offline (no listener) |

## 4. What was fixed while building

| Bug | Fix |
|---|---|
| Two different QwenPaw flavours (console API vs a minimal `1.0.0` wrapper with only `GET /health` + `POST /chat`) | health probe now detects and records `api_flavor: console / basic / unknown`; basic workers use a single-shot `/chat` and report failures honestly |
| Sorting mixed epoch floats with ISO strings raised `TypeError` | all timestamps normalised through one `_ts()` helper |
| A `basic` worker could sit in `Running` forever | request timeout raised; failure is finalised with the upstream note instead of pretending success |
| Pending approvals are returned globally by QwenPaw, not per session | client-side filtering on `session_id ∩ root_session_id`, de-duplication by `request_id`, newest wins, plus an `EXPIRED` state for stale entries |
| QwenPaw stores internal reasoning as extra assistant turns | display layer merges adjacent assistant turns (keeps the last) so the UI never shows reasoning drafts |
| `stop` needed the upstream chat id | stop resolves `run.chat_id or run.session_id` and lets QwenPaw resolve |

## 5. Risks reported, deliberately not changed

1. `do-cloud-1`'s QwenPaw wrapper listens on `0.0.0.⟨0⟩:8088` → publicly reachable. **Reported only.**
2. That same wrapper's LLM backend returns `{"status":"error","response":""}` after ~60 s. **Reported only.**
3. The workspace keeps runs in memory (bounded). A console restart preserves sessions and audit, but
   in-flight runs are not re-attached upstream — reconnect replays our own recorded events instead.

## 6. State of the box after this round

* Golden `:5188` **not modified, not restarted** — verified PID unchanged for the whole round.
* Verification instance on `:5198` + the four worker tunnels are the only new local processes
  (recorded with PIDs so they can be stopped on request).
* New code committed locally in `goaa-ai-main` (add-only); **no push to any code remote**, no deploy.

## 7. Next step (needs Tao's decision)

1. **Cut-over to Golden-05 `:5188`** — apply the add-only change to the live AIKA-BOX Control Center.
   This is the *only* Golden surface in scope, and it is an ADD-ONLY change, but a Golden change still
   needs Tao's explicit approval + the restart recorded (PID / unit / status / rollback).
   Until then the feature stays available on the alternate port.
2. Optional hardening, if wanted: replace the per-worker inline endpoint config with a small registry
   page, and align `do-cloud-1`'s service with the `console` flavour.
