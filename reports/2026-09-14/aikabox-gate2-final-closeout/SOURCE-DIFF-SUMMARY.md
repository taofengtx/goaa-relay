# SOURCE DIFF SUMMARY

Candidate freeze commit `2ede799` on top of base `0d8998c` in `/home/aika/gate2-ui-wt`
(branch `gate2-ui-patch`).

| File | Change | Lines |
|---|---|---|
| `local-console/main.py` | modified | +391 / -31 |
| `local-console/project_context.py` | added | +354 |

`git diff --stat 0d8998c 2ede799` -> `2 files changed, 745 insertions(+), 31 deletions(-)`.

## What the candidate adds

**`local-console/project_context.py` (new, 12,116 bytes)**
File-backed JSON project store (no DB schema change) exposing:
`GET/POST /api/projects`, `PUT /api/projects/{id}`, `POST /api/projects/{id}/activate`,
`GET/POST /api/projects/{id}/documents` (registry only - references, no file I/O),
`GET /api/projects/tasks/all`, `POST /api/projects/tasks`.
Model fields: `project_id`, `name`, `description` (seeded empty by design),
`objective`, `stage`, `documents[]`, `chief_engineer` (single value), `selected_workers`
(`null` = all), `created_at`, `updated_at`, `status`.
Registered in `main.py` with a single `app.include_router(project_router)` line.

**`local-console/main.py` (modified, 199,078 bytes)**
- **A/B/C:** QwenPaw workspace bridge wiring, fixed-viewport layout CSS, unified
  ChatGPT-style scrollbar skin.
- **D:** Global Approval Inbox - one approvals call per worker (no N x M fan-out),
  cross-session aggregation, `From Worker` / `From Session` labels, `Open` deep-link,
  PENDING-only filtering, audit card hidden but kept in the DOM, stale removal.
- **E:** Project Context UI - project selector, single-select Chief Engineer with
  `CONFIGURED / NOT CONNECTED` honesty badge, multi-select worker scope with an `All`
  master checkbox and indeterminate state, Project Details panel, description and
  document registry panels, project-scoped session bindings.
- **F:** Final UI polish - one-line context bar
  (`Project | Chief Engineer | Project Details | Workers`), second line
  (`Session | New Session | Reload | Run Status`), unified control height `1.85rem`
  and font sizes, approval action row `Open -> Approve -> Reject` with equal
  height/width on desktop and natural wrapping on narrow widths.

## Diff artifacts

| File | Meaning |
|---|---|
| `evidence/main.py.diff.vs-base-0d8998c` | freeze commit diff for `main.py` |
| `evidence/project_context.py.diff.vs-base-0d8998c` | freeze commit diff for the new module |
| `evidence/main.py.diff.vs-golden-5188` | candidate `main.py` vs the file `:5188` currently serves (`0c78b8e8…`) |

The delta against golden is informational only: **nothing in this diff has been applied
to `:5188`.**
