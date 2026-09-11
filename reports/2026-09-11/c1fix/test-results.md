# Round C1 fix — test results

- Candidate commit: `718ee10935a4894b173448928bf55e707fc7d894` (718ee10)
- Applied patch: `patches/0002-round-c1-fix-goaa-portal-scope.patch` (sha256 `5a271bb84d4f179e…`, via `git am`)
- Snapshot: `snapshots/frontend-718ee109/`
- Date: 2026-09-11

## TypeScript typecheck

```
$ npx tsc --noEmit
(no output)
rc=0
```

## Front-end mock suites — scripts/test-*.cjs

Runner: `node scripts/test-<name>.cjs` (bare require resolves react-test-renderer 18.3.1
from the workspace `node_modules`, matching react 18.3.1 — single React copy, no
"Invalid hook call"). No NODE_PATH override. No test assertions or expectations modified.

```
OK   scripts/test-chat-footer-legal-links.cjs        (rc=0, PASS=4)
OK   scripts/test-client-login-dismiss.cjs           (rc=0, PASS=21)
OK   scripts/test-client-login-legal-links.cjs       (rc=0, PASS=5)
OK   scripts/test-client-login-password-toggle.cjs   (rc=0, PASS=9)
OK   scripts/test-client-logout-cal.cjs              (rc=0, PASS=13)
OK   scripts/test-customer-growth-pages.cjs          (rc=0, PASS=6)
OK   scripts/test-customer-signout.cjs               (rc=0, PASS=16)
OK   scripts/test-goaa-cookie.cjs                    (rc=0, PASS=9)
OK   scripts/test-header-login-menu.cjs              (rc=0, PASS=9)
OK   scripts/test-logo-nav.cjs                       (rc=0, PASS=7)
OK   scripts/test-matters-tabs.cjs                   (rc=0, PASS=7)
OK   scripts/test-new-matter-archive.cjs             (rc=0, PASS=12)
OK   scripts/test-order-recovery.cjs                 (rc=0, PASS=25)
OK   scripts/test-paid-ui-regressions.cjs            (rc=0, PASS=13)
OK   scripts/test-portal-preview-admin-rbac.cjs      (rc=0, PASS=14)
OK   scripts/test-portal-preview-business.cjs        (rc=0, PASS=12)
OK   scripts/test-portal-preview-content.cjs         (rc=0, PASS=10)
OK   scripts/test-portal-preview-core.cjs            (rc=0, PASS=18)
OK   scripts/test-portal-preview-isolation.cjs       (rc=0, PASS=8)
OK   scripts/test-portal-shell.cjs                   (rc=0, PASS=8)
OK   scripts/test-product-handoff.cjs                (rc=0, PASS=13)
OK   scripts/test-signout-wiring.cjs                 (rc=0, PASS=8)
OK   scripts/test-workspace-english.cjs              (rc=0, PASS=4)
========================================
TOTAL files=23 green=23 fail=0
```

- `test-portal-shell.cjs` = 8 items (as expected for the C1 fix).

## scripts/c2-clerk/run-all.sh

```
$ bash scripts/c2-clerk/run-all.sh
test-entry-rules      rc=0 :: c2 clerk entry rules: 16 passed, 0 failed
test-middleware       rc=0 :: c2 clerk middleware: 15 passed, 0 failed
test-bff              rc=0 :: c2 clerk bff: 14 passed, 0 failed
test-signout          rc=0 :: c2 clerk sign-out: 7 passed, 0 failed
test-candidate-shape  rc=0 :: c2 clerk candidate shape: 8 passed, 0 failed
test-golden-routes    rc=0 :: golden routes: 16 passed, 0 failed
test-golden-session   rc=0 :: golden session: 23 passed, 0 failed
TOTAL: 99 passed, 0 failed, group_rc=0
```
