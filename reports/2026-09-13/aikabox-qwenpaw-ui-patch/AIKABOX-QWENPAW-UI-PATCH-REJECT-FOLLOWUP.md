# UI Patch §7 — Reject-path follow-up evidence (append-only)

Round: 2026-09-14 00:12 PDT · D0 / Aika-Box · instance **:5198** (tailnet `100.114.37.90:5198`)
Claim under test: **“Reject 已由 Tao 本人点击”**
Verdict: **NOT CORROBORATED — no human reject exists in any independent record.**
The reject *path* did fire, but it was fired by the worker's **300 s approval timeout (auto-deny)**, not by a click.

---

## 1. Requested checks

| # | Check | Result |
|---|---|---|
| 1 | audit decision = reject | **NOT FOUND** — 0 decision rows for the reject card; newest decision in the audit log is `23:45:37 approve` |
| 2 | run continues and completes | **PASS** — the run resumed after the denial and reached `Completed` (live run snapshot `state=Completed`, 875 SSE events) |
| 3 | `execute_shell_command` did not execute | **PASS** for the guarded call — the tool result is the denial, no stdout |
| 4 | transcript has no crontab execution result | **PASS** for the undecided attempts — only the denial + the assistant's final text; the `no crontab for aika` lines in the transcript belong to the two *approved* attempts |
| 5 | add `HUMAN REJECT = PASS` to the final evidence | **REFUSED AS UNSUPPORTED** — see §4; recorded instead as `REJECT_PATH_BEHAVIOUR = PASS` + `HUMAN_REJECT = NOT_EXERCISED` |
| 6 | relay follow-up evidence commit, append only | **DONE** — new files only, no amend, no force-push |

---

## 2. Card lifecycle (worker-side, authoritative)

```
23:45:31  Approval pending created: request_id=fae1579d  (UI-FINAL-APPROVE)  -> 23:50:31 approval timeout (300s)
23:50:39  Approval pending created: request_id=05f3fce7  (UI-FINAL-REJECT)   -> 23:55:39 approval timeout (300s)
00:04:46  Approval pending created: request_id=a0534151  (UI-FINAL-REJECT)   -> 00:09:46 approval timeout (300s)
```

No `Approval deny request` / `Approval reject request` line exists between 23:40 and 00:10.
The **only** deny in the whole worker log is `23:06:52 request 83f084d9 … reason=User denied` — the earlier
agent-era click that was already graded `TECHNICAL_PATH_PASS / HUMAN_APPROVAL_NOT_ACCEPTED`.

## 3. Four independent records, one conclusion

| Source | Finding |
|---|---|
| Console audit `/opt/goaa/run/qwenpaw_audit.jsonl` (105 rows) | 17 decisions = 10 approve / 7 reject; **newest decision = `23:45:37 approve`**; **0 decisions for `05f3fce7` and 0 for `a0534151`** |
| Console access log `/tmp/ui-logs/uvicorn-5198.log` | **exactly 1 reject POST in the instance's whole life** (`83f084d9`, loopback, 23:06 era); 6 approve POSTs; **0 reject POSTs from Tao's tailnet client** |
| Worker approval log `/home/aika/.qwenpaw/qwenpaw.log` | window 23:40–00:10: **5 approve requests, 0 reject requests, 4 approval timeouts** |
| Approvals API (`:5198`) | `05f3fce7` → `EXPIRED`, `clickable=false`, age 841 s; `a0534151` → `PENDING` → `STALE` at 00:09:47, age 300.8 s, `clickable=false` |

A card that had been clicked would show a decision POST in the access log, a `decision` row in the audit log,
and a `resolved: decision=…` line in the worker log. None of the three exist for these cards.

## 4. What is proven, and what is not

**Proven (behaviour of the deny path):**
* the guarded `execute_shell_command` call **was not executed** — the tool result is the denial text, no stdout;
* the run **did not die** on the denial: it continued and reached **`Completed`**
  (`GET /api/qwenpaw/runs/85ae6d741d51` → `state: "Completed"`, `sse_events: 875`), and the transcript ends with
  the assistant's final answer;
* the transcript contains **no `crontab -l` output for the undecided attempts**.

**Not proven:** that a **human** clicked Reject. There is no such decision anywhere. Recording
`HUMAN REJECT = PASS` would put a false acceptance line into the acceptance evidence, so it was not written.
`HUMAN_REJECT = NOT_EXERCISED` — the deny came from the 300 s TTL.

Note on the original run (`263aadfb099f`, 23:50): its in-memory run snapshot was cleared by the `:5198`
restart at 23:58 (done for the scrollbar round), so `GET /runs/263aadfb099f` answers `404 unknown run_id`.
Completion for that run is established from the transcript (denial → final answer) plus the worker's
session-save/usage-close at `23:55:44`; the identical path is demonstrated live by run `85ae6d741d51`.

## 5. Cards seeded for a genuine click (agent seeded the run only, never decided)

| request_id | session | seeded | outcome |
|---|---|---|---|
| `05f3fce7-f0bc-4d6f-90d6-4986b2f2cd00` | UI-FINAL-REJECT | 23:50:37 (run `263aadfb099f`) | TTL auto-deny 23:55:39, `EXPIRED` |
| `a0534151-1b7b-40be-932b-1f31ca30cc98` | UI-FINAL-REJECT | 00:04:46 (run `85ae6d741d51`) | TTL auto-deny 00:09:46, `STALE` |

To make `HUMAN REJECT = PASS` real: a fresh card must be seeded and clicked **inside its 300 s TTL**.
The agent will not click it (HITL rule) — the click has to come from Tao's browser.

## 6. Declarations

* No approve/reject was clicked by the agent in this round (anywhere, by any means).
* No commit was amended and no force-push was performed; this follow-up is pure append.
* Nothing on `:5188` was touched; the instance under test remains the D0 dev instance `:5198`.
