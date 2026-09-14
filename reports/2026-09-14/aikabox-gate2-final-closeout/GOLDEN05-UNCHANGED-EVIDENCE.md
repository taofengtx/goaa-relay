# GOLDEN-05 UNCHANGED EVIDENCE

Golden surface: **GOLDEN-05 = Aika-Box Control Center**, `http://127.0.0.1:5188/`
(tailnet `http://100.114.37.90:5188/`).

## 1. Service state (read-only)

| Property | Value |
|---|---|
| `ActiveState` / `SubState` | `active` / `running` |
| `MainPID` | `2457759` (same process as the pre-round baseline) |
| `NRestarts` | `2` (same) |
| `ActiveEnterTimestamp` | `Sun 2026-09-13 20:58:15 PDT` (same - no restart this round) |
| Unit file | `/etc/systemd/system/goaa-local-console.service` |
| Drop-in | `/etc/systemd/system/goaa-local-console.service.d/override.conf` (WorkingDirectory -> repo dir) |

## 2. Fingerprints

| Artifact | sha256 | vs baseline |
|---|---|---|
| `local-console/main.py` | `0c78b8e83516613a45b648331e90e07e64e02a034add55aac2920a3a7eb7364e` | UNCHANGED (152,687 bytes, mtime 2026-09-13 20:58:10 PDT) |
| `local-console/auth.py` | `9665e8d069bca4c87fd59f0534374c082f65a5b58c567b9d7116a4a760e32f14` | UNCHANGED |
| unit `goaa-local-console.service` | `dd9572d95116a7dc11abf1fc749689f21a073b8b40113d1192d095ce212f02e1` | UNCHANGED |
| drop-in `override.conf` | `6fab895d84668204e6dd91beb2cf66869d4a65bb725c540e6efaa3e1bfa0f37c` | UNCHANGED |

`local-console/project_context.py` does **not** exist under the golden working
directory - the Project Context module was never applied to `:5188`.

## 3. No-write proof

- `find /home/aika/Projects/goaa-ai-main/local-console -newermt "2026-09-14 00:00"`
  returns **no files**: nothing in the golden source tree was written today.
- The golden git repo `/home/aika/Projects/goaa-ai-main` (branch
  `codex/backend-source-capture-20260902`, HEAD `301b8ea`) shows **no tracked file
  modified**; its only untracked entries are pre-existing `*.bak` files for the
  roadmap docs and `__pycache__` directories, none created by this round.
- The candidate never runs from the golden directory: `:5188` serves
  `/home/aika/Projects/goaa-ai-main/local-console`, while the candidate runs from
  `/home/aika/gate2-ui-wt/local-console` on port `:5198` only.

## 4. Baseline reconciliation

Two fingerprints appear in older relay documentation for this surface and must not be
confused:

| Value | Meaning |
|---|---|
| `7f62dfea43d025f6` (138,956 B) | frozen registry v1.0 value, **pre** Gate-2 cutover |
| `0c78b8e83516613a` (152,687 B) | value currently served by `:5188`, recorded as the Gate-2 baseline in all Gate-2 reports |

The live baseline for this closeout is `0c78b8e83516613a`. The canonical manifest
`reports/2026-09-13/golden-baseline-v1/GOLDEN-SURFACE-MANIFEST.json` still carries the
older frozen value; that sync was already marked PENDING in
`GATE2-GOLDEN-CHANGE-EVIDENCE.md` and is not changed by this round.

`5188 Changed = NO`.
