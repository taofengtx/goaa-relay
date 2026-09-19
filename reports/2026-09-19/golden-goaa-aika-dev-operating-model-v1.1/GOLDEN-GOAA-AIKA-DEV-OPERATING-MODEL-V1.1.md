# GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1.1.md

# GOAA.AI / AIKA 开发体系 — GOLDEN DEVELOPMENT OPERATING MODEL
## Canonical Machine / Worker / Control-Plane Operating Model · v1.1 (GOLDEN CANDIDATE)

| Field | Value |
|---|---|
| **Golden ID** | `GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1` |
| **Document Version** | `v1.1` |
| **Golden Type** | `DEVELOPMENT_OPERATING_MODEL + DEVELOPMENT_GOVERNANCE` |
| **Owner** | Tao |
| **Authority** | `TAO_APPROVED_GOLDEN_CANDIDATE_BUILD` |
| **Control Plane** | Aika / 5188 |
| **Build Date** | 2026-09-19 (America/Los_Angeles) |
| **Build Stage** | `BUILD GOLDEN CANDIDATE + CONSISTENCY CORRECTION + MANIFEST + VERIFY` |
| **GOLDEN_STATUS** | `GOLDEN_CANDIDATE` |
| **REGISTRATION** | `PENDING_TAO_REVIEW` |
| **REMOTE_ACTIVATION** | `NOT_PERFORMED` |
| **Change Policy** | additive-only; every content change requires impact statement + Tao approval + rollback anchor + manifest update + version bump |
| **Related baselines** | relay Golden Surface Baseline v1.0 (`GOLDEN-01…GOLDEN-05`) — **compatibility reference only, NOT overwritten** |
| **Related governance** | `governance/CANONICAL-RULES.md`, `governance/AIKABOX-PROJECT-OPERATING-MODEL-v1.0.md` |

> **This document is a GOLDEN CANDIDATE.** It is the canonical description of the GOAA.ai / Aika
> development operating model. It does **not** modify the remote Golden Surface registry
> (`GOLDEN-SURFACE-MANIFEST.json` / legacy alias `GOLDEN-REGISTRY.json`), does **not** overwrite
> `GOLDEN-01…05`, and creates **no second Golden registry**. Remote registration stays
> `PENDING_TAO_REVIEW`.

---

## §0. Purpose and scope

This Golden defines **who controls, who executes, who falls back, which environment does what, how
work is approved, and which changes require a GCR** across:

- **GOAA.ai product development** (Track A)
- **Infrastructure / automation development** (Track B)
- **Aika Voice App** (Track C)

Scope is **development governance**, not product business logic. Product functionality,
Task business semantics, live stores, C1 and the remote Golden registry are all **out of scope and
unmodified** by this build.

---

## §1. Canonical identity

| Item | Canonical value |
|---|---|
| Golden ID | `GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1` |
| Version | `1.1` |
| Type | `DEVELOPMENT_OPERATING_MODEL` + `DEVELOPMENT_GOVERNANCE` |
| Owner | Tao (Human Authority) |
| Authority | `TAO_APPROVED_GOLDEN_CANDIDATE_BUILD` |
| Control Plane | Aika / 5188 |

**Identity rule — machine identity is not an OS probe.** A machine's *identity* is its canonical
name, role and responsibility. OS, toolchain and capability are **runtime attributes verified at
dispatch time**. An OS probe result must never rename, replace or negate a canonical machine
identity. (See §4 Track C / §5 Aika-2.)

---

## §2. Control plane — Aika / 5188

**Canonical:**

```
AIKA / 5188  =  CONTROL PLANE / DEVELOPMENT OS
```

Responsibilities:

- Project Management
- Chief Engineer orchestration
- Task Pool
- Worker dispatch
- Review
- Approval Inbox
- State machine
- Delivery governance
- Worker visibility

**Chief Engineer is a configurable reasoning role**, not a synonym for the control plane:

```
Chief Engineer  =  ChatGPT | Claude | Gemini | other configured CE
```

Therefore:

- **Aika / 5188 is the Control Plane** (the system that holds state, dispatch, review, approval).
- **Chief Engineer is a replaceable reasoning role** executed through the control plane.
- The two must **not** be written as mutually exclusive identities. "Chief Engineer = ChatGPT" and
  "Aika / 5188 = Control Plane" are simultaneously true statements.

Normative statement:

> *Aika 是开发体系的控制面；Chief Engineer 是可配置的推理角色；两者不是互斥身份。*

---

## §3. Execution hierarchy

| Layer | Identity | Role |
|---|---|---|
| **L0** | **TAO** | Human Authority — final approval and authorization |
| **L1** | **AIKA / 5188** | Control Plane — management, dispatch, review, approval inbox, state machine |
| **L2** | **WORKERS** | Execution — perform tasks in their assigned environment |
| **L3** | **QWENPAW / 小千** | Final Development / Runtime / Infra **Fallback** |

**Canonical principle:**

```
Aika 管理开发；Worker 执行任务；小千做最终级兜底。
```

- **小千 must not default-replace the normal 5188 workflow.** The control-plane path is primary.
- Escalation to 小千 is legitimate **only** when:

  1. 5188 cannot complete the work
  2. a Worker cannot be registered / cannot connect
  3. runtime problems
  4. service problems
  5. the Control Plane itself needs repair
  6. low-level infra / diagnostics
  7. Golden / governance repair

L3 is a **fallback of last resort**, not a parallel workflow.

> **No-bypass rule.** Under normal conditions tasks **must not bypass 5188** and be handed directly
> to 小千. The control-plane path (L1 → L2) is mandatory; L3 is entered only through the escalation
> conditions listed above.

---

## §4. Three parallel development tracks

### TRACK A — GOAA.ai PRODUCT MAINLINE

| Field | Value |
|---|---|
| Control Plane | Aika / 5188 |
| Primary Worker | `aika-core-01` = **W6** = **D0** execution worker |

Scope:

- Client AI Butler
- Matter
- Provider Connection
- Service Order
- Provider Workspace
- Admin
- GOAA Golden Flow
- Product Features

### TRACK B — INFRA / AUTOMATION

| Field | Value |
|---|---|
| Control Plane | Aika / 5188 |
| Primary Worker | **C3** = **W5** = **`do-cloud-3`** = `goaa-aika-cloud-3` |
| Fallback | QwenPAW / 小千 |

Scope:

- AUTO-MERGE-SYNC
- Webhook
- Ingress
- Worker Automation
- Runtime Automation
- Infrastructure

> **Naming correction (mandatory).** Infra worker is **`C3 / W5 / do-cloud-3`**.
> **`C3 / W3` is wrong and forbidden** — `W3 = do-cloud-1 = C1`.

### TRACK C — AIKA VOICE APP

| Field | Value |
|---|---|
| Project Control Plane | Aika / 5188 |
| Execution Worker | **AIKA-2** |
| Canonical Worker Identity | **`AIKA-2`** |
| Responsibility | **VOICE / AUDIO / APP DEVELOPMENT WORKER** |
| Platform attribute | runtime-verified (OS / Xcode / Swift / audio capability) |

Scope:

- Wake Word
- "Hi Aika"
- Audio Capture
- VAD
- STT
- TTS
- Voice Session
- Role Router
- Event Inbox
- Voice Approval
- Mobile / Desktop Voice Frontend
- Apple development capability **when available**

**Important:**

- **Aika-2 IS the original Aika-2.** The canonical identity is `AIKA-2`. No replacement identity
  (for example "Aika-Mac" or "Voice Worker") may be invented because of a current OS probe result.
- Aika-2's OS / toolchain capability **must be verified at dispatch time**, not assumed.
- **Linux, macOS and Xcode availability must never be written as machine identity.** They are
  capability attributes of the dispatch, not the worker's name.
- A required capability that is missing at dispatch time ⇒ **capability gap → escalation /
  provisioning**, never a rename.

---

## §5. Environment / worker map (canonical)

### Environments

| ID | Canonical meaning |
|---|---|
| **D0** | Development / Aika local development tier |
| **C1** | Production |
| **C2** | Staging / Test |
| **C3** | Worker Infrastructure |

### Worker numbering

| W | Machine | Environment | Address |
|---|---|---|---|
| **W1** | `aika-1` | primary coordinator (Windows 11) | tailnet node |
| **W2** | `aika-2` | secondary | `100.97.60.1` |
| **W3** | `do-cloud-1` | **C1** | `34.199.227.108` |
| **W4** | `do-cloud-2` | **C2** | `143.198.224.71` |
| **W5** | `do-cloud-3` | **C3** | `64.23.166.121` |
| **W6** | `aika-core-01` | **D0** | `100.114.37.90` |

### Aika-2

**Aika-2 is an independent Voice / App execution worker identity.**

- It is **not** an environment tier (it is not D0/C1/C2/C3).
- It is **not** addressed via the W-numbering of the cloud nodes; its worker identity is `AIKA-2`.
- Its responsibilities are **VOICE / AUDIO / APP DEVELOPMENT WORKER**.
- Its OS / toolchain / audio capability is verified **dynamically before dispatch**.

### Canonical mapping statements

```
C3 = W5 = do-cloud-3            (CANONICAL)
C3 = W3                          (FORBIDDEN — W3 = do-cloud-1 = C1)
Aika-2 = AIKA-2 (voice/apple)    (CANONICAL — identity not derived from OS)
```

---

## §6. Product role compatibility

**Golden canonical business roles:**

```
CLIENT / USER
PROVIDER
ADMIN
WORK / DEVELOPER
```

**Legacy implementations that exist today:**

| Layer | Legacy tokens |
|---|---|
| Product / order data | `customer`, `agent`, `admin` |
| Control plane (console auth) | `admin`, `provider`, `viewer` |

**This Golden v1.1 does NOT perform a rename migration.**

Canonical compatibility mapping:

| Canonical | Legacy token (allowed to remain) |
|---|---|
| `CLIENT` | `customer` |
| `PROVIDER` | `agent` |
| `ADMIN` | `admin` |
| `WORK` | `developer` / control-plane execution context |

Principles:

1. **Business semantics are expressed as `PROVIDER`.**
2. **Legacy token `agent` may continue to exist** until a future, separate **GCR migration**.
3. **Forbidden now:** renaming the DB role, renaming routes, renaming provider portals, or
   otherwise breaking Golden-03 compatibility.
4. Compatibility is **declared and frozen here**; migration is a separate change with its own GCR.

---

## §7. Voice role model

Voice canonical roles:

```
CLIENT · PROVIDER · ADMIN · WORK
```

- An account may hold a **single role** or **multiple roles**.
- Multiple roles ⇒ `Login → Role Selector → Active Role Context`.
- Role selection determines the session's active authorization context.

Voice session metadata (canonical fields):

| Field |
|---|
| `user_id` |
| `active_role` |
| `workspace_id` |
| `session_id` |
| `device_id` |

---

## §8. Universal voice event model

Applies uniformly to **CLIENT · PROVIDER · ADMIN · WORK**.

Canonical flow:

```
Backend Event
  → Event Router
    → Push
      → User Opens
        → Aika Automatically Speaks
          → AI Summary
            → User Voice Response
              → Backend Action
                → Workspace Record
```

Event types:

| Type | Meaning |
|---|---|
| `INFORMATION` | informational notice |
| `ACTION_REQUIRED` | user action needed |
| `APPROVAL_REQUIRED` | human approval needed |
| `WARNING` | degraded / risk signal |
| `CRITICAL` | urgent, high-impact |

---

## §9. Voice approval governance

**Aika may:**

- 播报 (announce)
- 总结 (summarize)
- 分析 (analyze)
- 解释风险 (explain risk)
- 解释影响 (explain impact)
- 说明 rollback
- 提醒用户 (remind)

**Aika may NOT:**

- substitute for **Human Approval**
- execute a high-risk approval on the user's behalf

Approval voice flow:

```
WHO · WHAT · WHY · IMPACT · RISK · ROLLBACK  →  HUMAN CONFIRMATION
```

Rules:

1. Every approval prompt must state **WHO / WHAT / WHY / IMPACT / RISK / ROLLBACK**.
2. **High-risk operations require an explicit confirmation phrase**, e.g.
   `确认批准` / `批准` / `确认执行`.
3. A bare `OK` / `好` / `行` **must not** trigger automatic execution of a high-risk approval.
4. Approval state is recorded in the workspace (see §8 final step).

---

## §10. C1 protection

**`C1` = PRODUCTION.**

The following require **explicit Tao authorization**:

- production deploy
- C1 source mutation
- DB destructive operation
- secret change
- auth change
- pricing change
- domain change
- rollback pointer change
- production service restart
- systemd mutation

**A Worker may never self-approve** any of the above.

---

## §11. Development flow

Canonical flow:

```
Tao
 → 5188 / Chief Engineer
  → Proposal
   → Tao Plan Approval
    → Task Pool
     → Worker
      → Task Branch
       → Code Review
        → PR
         → Integration
          → C2
           → C2 PASS
            → READY_FOR_C1
             → Tao Production Approval
              → C1
               → LIVE
                → COMPLETED
```

### Task state machine note (IMPLEMENTATION_EVOLUTION)

The live Task State Machine may contain **more gate states** than older governance documents
describe (the live control plane exposes **25** states; the legacy Operating Model v1.0 documents
**22**; the extra live states are `CODE_REVIEW`, `PROMOTION_APPROVAL_PENDING`, `NEEDS_REVISION`).

**Golden v1.1 must NOT force the live 25 states back to the documented 22.**

This is recorded as:

```
IMPLEMENTATION_EVOLUTION
```

State-machine documentation reconciliation is deferred to a **separate GCR**.

---

## §12. AUTO-MERGE-SYNC current state

| Item | State |
|---|---|
| `AUTO-MERGE-SYNC-V1` | implemented |
| **P0** | `CLOSED` |
| **Phase 3A** | `SOURCE_APPLIED_RUNTIME_LOADED_INERT` |
| **GitHub Webhook** | `NOT ACTIVE` |
| **Webhook Secret** | `ABSENT` |
| **Scheduler** | `NOT ACTIVE` |
| **Phase 3B** | `PARALLEL INFRA TRACK` |
| **Phase 3C** | `DEFERRED` |

Details:

- Phase 3A applied the trigger adapter to live source; the live runtime loaded it and it is **inert**
  (no secret, webhook fail-closed; unauthenticated access rejected).
- Phase 3B (webhook secret creation / activation) is the Track B infra work item and targets worker
  **`C3 / W5 / do-cloud-3`**.
- Phase 3C (scheduled reconciliation sweep) remains **DEFERRED** and disabled by default.

---

## §13. Current work priorities

| Priority | Work | Track | Worker / Owner | State |
|---|---|---|---|---|
| **P0** | GOAA Product Mainline | A | `aika-core-01` | `ACTIVE` |
| **P0** | Aika-2 worker registration / capability audit | C | `AIKA-2` | `NEXT` |
| **P0** | Aika Voice V1 Architecture Freeze | C | 5188 CE | `NEXT` |
| **P1** | Voice Environment Audit | C | `AIKA-2` | planned |
| **P1** | Voice Event Inbox | C | `AIKA-2` | planned |
| **P1** | Voice Approval | C | `AIKA-2` | planned |
| **P1** | AUTO-MERGE-SYNC Phase 3B | B | `C3 / W5 / do-cloud-3` | planned |
| **P2** | AUTO-MERGE-SYNC Phase 3C | B | — | `DEFERRED` |

> The Track A row reflects the live state at build time. Priorities are **planning state**, not
> authorization: each item still requires the normal approval flow (§11).

---

## §14. GCR triggers

The following changes **must** go through a GCR (impact statement + Tao approval + rollback anchor +
manifest/version update):

- Control Plane semantics
- Worker responsibility
- Environment responsibility
- C1 / C2 / C3 meaning
- Worker-number mapping
- Role semantics
- legacy `agent` / `provider` migration
- approval semantics
- human approval rules
- production permissions
- auth
- pricing
- domain
- destructive DB change
- Golden registry schema
- Voice App becoming a business truth source
- a Worker bypassing 5188 / C2 / Approval
- QwenPAW fallback semantics

---

## §15. Source references and compatibility boundaries

### A. Existing canonical governance (authoritative for governance documents)

| File | Content |
|---|---|
| `governance/CANONICAL-RULES.md` | canonical execution governance; `WORKER_INSTRUCTION_LENGTH_V1` (hard limit 10000 chars; overflow = `SPLIT_TASK`; truncation forbidden) |
| `governance/AIKABOX-PROJECT-OPERATING-MODEL-v1.0.md` | Aika-Box project operating model (status: DEFINED, NOT IMPLEMENTED) |

These documents remain authoritative for their scope. This Golden **references** them and does not
replace or rewrite them.

### B. Existing Golden surface baseline (compatibility reference only)

The relay Golden surface baseline v1.0 defines product **surfaces** `GOLDEN-01…GOLDEN-05`
(marketing / customer portal / provider portal / admin console / Aika-Box :5188) plus
`future_additions_not_golden` (D1…D6), `environment_mapping` and `canonical_role_direction`.

Rules:

- **This Golden does not overwrite any of `GOLDEN-01…05`.**
- It does not modify the remote `GOLDEN-SURFACE-MANIFEST.json` or its legacy alias
  `GOLDEN-REGISTRY.json`.
- It does not push to the relay repo or the product repo.
- It is a **development operating model / governance** baseline, a **different axis** from the
  surface baseline, and is registered separately (or not at all) by Tao's decision.
- Where this Golden and the frozen surface baseline touch the same subject (environment mapping,
  role direction), the difference is recorded as a **GCR-triggering change** (§14), not applied
  silently.

### C. Current live system evidence

| Evidence source | What it evidences |
|---|---|
| `local-console/project_context.py` | environment registry (D0 / C2 / C1 / C3), promotion tiers |
| `local-console/qwenpaw_workers.json` | live worker registry (Gate-2 MVP) |
| Task Pool / store | projects, tasks, proposals, approval records, scheduler state |
| Approval flow | plan approval, promotion approvals, delivery gates (admin session required) |
| Environment mapping | dev / test / prod / worker-infrastructure assignment |

---

## §16. Registration boundary

This round performs **BUILD GOLDEN CANDIDATE ONLY**.

Not performed:

- no modification of the remote `GOLDEN-SURFACE-MANIFEST`
- no modification of the remote `GOLDEN-REGISTRY`
- no push to the relay repo
- no push to the product repo
- no overwrite of `GOLDEN-01…05`
- no remote Golden activation
- no live Task / store modification
- no worker registry modification
- no role token rename
- no DB modification
- no C1 / C2 / C3 modification
- no restart

Output:

```
REGISTRATION = PENDING_TAO_REVIEW        (NOT "ACTIVE")
```

---

## §17. Verification

Structural and semantic verification of this candidate is recorded in
`GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1.1-VERIFY.json`, including:

- Golden ID uniqueness
- no `GOLDEN-01…05` overwrite
- `C3 = W5` mapping correctness
- Aika-2 identity preserved (no OS-derived rename)
- legacy `agent` / `customer` compatibility preserved
- no DB migration
- no product / live source mutation
- no live Task / store mutation

Integrity of the sealed candidate file set is recorded in
`GOLDEN-GOAA-AIKA-DEV-OPERATING-MODEL-V1.1-SHA256SUMS.txt`.

---

## Appendix A — Canonical mapping table

| Concept | Canonical | Legacy / note |
|---|---|---|
| Control plane | Aika / 5188 | Development OS, not a Worker |
| Chief Engineer | configurable reasoning role | ChatGPT / Claude / Gemini / other |
| Human authority | Tao | L0 |
| Fallback | QwenPAW / 小千 | L3, escalation-only |
| Track A worker | `aika-core-01` | W6 = D0 |
| Track B worker | `C3 / W5 / do-cloud-3` | infra |
| Track C worker | `AIKA-2` | voice / audio / apple development |
| Environments | D0 · C1 · C2 · C3 | development · production · staging/test · worker infrastructure |
| Business roles | CLIENT/USER · PROVIDER · ADMIN · WORK | `customer` · `agent` · `admin` (legacy, unchanged) |

## Appendix B — Corrections applied in v1.1

| # | Correction | v1.1 position |
|---|---|---|
| 1 | Infra worker naming | `C3 / W5 / do-cloud-3`; **`C3 / W3` forbidden** |
| 2 | Aika-2 identity | canonical `AIKA-2`; OS/toolchain never overrides identity; capability verified at dispatch |
| 3 | Chief Engineer vs control plane | CE is a configurable role; not mutually exclusive with Aika / 5188 |
| 4 | Role model | canonical CLIENT/PROVIDER/ADMIN/WORK with declared legacy compatibility; no rename migration |
| 5 | Task states | live 25 states recorded as `IMPLEMENTATION_EVOLUTION`; no forced downgrade to 22; separate GCR |

## Appendix C — Open items (follow-ups, not authorizations)

| ID | Item | Trigger |
|---|---|---|
| C-01 | Track C project container creation in the control plane | §14 / authorization |
| C-02 | Aika-2 worker registration + capability audit | §13 P0 |
| C-03 | Role semantics / legacy-token migration | GCR |
| C-04 | Task-state documentation reconciliation (25 vs 22) | GCR |
| C-05 | Golden registration decision (registry section vs document-only) | Tao decision |
| C-06 | Environment semantics (C3 / Track C) vs frozen surface baseline | GCR |

---

**END OF GOLDEN CANDIDATE v1.1**
**GOLDEN_STATUS = GOLDEN_CANDIDATE · REGISTRATION = PENDING_TAO_REVIEW · Memory Written = NO**
