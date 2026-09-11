# Round C1.3 (segment A) — test results

Date: 2026-09-11

## Frontend patch application (A2)

Tree: `/home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910`
Branch: `feat/c2-clerk-unified-login-v1`

- HEAD before apply: `b602bdd2556143ff6ba7330bd858304459a5b770`
- HEAD after apply:  `d4ad5613ce03914fa4a4c8de741942bff153a7f8`

Three patches applied in order with `git am` (all clean, no conflicts):

| Patch | New commit sha | Subject |
| --- | --- | --- |
| 0004-round-c1-3a-golden-header-sync.patch | `819b77fc756681ca7b042199e05316d663e89be2` | round C1.3a: golden header re-syncs when the bridge starts a session in this tab |
| 0005-round-c1-3b-brand-layer-outfit.patch | `a7fec0e8dc3c1b6e3c1b690908d60cea99dbfae0` | round C1.3b: one brand layer in Outfit for the portal and golden /planning |
| 0006-round-c1-3c-root-layout-dynamic.patch | `d4ad5613ce03914fa4a4c8de741942bff153a7f8` | round C1.3c: root layout is never prerendered (Clerk switch is a runtime decision) |

## Checks (A3)

1. `npx tsc --noEmit` — **zero errors**.
2. `for f in scripts/test-*.cjs; do node "$f"; done` — **27 files, 27 passed, 0 failed**.
3. `bash scripts/c2-clerk/run-all.sh` — **99 passed, 0 failed** (group_rc=0).
   - test-entry-rules: 16 passed, 0 failed
   - test-middleware: 15 passed, 0 failed
   - test-bff: 14 passed, 0 failed
   - test-signout: 7 passed, 0 failed
   - test-candidate-shape: 8 passed, 0 failed
   - test-golden-routes: 16 passed, 0 failed
   - test-golden-session: 23 passed, 0 failed

## Snapshot (A4)

Tool: `tools/make-frontend-snapshot.sh` (ran successfully).

- Snapshot path: `/tmp/goaa-relay/snapshots/frontend-d4ad5613`
- File count: **632**

### Redaction locations (relay copy only; file:line, `sk_test_` fixtures)

7 occurrences redacted:

- scripts/c2-clerk/test-middleware.mjs:15
- scripts/c2-clerk/test-middleware.mjs:80
- scripts/c2-clerk/test-golden-routes.mjs:23
- scripts/c2-clerk/test-golden-routes.mjs:291
- scripts/c2-clerk/test-entry-rules.mjs:28
- scripts/c2-clerk/test-bff.mjs:13
- scripts/c2-clerk/test-bff.mjs:63

### Secret scan

- Scan matches: **19** — all known false positives (`services/rag/*redact*`, their tests,
  `local-console/tests/*`, and `docs/`). No `sk_test_` / live-key material remains in the snapshot.

## Relay bookkeeping (A1)

- Relay HEAD before pull: `ed93971030bed18664b7db42bc80e346699e5660`
- Relay HEAD after "relay: move round c1.3 patches" (pushed): `e38e3bbf5adc7f07f624d85293efbd8b46b68108`
- Patch sha256 verified before move, after `git mv` into `patches/`, all three unchanged and matching expected.
