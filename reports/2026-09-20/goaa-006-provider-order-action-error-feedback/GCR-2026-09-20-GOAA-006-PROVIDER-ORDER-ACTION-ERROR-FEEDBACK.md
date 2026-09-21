# GCR-2026-09-20-GOAA-006-PROVIDER-ORDER-ACTION-ERROR-FEEDBACK

**Change Record** · GOAA.ai · Provider Service Order Workspace — Action Error Feedback Completion

> Registered under Golden ID **`GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1`** (version in effect **`v1.1`**).
> Registration is **purely additive**: no Golden-artifact byte, Golden semantics, Golden version,
> product code, or Task state was changed by this registration. See §11.

| Field | Value |
|---|---|
| GCR ID | `GCR-2026-09-20-GOAA-006-PROVIDER-ORDER-ACTION-ERROR-FEEDBACK` |
| Date | 2026-09-20 (PDT) |
| Issued by | Tao (human, GCR-registration order — GOVERNANCE ONLY) |
| Prepared by | AIKA control plane (5188) `aika-box-console` session `UI-FINAL-HUMAN-REJECT` |
| Source draft | `GOAA-006-GCR-DRAFT.md` (sha256 `45ece52fcf91aa93e4ff325483f7218f84f6c1d87da09b75fa002b2dc832a137`, 3,659 B) |
| Target Golden | `GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1` (v1.1) |
| Related Golden surface | GOLDEN-04 / GOLDEN-05 (provider-side console surface family) — **surface baseline untouched** |
| Change type | **ADD-ONLY / COMPATIBILITY-PRESERVING** (frontend-only) |
| Status | **REGISTERED (local registry record) · PROMOTION_READY = YES** |
| Registration authority | `TAO_EXPLICIT_APPROVAL` |
| Registration mode | `LOCAL_ONLY_NO_PUSH` (Tao instruction: do not push) |

---

## 1. Why

The Provider Service Order Workspace (`app/agent-order-live/page.tsx`, GOAA.ai frontend) drives
five provider actions — **Start Service / Send to Customer / Request Information / Upload Delivery
Files / Submit Delivery Package** — through one shared runner, `run()`.

Before GOAA-006, `run()` was a `try/finally` with **no `catch`**: an action failure produced **no
user-visible feedback**, could leak an **unhandled Promise rejection**, and any `runtime.refresh()`
failure was equally invisible — i.e. the operator could not tell a failed action from a successful
one. This is an operator-trust/observability gap inside an existing surface, not a feature change.

## 2. Current state (before) — verified

| Item | Value |
|---|---|
| Integration head | `a43f32cbd52267c07417a0d09b1587ad842c5143` (`integration/goaa-mainline`) |
| File (base) | `app/agent-order-live/page.tsx` · sha256 `fc3e517ab3212b62c25afdc6494d6717bf8cceb92b3392414b39067da8dc2c1f` · 117 lines |
| Runner | `run()` at L44 = `try/finally`, **no `catch`** |
| User-visible action failure feedback | **absent** |
| Refresh-failure feedback | **absent** |

## 3. Registered state (after) — verified final candidate

| Item | Value |
|---|---|
| File (candidate) | `app/agent-order-live/page.tsx` · sha256 `31946aaad354ed84cb95022f3ea6d94a0b9d59d2605b93f5f956ff3a5bda4a62` · 21,875 B / 120 lines |
| Diff | **1 file changed, 8 insertions(+), 5 deletions(-)** · sha256 `18cad11a19c6a46ee536af7a7d2e7588a7c1f3c8a73ea23f6166b112b49489d5` (18,762 B) |
| Hunks (U0) | `@@ -44 +44,4 @@` · `@@ -95 +98 @@` · `@@ -97,3 +100,3 @@` (only original L44, L95, L97–99) |
| Mechanism | scoped `actionError` state + `ACTION_LABEL` map + `actionApiMessage()` + failure-clears-old-error / action-catch-returns-before-refresh / refresh-catch-fallback; 4 DOM render points (`data-goaa-action-error` = `start` / `supplement` / `{actionError.scope}` (upload+delivery) / `message`) covering all 5 actions |
| New error system / dependency / visual system | **NONE** (reuses the existing `const error=` style established by GOAA-005) |

## 4. Compatibility matrix (verified)

| Dimension | Change |
|---|---|
| Files | `app/agent-order-live/page.tsx` — **1 file** |
| Routes / API paths | **NO CHANGE** |
| API contract | **NO** |
| DB / migration | **NO** |
| AUTH | **NO** |
| PAYMENT / pricing | **NO** |
| ROLE semantic change | **NO** |
| DOMAIN change | **NO** |
| DESTRUCTIVE change | **NO** |
| DEPLOY change | **NO** |
| BACKEND change | **NO** |
| Golden Flow state machine / stage transitions | **NO CHANGE** |
| Existing correct handlers (`Send Estimate`, `Confirm Documents Complete`) | **NO CHANGE** — byte-identical (base L69–88 vs candidate L72–91, sha256 `5ce3f5de…`) |

## 5. Verification evidence (read-only review)

| Evidence | Value |
|---|---|
| Static gates | `TSC_EXIT=0` · `LINT_EXIT=0` · `BUILD_EXIT=0` (`/agent-order-live 6.05 kB`) |
| Behaviour matrix | **42 / 42 PASS** + 1 documented gap (canonical evidence sha256 `490fb5ae9ef41cd5cece0adad57c61807b9e2ff3e22af66deed93ab51d733aad`) |
| Code review | **CODE_REVIEW = PASS** · `SCOPE_CHECK = PASS` · `REGRESSION_CHECK = PASS` · `ADD-ONLY content-level = PASS` · `BLOCKERS = NONE` |
| `PROMOTION_READY` | **YES** |
| Recorded gap | `GOAA-006-REFRESH-ERROR-SURFACE` — on the `start / ok + refresh failure` path the refresh failure is surfaced through the runtime badge rather than a new action-error row; accepted by Tao as a **documented gap, not a blocker** |

## 6. Documented gap (explicit, non-blocking)

`DOCUMENTED_GAP = GOAA-006-REFRESH-ERROR-SURFACE`
`REFRESH_FAILURE_USER_VISIBLE = YES` · `ACTION_ERROR_REFRESH_BRANCH_REACHABLE = NO`
No second file was added for this branch (Tao decision: do not expand scope beyond the single file).

## 7. Rollback

Revert the **single GOAA-006 commit** on `worker/aika-core-01/GOAA-006` (`app/agent-order-live/page.tsx`
only; base `a43f32cb…` / file `fc3e517a…`). No data, contract, or infrastructure rollback required.
Rollback anchor type: **git revert of a one-file frontend commit**.

## 8. Acceptance (AC1–AC10)

AC1 visible feedback for all 5 actions on failure · AC2 no unhandled rejection from those actions ·
AC3 busy state recovers · AC4 no false success-state update on failure · AC5 success path still
refreshes · AC6 `Send Estimate` no regression · AC7 `Confirm Documents Complete` no regression ·
AC8 existing stage logic unchanged · AC9 frontend-only scope (1 file) · AC10 minimal diff
(+8 / −5) — **all satisfied** (AC5 verified via observable DOM re-read of server state).

## 9. Golden-impact statement (§14 assessment)

Against Golden §14 (`GCR triggers`): this change touches **none** of the listed triggers — it is not
Control-Plane / Worker-responsibility / environment / C1-C2-C3 / role / auth / pricing / domain /
DB-destructive / registry-schema / Voice / approval / QwenPaw-fallback semantics. It is an
**additive, compatibility-preserving frontend change inside an existing surface**, registered
against Golden `GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1` **because Tao required a GCR** for it.

**Golden artifacts are byte-identical after registration**: `GOLDEN-SURFACE-MANIFEST.json`
sha256 `e05a7a28134160a070de7541dab0862cc8b38247957f916b2d8b91cd9222ed5a` (pre = post),
`GOLDEN-CHANGE-POLICY.md` sha256 `6d4055afb3fa34e9c12eb81f1d97a1a2dacedb2f97db182d74c4bfada5553eb0`
(pre = post). `GOLDEN_ID_MUTATED = NO` · `GOLDEN_VERSION_BUMP = NO` · `SCHEMA_CHANGE = NONE`.

## 10. Governance boundary (what registration did NOT do)

```
PRODUCT_CODE_MODIFIED   = NO
TASK_STATE_MODIFIED     = NO
GOLDEN_SEMANTICS_CHANGED= NO
GOLDEN_ARTIFACT_CHANGED = NO
tsconfig.tsbuildinfo    = NOT TOUCHED
PUSH                    = NO
MERGE                   = NO
DEPLOY                  = NO
PROMOTION_APPROVED      = NO
```

## 11. Process fields

```
GCR_REQUIRED        = YES
GCR_TYPE            = ADD-ONLY / COMPATIBILITY-PRESERVING FRONTEND CHANGE
GCR_STATUS          = REGISTERED
GCR_REGISTERED      = YES
GCR_ID              = GCR-2026-09-20-GOAA-006-PROVIDER-ORDER-ACTION-ERROR-FEEDBACK
GOLDEN_ID           = GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1
GOLDEN_VERSION      = v1.1
GOLDEN_ID_MUTATED   = NO
GOLDEN_VERSION_BUMP = NO
FILES_CHANGED       = app/agent-order-live/page.tsx
DIFF                = 1 file changed, 8 insertions(+), 5 deletions(-)
BACKEND_CHANGE      = NO
DB_CHANGE           = NO
AUTH_CHANGE         = NO
PAYMENT_CHANGE      = NO
API_CONTRACT_CHANGE = NO
ROLE_CHANGE         = NO
DOMAIN_CHANGE       = NO
DESTRUCTIVE_CHANGE  = NO
DEPLOY_CHANGE       = NO
DOCUMENTED_GAP      = GOAA-006-REFRESH-ERROR-SURFACE
CODE_REVIEW         = PASS
PROMOTION_READY     = YES
TASK_STATE_CHANGED  = NO
Memory Written      = NO
```

**Machine-readable twin of this record:** `GCR-2026-09-20-GOAA-006-REGISTRATION-EVIDENCE.json`
(same directory).
