# GOVERNANCE CORRECTIONS — Aika-Box Gate-2 closeout

## 1. Correction of record: A10 / A11

During the approval-button round, the `Approve` and `Reject` buttons were exercised by
**Aika via browser automation**. The decision endpoint recorded `actor=tao`, because the
console session belongs to the operator identity. **This is a logged-in identity, not
proof of a human click.**

Corrected record:

```
A10 Approve = TECHNICAL_PATH_PASS / HUMAN_APPROVAL_NOT_ACCEPTED
A11 Reject  = TECHNICAL_PATH_PASS / HUMAN_APPROVAL_NOT_ACCEPTED
```

Forbidden phrasings (must not appear anywhere in Gate-2 reporting):

- `Human Approve PASS`
- `Human Reject PASS`
- any citation of the automated clicks as Tao human-approval evidence
- any inference of human action from `actor=tao`

Allowed status vocabulary for this closeout:

`PASS`, `FAIL`, `TECHNICAL_PATH_PASS`, `HUMAN_APPROVAL_NOT_ACCEPTED`,
`NOT_APPLICABLE`, `NOT_RETESTED_THIS_CLOSEOUT`.

A technical test from an earlier round is never upgraded to a human PASS.

## 2. Standing prohibitions for Aika (effective from the correction round)

Aika must not:

- click `Approve` or `Reject` (UI or browser automation),
- call any approve/reject HTTP/API endpoint,
- use a script to approve or reject,
- simulate Tao in any way,
- infer a human click from `actor=tao`,
- infer authorization from historical precedent.

Any **real PENDING approval** must be displayed to Tao, after which Aika stops.
Human approval/rejection is performed by Tao personally in the UI.

## 3. Current acceptance state

| Item | State |
|---|---|
| Approve technical path | PASS |
| Reject technical path | PASS |
| Human approve accepted | NO |
| Human reject accepted | NO (deferred to Tao, next round) |
| Ready for Golden-05 cutover | NO |

## 4. Evidence hygiene

The audit trail entries from the automated clicks
(`request_id 33c11ebf-…` approve, `request_id 2d5dc02e-…` reject, both with `actor=tao`)
remain in the local audit log as technical-path evidence only. They are **not** to be
counted as human decisions, and the approvals they resolved were agent-generated test
requests, not real operator work.
