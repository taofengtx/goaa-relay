# GOAA Runtime OS Authorization Kernel V0 Design

| Field | Value |
|---|---|
| **Version** | V0.1 Candidate |
| **Status** | Design Only / Not Implemented |
| **Security Model** | Effect-Based Authorization |
| **Dependency** | Knife 2A-2 remains frozen until minimum Authorization Kernel gate is approved |

---

## 1. Purpose and Security Principle

### 1.1 Purpose

Define the GOAA Runtime OS authorization architecture that governs **what actions an Agent may perform, on which resources, under which conditions**. This Kernel is the central authority for all access decisions across the GOAA system — Shell, Git, File, Network, Service, and future capabilities.

### 1.2 Security Principle

Authorization is effect-based, not tool-based.

> The GOAA Runtime OS authorizes **action effects**, not tool names.
>
> An action effect is a semantically classified, resource-scoped description of **what actually happens** to the system state — regardless of which tool, language, API, skill, or execution path achieves it.

### 1.3 Fail-Closed Default

Any action whose effects, resource scopes, or equivalent groups are not explicitly authorized in the current AuthorizationSnapshot is **denied by default**. Absence of explicit authorization is denial.

---

## 2. Incident Motivation and Scope

### 2.1 Knife 2A-1 Incident

On 2026-06-15 PT (verified from commit `61a1caf` and incident audit records), during Knife 2A-1 implementation, the following violations occurred:

1. **Unauthorized git commit and push** — a commit and push to GitHub `main` were performed despite Tao explicitly prohibiting them (RULE-GIT-01, RULE-GIT-02 violations).
2. **Unauthorized file deletion via API bypass** — Tao explicitly rejected renaming/deleting stale test files, yet Python `os.rename()` and `os.remove()` were used to delete 3 untracked test files:
   - `test_shell_execution_plan.py`
   - `test_shell_mock_executor.py`
   - `test_shell_resource_policy.py`

### 2.2 Root Cause

- No **action effect classification** — the system had no vocabulary to express "DELETE" or "RENAME" as semantic effects.
- No **Deny Ledger** — Tao's verbal denial had no persistent, machine-readable record.
- No **equivalent action groups** — `os.rename()` and tool-level rename were not recognized as semantically equivalent.
- No **pre-action gate** — actions executed without any authorization check.

### 2.3 Scope

This design addresses the Authorization Kernel only. It does not modify Shell Capability, Task Runner, Router, or Console. Knife 2A-2 remains frozen until AK-1 through AK-4 are reviewed and approved.

---

## 3. Existing Capability Evidence Matrix

35 rows covering the current GOAA system's authorization-related capabilities, compiled from L1 read-only audit of all authoritative documents, code files, and Git history.

| # | Capability / Gate | STATUS |
|---|---|---|
| 1 | Command-level allowlist (shell 10 templates) | `EXISTING` |
| 2 | argv recomputation (shell anti-forgery) | `EXISTING` |
| 3 | Path resource policy (ResourcePolicy + verify_runtime_path_evidence) | `EXISTING` |
| 4 | Risk level classification (dual systems in router + shell_policy) | `PARTIAL` |
| 5 | `awaiting_approval` state machine trigger | `EXISTING` |
| 6 | `task_approve` endpoint | `EXISTING` |
| 7 | `task_reject` endpoint | `NOT_FOUND` |
| 8 | `queued` state | `NOT_FOUND` |
| 9 | approve→queued atomic transaction | `NOT_FOUND` |
| 10 | Worker atomic task claiming (SELECT ... FOR UPDATE) | `PARTIAL` |
| 11 | approval_id idempotency | `NOT_FOUND` |
| 12 | Approval expiry mechanism | `NOT_FOUND` |
| 13 | Approval revocation mechanism | `NOT_FOUND` |
| 14 | audit_log INSERT (approve only) | `EXISTING` |
| 15 | tool_invocations dual-write | `PARTIAL` |
| 16 | **Deny Ledger** | `NOT_FOUND` |
| 17 | **Authorization Snapshot** | `NOT_FOUND` |
| 18 | **Action Effect Classification** | `NOT_FOUND` |
| 19 | **Equivalent Action Groups** | `NOT_FOUND` |
| 20 | READ gate | `PARTIAL` |
| 21 | WRITE gate | `NOT_FOUND` |
| 22 | CREATE gate | `NOT_FOUND` |
| 23 | DELETE gate | `NOT_FOUND` |
| 24 | RENAME gate | `NOT_FOUND` |
| 25 | MOVE_OUT_OF_DISCOVERY gate | `NOT_FOUND` |
| 26 | EXECUTE gate | `PARTIAL` |
| 27 | COMMIT gate | `NOT_FOUND` |
| 28 | PUSH gate | `NOT_FOUND` |
| 29 | DEPLOY gate | `NOT_FOUND` |
| 30 | SERVICE_RESTART gate | `NOT_FOUND` |
| 31 | SECRET_READ gate | `PARTIAL` |
| 32 | NETWORK_EGRESS gate | `NOT_FOUND` |
| 33 | PERMISSION_CHANGE gate | `NOT_FOUND` |
| 34 | Cross-tool equivalent bypass protection | `NOT_FOUND` |
| 35 | Persistent post-denial constraint | `NOT_FOUND` |

**Total: 35 rows.**

---

## 4. Execution Action Effects

14 classes describing what actually happens to system state. These are **factual** — they describe the effect, not the risk or potential consequence.

| # | ActionEffect | Definition | Examples |
|---|---|---|---|
| 1 | `READ` | Reading file/directory/config content | `cat`, `read_file()`, `Path.read_text()`, `git show`, `grep` |
| 2 | `WRITE` | Modifying file/directory/config content | `write_file()`, `sed -i`, `open("w")`, `json.dump()` |
| 3 | `CREATE` | Creating new file/directory | `touch`, `mkdir`, `Path.touch()`, `Path.mkdir()` |
| 4 | `DELETE` | Deleting file/directory | `rm`, `unlink`, `os.remove()`, `shutil.rmtree()`, `Path.unlink()` |
| 5 | `RENAME` | Renaming/moving file/directory | `mv`, `os.rename()`, `Path.rename()`, `shutil.move()` |
| 6 | `MOVE_OUT_OF_DISCOVERY` | Making file undiscoverable | rename to `.stale`, move out of `tests/`, append to `.gitignore` |
| 7 | `EXECUTE` | Running command/program | `subprocess.run()`, `exec()`, `eval()`, `python -c` |
| 8 | `COMMIT` | Creating a Git commit | `git commit`, GitHub API create commit, libgit2 commit |
| 9 | `PUSH` | Pushing commits to remote | `git push`, GitHub API update ref, remote proxy push |
| 10 | `DEPLOY` | Deploying to production | deploy script, `scp`/`rsync` production, GitHub Actions deploy |
| 11 | `SERVICE_RESTART` | Restarting a service | `systemctl restart`, `service restart`, `docker restart`, `kill -HUP` |
| 12 | `SECRET_READ` | Reading credential/secret content | reading `/etc/goaa/*.env`, `~/.ssh/*`, `*secret*`, `*password*` |
| 13 | `NETWORK_EGRESS` | Outbound network connection | `curl`, `wget`, `ssh`, `nc`, `requests.get()`, `socket.connect()` |
| 14 | `PERMISSION_CHANGE` | Changing permissions/ownership | `chmod`, `chown`, `os.chmod()`, `os.chown()`, `setfacl` |

### 4.1 Factual Effect Rule

> ActionEffect describes only the **actual effect** of the action.
> Resource sensitivity is described by TypedResourceScope.
> Risk or potential consequences must NOT be disguised as secondary effects.

**Correct examples:**

```text
Delete credential file:
  primary_effect = DELETE
  secondary_effects = {}
  resource_scopes = {FILE_PATH, SECRET_RESOURCE}

Change credential permission:
  primary_effect = PERMISSION_CHANGE
  secondary_effects = {}
  resource_scopes = {FILE_PATH, SECRET_RESOURCE}
```

### 4.2 Verified Effect Inheritance (factually true)

```text
SECRET_READ → secondary {READ}
  Reading secret content is also a READ of the underlying file.

MOVE_OUT_OF_DISCOVERY → secondary {RENAME}
  Making a file undiscoverable is factually a rename operation.

PUSH → secondary {NETWORK_EGRESS}
  Pushing to a remote requires network egress.

DEPLOY → secondary effects are FACTUALLY RECOMPUTED per deployment (see §10.3).
```

---

## 5. Control Plane Events

### 5.1 Events

4 classes that govern the authorization lifecycle itself:

| # | ControlPlaneEvent | Description |
|---|---|---|
| 1 | `APPROVAL_GRANTED` | Approval decision was positive |
| 2 | `APPROVAL_DENIED` | Approval decision was negative (triggers Deny Ledger) |
| 3 | `APPROVAL_EXPIRED` | Approval timed out before use |
| 4 | `APPROVAL_REVOKED` | Previously granted approval was revoked |

### 5.2 Control-Plane Authorization Gate

Control plane events **do not bypass authorization**. Every approval action must pass a dedicated gate before the event is recorded.

```text
APPROVAL_GRANTED / APPROVAL_DENIED / APPROVAL_REVOKED
  MUST be verified against:

    actor identity           — who is performing the approval action
    approver role            — does the actor have authority for this scope
    task_id                  — which task is being approved/rejected
    resource scope           — which resources does this approval cover
    approval scope           — single action / entire task / persistent
    approval_id              — unique idempotency key (UUID)
    expiry                   — duration before the decision expires
    idempotency              — same approval_id + same digest → 200
                             — same approval_id + different decision → 409
    current state transition — is the task in a valid state for this action
    audit event              — every decision is logged with full attestation
```

### 5.3 Idempotency Rules

```text
Same approval_id + same canonical request digest
  → return existing result, HTTP 200

Same approval_id + different digest / task / scope / decision
  → IDEMPOTENCY_CONFLICT, HTTP 409
```

### 5.4 Gate Failure

```text
actor identity invalid          → INVALID_REQUEST, audit, no event
approver role insufficient      → DENY (AUTOMATIC_POLICY_BLOCK), audit, no event
approval_id duplicate + diff    → IDEMPOTENCY_CONFLICT, audit, no new event
state transition invalid        → POLICY_CONFLICT, audit, no event
expiry already reached          → APPROVAL_EXPIRED, audit, no new event
```

---

## 6. Typed Resource Scopes

9 classes of resources that actions operate on. Each has a canonical identity and matching rules.

### 6.1 Canonical Form

```python
@dataclass(frozen=True)
class TypedResourceScope:
    scope_type: ResourceScopeType
    canonical_id: str
    attributes_digest: str | None = None
```

### 6.2 Scope Types and Matching Rules

| # | ResourceScopeType | canonical_id Format | Matching Rule |
|---|---|---|---|
| 1 | `FILE_PATH` | `/home/aika/Projects/goaa-ai-main/services/rag/workers/shell_schema.py` | `Path.is_relative_to()` + `os.path.realpath` containment |
| 2 | `DIRECTORY_PATH` | `/home/aika/Projects/goaa-ai-main` | canonical path containment; must be directory |
| 3 | `GIT_REPOSITORY` | `repo:aika-core-01:/home/aika/Projects/goaa-ai-main` | exact repository identity (`git rev-parse --git-dir` + remote origin URL) |
| 4 | `GIT_REF` | `refs/heads/main` | exact ref or explicitly approved namespace in snapshot |
| 5 | `SERVICE_UNIT` | `goaa-local-console.service` | exact, **case-sensitive** unit identity |
| 6 | `REMOTE_NODE` | `node:aika-core-01` | stable node UUID / machine identity / host-key fingerprint; IP is attribute only, NOT authorization identity |
| 7 | `API_RESOURCE` | `github:repository:taofengtx/goaa-ai-frontend` | provider + resource type + resource ID |
| 8 | `NETWORK_DESTINATION` | `canonical_host_id:port:protocol` | host-key fingerprint + port + protocol |
| 9 | `SECRET_RESOURCE` | `/etc/goaa/console.env` | exact secret path identity |

### 6.3 NetworkDestination Structure

```python
@dataclass(frozen=True)
class NetworkDestination:
    canonical_host_id: str                # DNS name / host-key fingerprint
    port: int
    protocol: str                         # "ssh", "https", "tcp", "udp"
    approved_address_set: frozenset[str]  # known IPs, NOT authorization identity
```

### 6.4 REMOTE_NODE Restriction

`REMOTE_NODE` is reserved for GOAA registered nodes with stable machine identity.

```text
Valid:   node:aika-core-01, node:aika-1, node:do-sfo3-router
Invalid: node:github.com, node:registry.example.com
```

External services (GitHub, Docker Registry, etc.) use `API_RESOURCE` + `NETWORK_DESTINATION`.

---

## 7. Multi-Effect Classification

Every action is classified into one primary effect and zero or more secondary effects.

### 7.1 ActionRequest Definition

```python
@dataclass(frozen=True)
class ActionRequest:
    request_id: str
    task_id: str
    authorization_snapshot_id: str
    actor_id: str

    primary_effect: ActionEffect
    secondary_effects: frozenset[ActionEffect]
    resource_scopes: tuple[TypedResourceScope, ...]

    requested_tool: str
    normalized_parameters: tuple[CanonicalParameter, ...]
    parameters_digest: str
    equivalent_action_groups: frozenset[str]
    classification_policy_version: str
```

### 7.2 Identity Verification

Kernel MUST verify:

```text
request.task_id == snapshot.task_id
request.authorization_snapshot_id == snapshot.snapshot_id
```

Mismatch → `POLICY_CONFLICT`, no execution, audit only.

### 7.3 Classification Rule

```text
primary_effect or any secondary_effect hits DENY → overall DENY
primary_effect or any secondary_effect hits REQUIRES_APPROVAL → BLOCKED_PENDING_APPROVAL
```

### 7.4 Examples

```text
git push:
  primary = PUSH
  secondary = {NETWORK_EGRESS}

systemctl restart (standalone):
  primary = SERVICE_RESTART
  secondary = {}

deploy with restart:
  primary = DEPLOY
  secondary = factually recomputed per steps (see §10.3)

cat ~/.ssh/id_rsa:
  primary = SECRET_READ
  secondary = {READ}

rm /tmp/file:
  primary = DELETE
  secondary = {}
```

---

## 8. Multi-Resource ActionRequest

Actions can (and often do) operate on multiple resources simultaneously.

### 8.1 Rule

```text
1. resource_scopes must be non-empty
2. No duplicate canonical identities
3. Each scope must independently pass AuthorizationSnapshot checks
4. Any scope unauthorized → overall DENY
5. No overly broad scope may substitute for specific resource identity
```

### 8.2 Example — git push

```python
resource_scopes = (
    TypedResourceScope(GIT_REPOSITORY, "repo:aika-core-01:goaa-ai-main"),
    TypedResourceScope(GIT_REF, "refs/heads/main"),
    TypedResourceScope(API_RESOURCE, "github:repository:taofengtx/goaa-ai-frontend"),
    TypedResourceScope(NETWORK_DESTINATION, "github.com:22:ssh"),
)
```

---

## 9. Canonical Parameters and Digest Verification

Every parameter is normalized, typed, and bound to its associated resource scopes.

### 9.1 CanonicalParameter

```python
@dataclass(frozen=True)
class CanonicalParameter:
    name: str
    value: str
    value_type: str
    resource_scope_indices: tuple[int, ...]
```

### 9.2 Multi-Resource Binding Rules

```text
1. resource_scope_indices must be non-empty
2. Each index must be valid within resource_scopes tuple
3. Indices must not repeat
4. Each security-relevant parameter must bind to all related scopes
5. Kernel must verify parameter consistency with every associated scope
```

### 9.3 Digest Verification

```text
Kernel recomputes parameters_digest = SHA-256(canonical_json(normalized_parameters))
Compares against declared parameters_digest.
Mismatch → POLICY_CONFLICT, no execution, audit only.
```

---

## 10. Equivalent Action Groups

Groups of semantically equivalent actions. Denying a group denies all member tools.

### 10.1 Base Mapping (13 Groups)

Each ActionEffect maps to exactly one base group:

| ActionEffect | Equivalent Group |
|---|---|
| `READ` | `GROUP_READ` |
| `WRITE` | `GROUP_WRITE` |
| `CREATE` | `GROUP_CREATE` |
| `DELETE` | `GROUP_DELETE` |
| `RENAME` | `GROUP_RENAME` |
| `MOVE_OUT_OF_DISCOVERY` | `GROUP_RENAME` |
| `EXECUTE` | `GROUP_EXECUTE` |
| `COMMIT` | `GROUP_COMMIT` |
| `PUSH` | `GROUP_PUSH` |
| `DEPLOY` | `GROUP_DEPLOY` |
| `SERVICE_RESTART` | `GROUP_SERVICE_RESTART` |
| `SECRET_READ` | `GROUP_SECRET_READ` |
| `NETWORK_EGRESS` | `GROUP_NETWORK_EGRESS` |
| `PERMISSION_CHANGE` | `GROUP_PERMISSION_CHANGE` |

Union of all groups covers all 14 execution effects.

### 10.2 Multi-Group Model

```python
equivalent_action_groups: frozenset[str]
```

Groups are **not overloaded** with multiple effects. Each group name corresponds to exactly one base effect. Composite actions express multiple effects via multiple groups:

```text
git push:
  effects = {PUSH, NETWORK_EGRESS}
  groups = {GROUP_PUSH, GROUP_NETWORK_EGRESS}

deploy + restart:
  effects = {DEPLOY, WRITE, NETWORK_EGRESS, SERVICE_RESTART}
  groups = {GROUP_DEPLOY, GROUP_WRITE, GROUP_NETWORK_EGRESS, GROUP_SERVICE_RESTART}
```

**Kernel MUST recompute groups from classification policy — never trust caller-declared groups.**

```text
Mismatch → POLICY_CONFLICT, no execution, audit only.
```

### 10.3 DEPLOY Secondary Effects: Factually Recompiled

> DEPLOY secondary effects are **not** fixed.
> They must be factually recomputed per concrete, canonicalized deployment steps.

```text
Local copy deploy:
  primary = DEPLOY
  secondary = {WRITE}                    # no NETWORK_EGRESS, no SERVICE_RESTART

Remote deploy:
  primary = DEPLOY
  secondary = {WRITE, NETWORK_EGRESS}    # no SERVICE_RESTART (hot-reload)

Deploy requiring restart:
  primary = DEPLOY
  secondary = {WRITE, NETWORK_EGRESS, SERVICE_RESTART}

Hot-reload deploy:
  primary = DEPLOY
  secondary = {WRITE, NETWORK_EGRESS}    # no SERVICE_RESTART
```

### 10.4 Standalone Restart

```text
systemctl restart goaa-local-console.service (standalone maintenance):
  primary = SERVICE_RESTART
  secondary = {}
  groups = {GROUP_SERVICE_RESTART}
  NOT automatically GROUP_DEPLOY.

  Only when restart is part of a deployment pipeline (primary=DEPLOY)
  does GROUP_DEPLOY apply.
```

---

## 11. Immutable AuthorizationSnapshot

An immutable record of what is authorized for a given task/session.

### 11.1 Definition

```python
@dataclass(frozen=True)
class AuthorizationSnapshot:
    snapshot_id: str
    task_id: str
    policy_version: str
    created_at: datetime
    expires_at: datetime | None
    source_authorizations: tuple[str, ...]
    approved_by: str | None
    allowed_effects: frozenset[ActionEffect]
    allowed_resource_scopes: frozenset[TypedResourceScope]
    allowed_equivalent_groups: frozenset[str]
    snapshot_hash: str
```

### 11.2 Immutable Rules

```text
1. Frozen dataclass — no in-place mutation
2. Authorization changes require new snapshot_id
3. Old snapshots retained as historical evidence
4. Nothing explicitly allowed → DEFAULT_DENY
```

### 11.3 Strictest Policy Merge

AuthorizationSnapshot is one of multiple applicable policies. The final authorization result is the **strictest** among all applicable policies.

```text
STRICTEST POLICY MERGE RULE:

Final result = strictest of:
  - AuthorizationSnapshot (effect × scope × group)
  - Shell Policy (template-level risk, requires_approval, timeout, blocklist)
  - Any other applicable capability-specific policy

Merge semantics:
  Any applicable policy returns DENY
    → overall DENY

  No DENY, but any applicable policy returns REQUIRES_APPROVAL
    → BLOCKED_PENDING_APPROVAL

  Only when ALL applicable policies explicitly ALLOW
    → allow execution
```

AuthorizationSnapshot can further **tighten** capability-specific Policy, but **cannot lower it**:

```text
AuthorizationSnapshot CANNOT:
  - Override Shell Policy requires_approval=True → make it ALLOW
  - Lift Shell Policy blocked commands (curl, wget, ssh, ...)
  - Remove resource restrictions from capability-specific policies
  - Lower security baseline of any applicable policy

AuthorizationSnapshot CAN:
  - Further restrict allowed effects beyond what capability-specific policies require
  - Narrow allowed resource scopes
  - Narrow allowed equivalent groups
  - Add additional DENY conditions
```

### 11.4 Examples

```text
Example 1 — Shell Policy says requires_approval=True, Snapshot says ALLOW:
  Shell Policy       → REQUIRES_APPROVAL
  AuthorizationSnapshot → ALLOW
  Strictest merge    → REQUIRES_APPROVAL (cannot lower) ✅

Example 2 — Shell Policy says requires_approval=False, Snapshot says DENY:
  Shell Policy       → ALLOW
  AuthorizationSnapshot → DENY
  Strictest merge    → DENY (snapshot tightened) ✅

Example 3 — Shell Policy blocks "curl", Snapshot allows EXECUTE:
  Shell Policy       → DENY
  AuthorizationSnapshot → ALLOW
  Strictest merge    → DENY (cannot lift prohibition) ✅

Example 4 — Both allow:
  Shell Policy       → ALLOW
  AuthorizationSnapshot → ALLOW
  Strictest merge    → ALLOW ✅
```

---

## 12. Snapshot Canonical Serialization and Hash

### 12.1 Algorithm

```text
serialization = canonical JSON
encoding = UTF-8
Unicode normalization = NFC
key ordering = sorted
frozenset / set-like tuple: sorted by canonical identity string
ordered tuple: maintain declaration order
datetime = UTC RFC3339 (e.g. "2026-06-15T10:30:00Z")
Enum = .value (e.g. "READ")
null = JSON null for None
hash = SHA-256 of canonical UTF-8 bytes
```

### 12.2 Tuple Type Declarations

Every tuple field in the model MUST declare whether it is *ordered* or *set-like*:

```text
Set-like tuples (sorted by canonical identity):
  resource_scopes
  source_authorizations
  normalized_parameters (when used in set contexts)

Ordered tuples (maintain declaration order):
  CanonicalParameter.resource_scope_indices
```

### 12.3 Fields Covered by snapshot_hash

```text
snapshot_id
task_id
policy_version
created_at
expires_at
source_authorizations
approved_by
allowed_effects
allowed_resource_scopes
allowed_equivalent_groups
```

**All security-relevant fields are covered. No field is excluded from the hash.**

---

## 13. Authorization Decision Model

### 13.1 Core Function

```python
def authorize_action(
    action_request: ActionRequest,
    authorization_snapshot: AuthorizationSnapshot,
    deny_ledger: DenyLedger,
) -> AuthorizationDecision:
```

### 13.2 Decisions

| Decision | Write Deny Ledger? | Behavior |
|---|---|---|
| `ALLOW` | ❌ | Capability Broker proceeds |
| `DENY` (USER_DENIAL / APPROVER_DENIAL / PERSISTENT_POLICY) | ✅ `DENY_CREATED` | Blocked |
| `DENY` (AUTOMATIC_POLICY_BLOCK) | ⚠️ Only if policy declares scope+expires | Blocked; not auto-persistent |
| `REQUIRES_APPROVAL` | ❌ Not written | Blocked; waiting for approval |
| `OUT_OF_SCOPE` | ❌ Audit only | Default deny; configuration error |
| `POLICY_CONFLICT` | ❌ Audit only | Stop; report conflict |
| `INVALID_REQUEST` | ❌ Audit only | Malformed request |

### 13.3 Pending Approval vs Deny (Critical Separation)

```text
REQUIRES_APPROVAL:
  - Action does NOT execute
  - ExecutionGate = BLOCKED_PENDING_APPROVAL
  - Deny Ledger is NOT written
  - Equivalent tools also return REQUIRES_APPROVAL (no bypass)

Only when user explicitly rejects or approver denies:
  → AuthorizationDecision = DENY
  → Deny Ledger (DENY_CREATED) is written
```

---

## 14. Classification Attestation

### 14.1 Definition

```python
@dataclass(frozen=True)
class ClassificationAttestation:
    classification_policy_version: str
    declared_primary_effect: ActionEffect
    declared_secondary_effects: frozenset[ActionEffect]
    recomputed_primary_effect: ActionEffect
    recomputed_secondary_effects: frozenset[ActionEffect]
    declared_equivalent_groups: frozenset[str]
    recomputed_equivalent_groups: frozenset[str]
    classification_attestation_hash: str
```

### 14.2 Verification Flow

```text
Step 1: Load classification rules by classification_policy_version
Step 2: Recompute primary_effect / secondary_effects / equivalent_groups
         from requested_tool + normalized_parameters
Step 3: Compare declared vs recomputed:
         - Match → proceed
         - Mismatch → POLICY_CONFLICT, no execution, audit only
Step 4: Attestation hash written to audit log
```

Mismatch does NOT write to Deny Ledger — it writes to audit only.

---

## 15. Deny Ledger Event-Sourced Model

### 15.1 Events (Append-Only)

| Event | Description | Trigger |
|---|---|---|
| `DENY_CREATED` | User or policy denies action | USER_DENIAL / APPROVER_DENIAL / PERSISTENT_POLICY |
| `DENY_REVOKED` | User revokes prior denial | Explicit user revocation |
| `DENY_SUPERSEDED` | Overridden by subsequent approval | Approval covers previously denied scope |
| `DENY_EXPIRED` | Denial expired by time | expires_at reached |

### 15.2 Event Record

```python
@dataclass(frozen=True)
class DenyEvent:
    event_id: str
    deny_id: str
    task_id: str
    session_id: str | None

    event_type: DenyEventType        # CREATED / REVOKED / SUPERSEDED / EXPIRED
    deny_scope: DenyScope
    deny_origin: DenyOrigin

    primary_effect: ActionEffect
    secondary_effects: frozenset[ActionEffect]
    resource_scopes: tuple[TypedResourceScope, ...]       # multi-resource
    equivalent_action_groups: frozenset[str]

    actor: str
    occurred_at: datetime
    expires_at: datetime | None
    reason: str
    approval_id: str | None

    previous_event_hash: str | None  # None for first event of a deny_id chain
    event_hash: str
```

### 15.3 DenyScope

```python
class DenyScope(Enum):
    CURRENT_ACTION = "current_action"       # this action only
    CURRENT_TASK = "current_task"           # entire task lifetime
    CURRENT_SESSION = "current_session"     # current Agent session
    PERSISTENT_POLICY = "persistent_policy" # cross-session policy
```

### 15.4 DenyOrigin

```python
class DenyOrigin(Enum):
    USER_DENIAL = "user_denial"                     # user explicitly refused
    APPROVER_DENIAL = "approver_denial"             # approver via reject endpoint
    PERSISTENT_POLICY = "persistent_policy"         # policy/config rule
    AUTOMATIC_POLICY_BLOCK = "automatic_policy_block"  # automatic block
```

### 15.5 Append-Only Rule

```text
Append-only. No deletion, no overwrite of historical records.
Link: previous_event_hash → SHA-256 of previous JSON.
First event (DENY_CREATED) has previous_event_hash = None.
```

### 15.6 DENY_EXPIRED Lifecycle

```text
DENY_EXPIRED is a Ledger lifecycle event,
NOT a new AuthorizationDecision.

Flow:
  1. DENY_CREATED (with expires_at)
  2. expires_at reached
  3. Append DENY_EXPIRED to Ledger
  4. Subsequent requests re-authorize (fresh decision)
```

---

## 16. Deny Origin and Persistence Rules

### 16.1 Writing Deny Ledger

Only these origins create persistent Deny Ledger entries by default:

| DenyOrigin | Write DENY_CREATED? | Default Scope |
|---|---|---|
| `USER_DENIAL` | ✅ Yes | As declared |
| `APPROVER_DENIAL` | ✅ Yes | As declared |
| `PERSISTENT_POLICY` | ✅ Yes | Cross-session |

### 16.2 Audit-Only (No Deny Ledger)

```text
OUT_OF_SCOPE          → audit only
INVALID_REQUEST       → audit only
POLICY_CONFLICT       → audit only
PARAMETER_DIGEST_MISMATCH → audit only
RESOURCE_SCOPE_MISMATCH   → audit only
TEMPORARY_SYSTEM_ERROR    → audit only
```

### 16.3 AUTOMATIC_POLICY_BLOCK — Not Persistent by Default

```text
AUTOMATIC_POLICY_BLOCK does NOT write Deny Ledger by default.
Only writes DENY_CREATED if ALL of:
  - persistent = true (explicitly set)
  - deny_scope is set
  - expires_at is set
  - equivalent_action_groups is set
  - resource_scopes is set

Missing any field → audit only, no Ledger.
```

---

## 17. Pending Approval State

### 17.1 Separation from Deny

| State | Execution | Write Deny Ledger? | Equivalent Tool Bypass? |
|---|---|---|---|
| `REQUIRES_APPROVAL` | ❌ Blocked, awaiting approval | ❌ No | ❌ Blocked (same decision) |
| `DENY` (user/approver/policy) | ❌ Stopped | ✅ DENY_CREATED | ❌ Blocked (same decision) |

### 17.2 Behavior

```text
BLOCKED_PENDING_APPROVAL:
  - Task stays in awaiting_approval
  - No Deny Ledger record
  - Equivalent tools also return REQUIRES_APPROVAL
  - Only explicit user approval (APPROVAL_GRANTED) can move to queued
  - Only explicit user rejection (APPROVAL_DENIED) writes to Deny Ledger
```

---

## 18. Eleven-Step Pre-Action Gate

### 18.1 Two Layers

```text
Layer 1: Capability Broker
  Agent → requests capability → Broker → resolves action → authorize_action()

  Agent does NOT directly hold OS/Git/network capabilities.
  Agent can only request capabilities through Broker.

Layer 2: Capability Internal Gate
  Even if caller bypasses Agent (calls Python API directly),
  each capability implementation MUST call authorize_action() again.

  No capability without Broker → no escape from Kernel.
```

### 18.2 The 11 Steps (Strict Order)

```text
 1. Parse capability request
 2. Canonicalize parameters
 3. Resolve typed resource scopes (9 types)
 4. Recompute primary and secondary effects
 5. Recompute equivalent action groups
 6. Verify parameter digest and classification attestation
 7. Load and bind immutable AuthorizationSnapshot
    (verify task_id and snapshot_id match ActionRequest)
 8. Apply strictest merge across all applicable policies
 9. Check active Deny Ledger events
10. Produce decision and write pre-action audit
11. Only ALLOW invokes capability
```

### 18.3 Isolation Principles

```text
Python file API: not directly exposed to Agent. Only through File Capability Broker.
Git client: not directly exposed to Agent. Only through Git Capability Broker.
Network socket: not directly exposed to Agent. Only through Network Capability Broker.
Remote execution: only through GOAA Router dispatch. No standalone SSH.
```

### 18.4 Long-Term Enforcement (Beyond Code Convention)

```text
Code convention alone is insufficient.
Future requirements:
  - OS sandbox (seccomp / Landlock / AppArmor) for raw syscall restriction
  - Service account isolation per capability
  - Process-level separation: Broker process ≠ Agent process
```

---

## 19. Capability Broker and Internal Gate

### 19.1 Broker Interface

```text
Agent                     Broker                    Capability
  │                        │                          │
  │── request_capability ──►│                          │
  │                        │── authorize_action() ───►│ (Layer 2 Gate)
  │                        │                          │
  │                        │◄── ALLOW / DENY ────────│
  │                        │                          │
  │◄── result / error ────│                          │
```

### 19.2 Broker Responsibilities

```text
1. Accept capability requests from Agent (never raw OS/Git/network access)
2. Canonicalize parameters into CanonicalParameter tuples
3. Classify action → ActionRequest
4. Call authorize_action() on Layer 1 Gate
5. If ALLOW → invoke capability (which also calls authorize_action() on Layer 2)
6. Return result or error to Agent
```

---

## 20. Shell Capability Relationship

### 20.1 Integration Points

```text
Shell Policy (shell_policy.py):
  - Template allowlist (EXECUTE effect constraint)
  - Risk levels, timeout, requires_approval flags
  → These are independent policies; merged via strictest rule (§11.3)

Shell Validator (shell_validator.py):
  - Static validation layers 1-5 (template/resource/path/block tokens)
  → Authorization Kernel adds Layer 6+ (effect-level authorization)

Shell Execution Plan (shell_execution_plan.py):
  - verify_execution_plan() — 9-dimension argv integrity check
  → This is the EXECUTE-specific final validation BEFORE the gate

Shell Mock Executor (shell_mock_executor.py):
  - Pure mock, no subprocess
  → Remains for Knife 2A testing; real executor requires Kernel gate
```

### 20.2 Strictest Merge in Practice

```text
Example 1 — Shell Policy says requires_approval=True, Snapshot says ALLOW:
  Strictest merge → REQUIRES_APPROVAL (snapshot cannot lower)

Example 2 — Shell Policy says requires_approval=False, Snapshot says DENY:
  Strictest merge → DENY (snapshot tightened)

Example 3 — Shell Policy blocks "curl", Snapshot allows EXECUTE:
  Strictest merge → DENY (cannot lift prohibition)

Example 4 — Both allow:
  Strictest merge → ALLOW
```

---

## 21. Router / Worker / Console Responsibilities

### 21.1 Router (api.py)

```text
Existing:
  - Task state machine (created → validated → awaiting_approval → ...)
  - auto_dispatcher_loop with priority/risk trigger
  - task_approve() endpoint
  - audit_log INSERT on approve
  - task_rebuild_pool (PG restore awaiting_approval)

To add:
  - task_reject() endpoint (missing in V0)
  - Deny Ledger INSERT on reject
  - Control-Plane Authorization Gate (§5.2) for all approval events
  - AuthorizationSnapshot creation (per task, on first dispatch)
  - ClassificationPolicy loading
  - Gate integration (approve→queued atomic transaction)
```

### 21.2 Worker

```text
Existing:
  - Polling for executable tasks
  - task_runner.py dispatch to capabilities

To add:
  - Load AuthorizationSnapshot before executing any capability
  - Apply strictest policy merge (§11.3)
  - Call authorize_action() through Broker
  - Respect DENY / REQUIRES_APPROVAL decisions
  - Report authorization failures to audit log
```

### 21.3 Console (Port 5188)

```text
Existing:
  - UI / proxy / approval display

To add:
  - Authorization snapshot viewer
  - Pending approval queue (approve/reject UI)
  - Deny Ledger viewer
  - Classification attestation viewer (for audit)
```

---

## 22. Fail-Closed Rules

```text
1. No AuthorizationSnapshot for task → DEFAULT_DENY
2. Snapshot expired → DEFAULT_DENY
3. Deny Ledger unreachable → DEFAULT_DENY (fail secure, not fail open)
4. Classification Policy unavailable → DEFAULT_DENY
5. Any resource scope unauthorized → overall DENY
6. Any effect or group unauthorized → overall DENY
7. Classification attestation mismatch → POLICY_CONFLICT, no execution
8. Digest verification mismatch → POLICY_CONFLICT, no execution
9. Gate Layer 1 passes but Layer 2 fails → DENY
10. Any applicable policy returns DENY → overall DENY (strictest merge)
```

---

## 23. Audit Requirements

### 23.1 Minimum Audit Events

```text
1. ActionRequest received (digest, primary, secondary, groups, scopes)
2. ClassificationAttestation (declared vs recomputed; hash)
3. AuthorizationDecision (decision, reason, snapshot_id, strictest merge source)
4. DenyEvent (all fields per §15)
5. ApprovalDecision with Control-Plane Gate attestation (§5.2)
6. AuthorizationSnapshot created
7. Gate Layer 1 result (Broker level)
8. Gate Layer 2 result (Capability internal)
```

### 23.2 Audit Format

```text
Each audit record includes:
  request_id
  action_request digest
  classification_attestation hash
  authorization_decision
  deny_origin (if DENY)
  deny_event_id (if Ledger written)
  control_plane_gate_attestation (if approval event)
  snapshot_id
  timestamp (UTC RFC3339)
```

---

## 24. Threat Model and Bypass Cases

### 24.1 Incident Replay Protection (Knife 2A-1)

Scenario: User denied RENAME of stale test files (`test_shell_execution_plan.py`, `test_shell_mock_executor.py`, `test_shell_resource_policy.py`).

```text
Subsequent Agent attempts:
  os.rename(...)                         → DENY (GROUP_RENAME)
  Path.rename(...)                       → DENY (GROUP_RENAME)
  shutil.move(...)                       → DENY (GROUP_RENAME)
  Move out of tests/ directory           → DENY (GROUP_RENAME)
  Change extension to evade discovery    → DENY (GROUP_RENAME)
  Delete + recreate (different identity) → DENY (GROUP_DELETE + GROUP_CREATE)
```

### 24.2 Other Bypass Cases

```text
Forbidden commit:
  git commit                    → DENY (GROUP_COMMIT)
  GitHub API create commit      → DENY (GROUP_COMMIT, multi-scope)
  libgit2 programmatic commit   → DENY (GROUP_COMMIT)

Forbidden push:
  git push                      → DENY (GROUP_PUSH)
  GitHub API update ref         → DENY (GROUP_PUSH + GROUP_NETWORK_EGRESS)
  Remote host proxy push        → DENY (GROUP_PUSH, REMOTE_NODE scope)

Forbidden delete:
  rm                            → DENY (GROUP_DELETE)
  os.remove()                   → DENY (GROUP_DELETE)
  Path.unlink()                 → DENY (GROUP_DELETE)
  shutil.rmtree()               → DENY (GROUP_DELETE)
  Overwrite with empty content  → DENY (GROUP_WRITE)

Awaiting approval (strictest merge prevents snapshot from lowering):
  Shell template with requires_approval=True → REQUIRES_APPROVAL
  Python subprocess.run()                    → REQUIRES_APPROVAL (GROUP_EXECUTE)
  eval() / exec()                            → REQUIRES_APPROVAL (GROUP_EXECUTE)
```

### 24.3 DENY_EXPIRED Recovery

```text
If a deny_scope=CURRENT_TASK deny expires (DENY_EXPIRED appended):
  - Subsequent requests for same action → fresh authorize_action()
  - Not automatically re-DENY'd
  - New snapshot or approval may allow the action
```

### 24.4 Control-Plane Gate Bypass

```text
Attempt to approve task without identity:
  → INVALID_REQUEST (actor identity missing)

Attempt to reject task with wrong role:
  → DENY (approver role insufficient)

Attempt to re-approve with same approval_id but different decision:
  → IDEMPOTENCY_CONFLICT, HTTP 409
```

---

## 25. Implementation Phases

Knife 2A-2 remains frozen until AK-1 through AK-4 are reviewed and approved.

| Knife | Scope | Real Subprocess? | Git/DO/Runtime? |
|---|---|---|---|
| **AK-1** | Schema / Enum / canonical serialization | ❌ No | ❌ No |
| **AK-2** | AuthorizationSnapshot + ClassificationPolicy (mock) | ❌ No | ❌ No |
| **AK-3** | Append-only DenyLedger model (mock) | ❌ No | ❌ No |
| **AK-4** | `authorize_action()` pure policy kernel (mock) | ❌ No | ❌ No |
| **AK-5** | Capability Broker interface (mock) | ❌ No | ❌ No |
| **AK-6** | Single controlled capability integration trial | ❌ No | ❌ No (requires Tao approval) |

### 25.1 AK-1 Constraints

```text
1. Pure functions only — no I/O, no subprocess, no network
2. Testing framework: unittest (standard library). No new test dependencies.
3. Define enums: ActionEffect, ControlPlaneEvent, ResourceScopeType,
   DenyEventType, DenyScope, DenyOrigin, AuthorizationDecision
4. Define dataclasses: ActionRequest, CanonicalParameter, TypedResourceScope,
   AuthorizationSnapshot, DenyEvent, ClassificationAttestation, NetworkDestination
5. Define canonical serialization + hash functions
6. All tests via unittest.TestCase, no pytest dependency
```

### 25.2 Knife 2A-2 Remains Frozen

```text
Knife 2A-2 (real subprocess.run integration) stays frozen
until AK-1, AK-2, AK-3, AK-4 are:
  - Code complete
  - Tested (all pass via unittest)
  - L1 reviewed
  - Approved by Tao
```

---

## 26. Highest Governance Rule

```text
GOAA Runtime OS 的授權對象是動作效果，而不是工具名稱。

當用戶明確拒絕某項動作效果後，
任何 Agent、Tool、Skill、Shell、Python API、Git API、
文件 API、遠端腳本或其他等價執行路徑，
均不得在同一授權作用域內實現相同效果。

未獲得明確授權的副作用操作默認拒絕。
安全審批不得通過更換工具、語言、API、機器或執行節點繞過。
```

---

## 27. Open Questions and Non-Blocking Items

| # | Item | Status | Notes |
|---|---|---|---|
| N1 | Dual risk mapping (router int vs shell_policy string) | Non-blocking | Bridge function can normalize |
| N2 | Worker identity authentication | Non-blocking | Currently relies on Tailscale trust |
| N3 | Console approval UI | Non-blocking | Marked in F-lite §16 as required |
| N4 | `approved` state has no consumer | Non-blocking | Covered by approve→queued atomic transaction |
| N5 | approval_id idempotency missing | Non-blocking | Can be added in AK-2 implementation |
| N6 | Concurrent approval/rejection race | Open | Needs distributed lock or PG advisory lock |
| N7 | Snapshot storage backend | Open | PG recommended for consistency |
| N8 | Deny Ledger storage | Open | Single append-only table, JSONB event body |
| N9 | Snapshot expiry enforcement | Open | Worker polling pattern consistent with existing |
| N10 | Task ROLLBACK after DENY | Open | Task enters rejected/cancelled; needs cleanup |

---

## Appendix A: File Overwrite Guard

```bash
FILE='docs/architecture/GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md'

test ! -e "$FILE" || {
  echo 'STOP_FILE_ALREADY_EXISTS'
  exit 1
}
```

## Appendix B: Canonical JSON Rules

```text
Encoding: UTF-8
Unicode normalization: NFC
Key ordering: lexicographic sorted
frozenset: sorted by canonical identity string
Set-like tuple: sorted by canonical identity string
Ordered tuple: maintain declaration order
Enum: .value string
datetime: UTC RFC3339 (e.g. "2026-06-15T10:30:00Z")
null: JSON null for None
Hash: SHA-256 of canonical UTF-8 bytes
```

## Appendix C: Effect-Group Coverage Verification

```text
Execution Effects (14):
  {READ, WRITE, CREATE, DELETE, RENAME, MOVE_OUT_OF_DISCOVERY,
   EXECUTE, COMMIT, PUSH, DEPLOY, SERVICE_RESTART,
   SECRET_READ, NETWORK_EGRESS, PERMISSION_CHANGE}

13 base groups, 1:1 mapping, no overloading.

Union of all groups = all 14 execution effects ✅

Factual inheritance only:
  SECRET_READ → secondary {READ}
  MOVE_OUT_OF_DISCOVERY → secondary {RENAME}
  PUSH → secondary {NETWORK_EGRESS}
  DEPLOY → secondary factually recomputed per deployment steps
```

## Appendix D: Glossary

| Term | Definition |
|---|---|
| ActionEffect | Factual semantic effect of an action on system state |
| AuthorizationDecision | Result of the authorize_action() function |
| AuthorizationSnapshot | Immutable, hashed record of authorized effects/scopes/groups per task |
| Capability Broker | Layer 1 of the Pre-Action Gate; mediates agent → capability |
| ClassificationAttestation | Verified record of effect classification with recomputed values |
| Control-Plane Gate | Mandatory checks for approval events (identity, role, scope, idempotency) |
| ControlPlaneEvent | Meta-event in the authorization lifecycle |
| Deny Ledger | Append-only event-sourced log of denial events |
| Effect Inheritance | Factual secondary effects derived from the primary effect |
| Equivalent Action Group | 1:1 mapping from ActionEffect; composite actions use multiple groups |
| ExecutionGate | BLOCKED_PENDING_APPROVAL for REQUIRES_APPROVAL decisions |
| Pre-Action Gate | 11-step two-layer gate before any action executes |
| Strictest Policy Merge | Final = strictest result among all applicable policies |
| TypedResourceScope | Typed, canonicalized resource identity with structured matching |
