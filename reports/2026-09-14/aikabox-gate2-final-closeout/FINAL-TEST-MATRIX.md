# FINAL TEST MATRIX - Aika-Box Gate-2

Status vocabulary (only these are used):
`PASS`, `FAIL`, `TECHNICAL_PATH_PASS`, `HUMAN_APPROVAL_NOT_ACCEPTED`,
`NOT_APPLICABLE`, `NOT_RETESTED_THIS_CLOSEOUT`.

Closeout action column states whether the capability was re-executed during this
closeout round. Items not re-executed keep their previous status and cite the artifact
they came from; nothing was upgraded, and no technical result is presented as a human one.

| # | Capability | Status | Evidence | Closeout action |
|---|---|---|---|---|
| 1 | QwenPaw bridge - worker discovery | PASS | `2026-09-13/gate2-mvp/*`, live `:5198` worker list (4 registered, 2 online) | NOT_RETESTED_THIS_CLOSEOUT |
| 2 | QwenPaw bridge - session create / switch | PASS | `2026-09-13/gate2-mvp/*`, Project rounds E/L | NOT_RETESTED_THIS_CLOSEOUT |
| 3 | QwenPaw bridge - history load | PASS | `2026-09-13/gate2-mvp/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 4 | QwenPaw bridge - SSE streaming | PASS | Project round L8 (`Run Status: sse 0 -> Completed`) | NOT_RETESTED_THIS_CLOSEOUT |
| 5 | QwenPaw bridge - server-side adapter | PASS | `2026-09-13/gate2-mvp/*` (`integrations/qwenpaw/*`) | NOT_RETESTED_THIS_CLOSEOUT |
| 6 | Auth-protected access (session cookie) | PASS | `2026-09-13/gate2-mvp/*`; `require_session` on all `/api/qwenpaw/*` routes | NOT_RETESTED_THIS_CLOSEOUT |
| 7 | Approval capture (PENDING only) | PASS | `2026-09-14/aikabox-global-approval-inbox/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 8 | Open deep-link | PASS | A9 executed 2026-09-14: highlight applied, header/session switched, history loaded, card still PENDING | re-executed (by automation, technical path) |
| 9 | Approve technical path | TECHNICAL_PATH_PASS | A10 executed 2026-09-14 by automation; audit `decision=approve, rid 33c11ebf-…`; run continued to a second request | re-executed (technical path only) |
| 10 | Reject technical path | TECHNICAL_PATH_PASS | A11 executed 2026-09-14 by automation; audit `decision=reject, rid 2d5dc02e-…`; run ended `Completed` | re-executed (technical path only) |
| 11 | Human approve | HUMAN_APPROVAL_NOT_ACCEPTED | automated click is not human evidence (`actor=tao` = login identity) | NOT_APPLICABLE_THIS_ROUND |
| 12 | Human reject | HUMAN_APPROVAL_NOT_ACCEPTED | deferred to Tao, next round, in the UI | NOT_APPLICABLE_THIS_ROUND |
| 13 | Global Approval Inbox - cross-session aggregation | PASS | `2026-09-14/aikabox-global-approval-inbox/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 14 | Global Approval Inbox - From Worker / Session labels | PASS | same | NOT_RETESTED_THIS_CLOSEOUT |
| 15 | Global Approval Inbox - audit card hidden, DOM kept | PASS | same | NOT_RETESTED_THIS_CLOSEOUT |
| 16 | Global Approval Inbox - stale removal, no N x M polling | PASS | same (one approvals call per worker) | NOT_RETESTED_THIS_CLOSEOUT |
| 17 | Project Context - project entity / switching | PASS | Project rounds 1-4 (local DOM assertions) | NOT_RETESTED_THIS_CLOSEOUT |
| 18 | Project Context - single-select Chief Engineer | PASS | Project rounds 1-4; `CONFIGURED / Not Yet Bound` honesty badge | NOT_RETESTED_THIS_CLOSEOUT |
| 19 | Worker scope multi-select + All / indeterminate | PASS | Project rounds 2-4 (0/4, 2/4 indeterminate, 4/4) | NOT_RETESTED_THIS_CLOSEOUT |
| 20 | Project Details / Description / Documents registry | PASS | Project round 2 (registry only, no file I/O) | NOT_RETESTED_THIS_CLOSEOUT |
| 21 | Project isolation / session inheritance | PASS | Project rounds 1-4 (per-project bindings, scope-switch re-pick) | NOT_RETESTED_THIS_CLOSEOUT |
| 22 | Fixed AI workspace - sticky composer | PASS | `2026-09-13/gate2-mvp/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 23 | Fixed AI workspace - long message collapse | PASS | `2026-09-13/gate2-mvp/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 24 | Fixed AI workspace - 100+ message history / independent scroll | PASS | `2026-09-13/gate2-mvp/*` (long-history scroll verification) | NOT_RETESTED_THIS_CLOSEOUT |
| 25 | Unified ChatGPT-style scrollbar | PASS | `2026-09-13/aikabox-qwenpaw-scrollbar-css/*` | NOT_RETESTED_THIS_CLOSEOUT |
| 26 | Final UI - one-line context bar | PASS | Project round 4 + round 5 polish (1440 rows=1, 1024 rows=1) | NOT_RETESTED_THIS_CLOSEOUT |
| 27 | Final UI - Session second line unchanged | PASS | Project rounds 3-5 | NOT_RETESTED_THIS_CLOSEOUT |
| 28 | Approval action row `Open -> Approve -> Reject` | PASS | Approval-button round: DOM order, equal height 35.2px, equal width 88.8px, gap 8px | NOT_RETESTED_THIS_CLOSEOUT |
| 29 | Responsive 1440 / 1024 / narrow wrap | PASS | Project round 4/5 + approval row at 1024 wrapping naturally | NOT_RETESTED_THIS_CLOSEOUT |
| 30 | No horizontal overflow | PASS | measured at 1440 / 1024 / 620 / 560 / 380 (`scrollWidth == clientWidth`) | NOT_RETESTED_THIS_CLOSEOUT |
| 31 | `:5188` unchanged | PASS | `GOLDEN05-UNCHANGED-EVIDENCE.md` (hashes + service state + no file written today) | re-verified read-only this closeout |
| 32 | C1 / C2 untouched | PASS | no access, no command issued against `/opt/goaa` or `do-c2` this round | re-verified (no-op) |
| 33 | DB schema change | NOT_APPLICABLE | project store is file-backed JSON; no migration was written | NOT_RETESTED_THIS_CLOSEOUT |

Notes:

- Row 11/12 must never be re-rendered as `PASS` on the basis of the automated clicks.
- Rows that were not re-executed keep the status of their original round and are not
  re-scored in this closeout.
