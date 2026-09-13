# GATE2-GOLDEN-CHANGE-EVIDENCE — GOLDEN-05 source fingerprint change

- Date: 2026-09-13 (PDT)
- Change id: `GCR-2026-09-13-AIKABOX-QWENPAW-MVP`
- Surface: GOLDEN-05 = D0 Aika-Box Local Console (`:5188`)
- Type: **ADD ONLY** (no deletions of existing Golden behaviour, no route removal, no role change)

---

## 1. Fingerprint

| | Value |
|---|---|
| Surface file | `local-console/main.py` |
| Previous (Golden v1.0 frozen) sha16 | `7f62dfea43d025f6` |
| Previous bytes | 138,956 |
| New (Gate-2 MVP) sha16 | `64fdc422d39a3cb9` |
| New bytes | 162,056 |
| Delta | +23,100 bytes; 420 insertions, 1 deletion |
| The single deletion | a `</script>` tag that had been overwritten during authoring (fixed) |
| Canonical manifest | `reports/2026-09-13/golden-baseline-v1/GOLDEN-SURFACE-MANIFEST.json` |

**Manifest sync status: PENDING.** The canonical manifest still records the frozen fingerprint
`7f62dfea43d025f6`. It will be updated to `64fdc422d39a3cb9` (with the old value retained in the
change history) only once the cut-over reaches a Final PASS, or once Tao accepts the change with
the two open defects recorded as known limitations.

---

## 2. Added files (all new, none pre-existing)

Verified against ref `02a17ffe`: `local-console/integrations` and `local-console/tools` each had
**0 files** before this change.

| Path | sha16 |
|---|---|
| `local-console/integrations/__init__.py` | `727f1d9f9a8b4161` |
| `local-console/integrations/qwenpaw/__init__.py` | `2d0dc48da2cebaf0` |
| `local-console/integrations/qwenpaw/models.py` | `cb42871faba584cc` |
| `local-console/integrations/qwenpaw/client.py` | `b175783d7cf081f2` |
| `local-console/integrations/qwenpaw/events.py` | `81598b0a256e3001` |
| `local-console/integrations/qwenpaw/sessions.py` | `f1d1ad034e7df3c4` |
| `local-console/integrations/qwenpaw/approvals.py` | `3d907e0f59148aa7` |
| `local-console/qwenpaw_api.py` | `88962ccdf4ace723` |
| `local-console/qwenpaw_workers.json` | `c6b139343796b1de` |
| `local-console/tools/start_qwenpaw_tunnels.sh` | `b77a8739dcb40ef0` |

Runtime state (not in the repo): audit log and session snapshot under the console run directory.

---

## 3. Modified file

`local-console/main.py` — additive only:

- include the QwenPaw API router (prefix `/api/qwenpaw`)
- one navigation entry
- one page container (`#p-qwenpaw`)
- one inline script block implementing the AI Workspace UI

No existing route, response shape, nav item, or handler was removed or renamed.

---

## 4. What did NOT change

- GOLDEN-01 / 02 / 03 / 04 — UNCHANGED
- C1 (Live) and C2 (Test) — NO CHANGE
- Database — NO MIGRATION
- systemd unit and drop-in — NO CHANGE (unit sha256 `dd9572d95116a7dc…`, drop-in sha16 `6fab895d84668204`)
- Proxy / tunnel configuration — NO CHANGE
- Auth behaviour — NO CHANGE

---

## 5. Open defects at the time of writing

1. **Duplicate QwenPaw script block** — the same ~10.2 KB block was appended to both HTML templates;
   the stray copy on the login template throws at load. Index page itself is clean.
2. **Session history not restored in the UI** — the adapter endpoint works but the UI never calls it.

See `evidence/js-duplication-diagnosis.json` and `evidence/session-history-ui-diagnosis.json`.
