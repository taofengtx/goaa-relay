"""
GOAA Task Gateway Pure Data Models (P4-T2)
===========================================
Pure dataclass models for /tasks/run gateway: TaskRunRequest, TaskRunResult,
AuditLog, EvidencePackage, RollbackPlan, ThreeTruthLayers, and supporting enums.

Per spec: docs/runtime/GOAA_PACKAGE4_TASK_EXECUTION_GATEWAY_SPEC_V0.1_20260623.md

No external side effects: no IO, no network, no shell, no subprocess, no
runtime mutation, no secrets, no DO access, no persistence, no executor.
All validation is pure-function only.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ══════════════════════════════════════════════════════════════
# ENUMS — spec sections 4, 5, 6, 8
# ══════════════════════════════════════════════════════════════

class ExecutionMode(str, Enum):
    """Execution mode for a /tasks/run request (spec section 4)."""
    PREVIEW_ONLY = "preview_only"
    PLAN_ONLY = "plan_only"
    DRY_RUN_ONLY = "dry_run_only"
    READONLY_DRY_RUN = "readonly_dry_run"
    APPROVED_LOCAL_ACTION = "approved_local_action"
    BLOCKED = "blocked"


class ApprovalState(str, Enum):
    """Approval state for a /tasks/run request (spec section 5)."""
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    APPROVED_BY_TAO = "approved_by_tao"
    REJECTED_BY_TAO = "rejected_by_tao"
    EXPIRED = "expired"


class TaskRiskLevel(str, Enum):
    """Risk level for a /tasks/run request (spec section 6).

    L0=information, L1=readonly, L2=local_dry_run,
    L3=local_mutation, L4=critical_runtime.
    """
    L0_INFORMATION = "L0_information"
    L1_READONLY = "L1_readonly"
    L2_LOCAL_DRY_RUN = "L2_local_dry_run"
    L3_LOCAL_MUTATION = "L3_local_mutation"
    L4_CRITICAL_RUNTIME = "L4_critical_runtime"

    def to_int(self) -> int:
        return {
            "L0_information": 0,
            "L1_readonly": 1,
            "L2_local_dry_run": 2,
            "L3_local_mutation": 3,
            "L4_critical_runtime": 4,
        }[self.value]


class TaskRunStatus(str, Enum):
    """Status of a /tasks/run execution attempt (spec section 8)."""
    BLOCKED = "blocked"
    PREVIEW_ONLY = "preview_only"
    PLAN_ONLY = "plan_only"
    DRY_RUN_ONLY = "dry_run_only"
    DRY_RUN = "dry_run"
    APPROVED_PENDING = "approved_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class IntentExecutionPolicy(str, Enum):
    """Pre-configured execution policy per intent (spec section 9)."""
    NEVER = "never"
    NO_MUTATION = "no_mutation"
    MUTATION = "mutation"
    APPROVAL_RECORD_ONLY = "approval_record_only"
    REJECTION_RECORD_ONLY = "rejection_record_only"
    NO_REAL_RAG = "no_real_rag"
    NO_PRIVATE_ACCESS = "no_private_access"


class Decision(str, Enum):
    """Audit decision for a /tasks/run attempt (spec section 11)."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    PREVIEW_ONLY = "preview_only"
    PLAN_ONLY = "plan_only"
    DRY_RUN_ONLY = "dry_run_only"
    REQUIRES_APPROVAL = "requires_approval"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ══════════════════════════════════════════════════════════════
# DATACLASSES — spec sections 7, 8, 11, 12, 13, 14
# ══════════════════════════════════════════════════════════════

@dataclass
class ThreeTruthLayers:
    """Three Truth Layers snapshot for audit (spec section 14)."""
    runtime_truth: dict
    git_truth: dict
    documentation_truth: dict

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class RollbackPlan:
    """Rollback plan for any action above L1 (spec section 13)."""
    rollback_available: bool
    rollback_steps: list[str] = field(default_factory=list)
    rollback_risk: str = ""
    rollback_owner: str = ""
    rollback_test: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class TaskRunRequest:
    """Request to execute a task via /tasks/run (spec section 7).

    Pure data container — no methods that cause side effects.
    """
    request_id: str
    task_id: str
    envelope_id: str
    intent: str
    risk_level: str                  # one of TaskRiskLevel values (as string)
    execution_mode: str              # one of ExecutionMode values (as string)
    approval_state: str              # one of ApprovalState values (as string)
    approval_id: str = ""
    actor_id: str = ""
    requested_action: str = ""
    normalized_parameters: dict = field(default_factory=dict)
    parameter_digest: str = ""
    created_at_utc: str = ""
    expires_at_utc: str = ""
    source_message_hash: str = ""
    runtime_context: dict = field(default_factory=dict)
    rollback_plan: Optional[RollbackPlan] = None
    evidence_required: bool = False
    policy_version: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.rollback_plan is not None:
            d["rollback_plan"] = self.rollback_plan.to_dict()
        else:
            d["rollback_plan"] = None
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def compute_sha256(self) -> str:
        return hashlib.sha256(self.to_json(indent=2).encode("utf-8")).hexdigest()


@dataclass
class TaskRunResult:
    """Result of a /tasks/run execution attempt (spec section 8).

    Pure data container — no methods that cause side effects.
    """
    run_id: str
    request_id: str
    status: str                      # one of TaskRunStatus values (as string)
    execution_mode: str              # one of ExecutionMode values (as string)
    task_executed: bool = False
    mutation_performed: bool = False
    worker_started: bool = False
    executor_enabled: bool = False
    do_connected: bool = False
    real_rag_query_executed: bool = False
    embedding_rebuild_executed: bool = False
    started_at_utc: str = ""
    completed_at_utc: str = ""
    evidence_package_id: str = ""
    audit_log_id: str = ""
    result_summary: str = ""
    error_code: str = ""
    error_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def compute_sha256(self) -> str:
        return hashlib.sha256(self.to_json(indent=2).encode("utf-8")).hexdigest()


@dataclass
class AuditLog:
    """Audit record for a /tasks/run attempt (spec section 11).

    Pure data container — no methods that cause side effects.
    """
    audit_log_id: str
    request_id: str
    actor_id: str
    intent: str
    risk_level: str
    approval_state: str
    decision: str                    # one of Decision values (as string)
    denial_reason: str = ""
    runtime_truth_snapshot: dict = field(default_factory=dict)
    git_truth_snapshot: dict = field(default_factory=dict)
    documentation_truth_snapshot: dict = field(default_factory=dict)
    created_at_utc: str = ""
    three_truths: Optional[ThreeTruthLayers] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.three_truths is not None:
            d["three_truths"] = self.three_truths.to_dict()
        else:
            d["three_truths"] = None
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class GatewayEvidencePackage:
    """Evidence package for a /tasks/run attempt (spec section 12).

    Renamed to avoid collision with task_envelope.EvidencePackage.
    """
    evidence_package_id: str
    request_id: str
    run_id: str
    readonly: bool = False
    preview_only: bool = False
    task_executed: bool = False
    runtime_mutation: bool = False
    worker_started: bool = False
    executor_enabled: bool = False
    do_connected: bool = False
    real_rag_query_executed: bool = False
    embedding_rebuild_executed: bool = False
    evidence_summary: str = ""
    created_at_utc: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ══════════════════════════════════════════════════════════════
# INTENT POLICY MATRIX — spec section 9
# ══════════════════════════════════════════════════════════════

_INTENT_POLICY_MATRIX: dict[str, dict[str, Any]] = {
    "pure_chat": {
        "default_mode": ExecutionMode.PREVIEW_ONLY,
        "approval_state": ApprovalState.NOT_REQUIRED,
        "execution_policy": IntentExecutionPolicy.NEVER,
    },
    "task_status": {
        "default_mode": ExecutionMode.READONLY_DRY_RUN,
        "approval_state": ApprovalState.NOT_REQUIRED,
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
    },
    "topk_verify": {
        "default_mode": ExecutionMode.READONLY_DRY_RUN,
        "approval_state": ApprovalState.NOT_REQUIRED,
        "execution_policy": IntentExecutionPolicy.NO_REAL_RAG,
    },
    "memory_fetch": {
        "default_mode": ExecutionMode.PREVIEW_ONLY,
        "approval_state": ApprovalState.REQUIRED,
        "execution_policy": IntentExecutionPolicy.NO_PRIVATE_ACCESS,
    },
    "embed": {
        "default_mode": ExecutionMode.BLOCKED,
        "approval_state": ApprovalState.REQUIRED,
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
    },
    "approve_task": {
        "default_mode": ExecutionMode.PREVIEW_ONLY,
        "approval_state": ApprovalState.APPROVED_BY_TAO,
        "execution_policy": IntentExecutionPolicy.APPROVAL_RECORD_ONLY,
    },
    "reject_task": {
        "default_mode": ExecutionMode.PREVIEW_ONLY,
        "approval_state": ApprovalState.REJECTED_BY_TAO,
        "execution_policy": IntentExecutionPolicy.REJECTION_RECORD_ONLY,
    },
}


# ══════════════════════════════════════════════════════════════
# PURE HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def get_default_execution_mode(intent: str) -> ExecutionMode:
    """Return the default ExecutionMode for a given intent.

    Unknown intents default to BLOCKED.
    """
    policy = _INTENT_POLICY_MATRIX.get(intent)
    if policy is None:
        return ExecutionMode.BLOCKED
    return policy["default_mode"]


def get_default_approval_state(intent: str) -> ApprovalState:
    """Return the default ApprovalState for a given intent.

    Unknown intents default to REQUIRED.
    """
    policy = _INTENT_POLICY_MATRIX.get(intent)
    if policy is None:
        return ApprovalState.REQUIRED
    return policy["approval_state"]


def is_effectively_blocked(
    execution_mode: str,
    approval_state: str,
) -> bool:
    """Determine whether a request is effectively blocked.

    A request is blocked if:
    - execution_mode is BLOCKED or PREVIEW_ONLY, OR
    - approval_state is REQUIRED (not yet approved), REJECTED, or EXPIRED.
    """
    blocked_modes = {ExecutionMode.BLOCKED.value, ExecutionMode.PREVIEW_ONLY.value}
    if execution_mode in blocked_modes:
        return True
    blocked_approvals = {
        ApprovalState.REQUIRED.value,
        ApprovalState.REJECTED_BY_TAO.value,
        ApprovalState.EXPIRED.value,
    }
    if approval_state in blocked_approvals:
        return True
    return False


def is_real_execution_represented(
    execution_mode: str,
    approval_state: str,
    task_executed: bool,
    mutation_performed: bool,
    worker_started: bool,
    executor_enabled: bool,
    do_connected: bool,
    real_rag_query_executed: bool = False,
    embedding_rebuild_executed: bool = False,
) -> bool:
    """Check whether the result represents real execution.

    Returns True ONLY when:
    - execution_mode == approved_local_action
    - approval_state == approved_by_tao
    - any execution flag is True

    All other combinations return False (blocked, preview, not-yet-approved, expired).
    """
    if execution_mode != ExecutionMode.APPROVED_LOCAL_ACTION.value:
        return False
    if approval_state != ApprovalState.APPROVED_BY_TAO.value:
        return False
    any_execution = any([
        task_executed,
        mutation_performed,
        worker_started,
        executor_enabled,
        do_connected,
        real_rag_query_executed,
        embedding_rebuild_executed,
    ])
    return any_execution


def validate_task_run_request(request: TaskRunRequest) -> list[str]:
    """Validate a TaskRunRequest and return a list of error messages.

    Returns an empty list if the request is valid.
    Pure function — no side effects.
    """
    errors: list[str] = []

    # request_id must be non-empty
    if not request.request_id:
        errors.append("request_id must be non-empty")

    # task_id must be non-empty
    if not request.task_id:
        errors.append("task_id must be non-empty")

    # envelope_id must be non-empty
    if not request.envelope_id:
        errors.append("envelope_id must be non-empty")

    # intent must be a known value
    if request.intent not in _INTENT_POLICY_MATRIX:
        errors.append(f"unknown intent: {request.intent}")

    # risk_level must be a valid TaskRiskLevel
    valid_risk_levels = {e.value for e in TaskRiskLevel}
    if request.risk_level not in valid_risk_levels:
        errors.append(f"invalid risk_level: {request.risk_level}")

    # execution_mode must be a valid ExecutionMode
    valid_modes = {e.value for e in ExecutionMode}
    if request.execution_mode not in valid_modes:
        errors.append(f"invalid execution_mode: {request.execution_mode}")

    # approval_state must be a valid ApprovalState
    valid_states = {e.value for e in ApprovalState}
    if request.approval_state not in valid_states:
        errors.append(f"invalid approval_state: {request.approval_state}")

    # parameter_digest must be non-empty if normalized_parameters is non-empty
    if request.normalized_parameters and not request.parameter_digest:
        errors.append("parameter_digest must be non-empty when normalized_parameters is present")

    return errors


def validate_task_run_result(result: TaskRunResult) -> list[str]:
    """Validate a TaskRunResult and return a list of error messages.

    Returns an empty list if the result is valid.
    Pure function — no side effects.
    """
    errors: list[str] = []

    # run_id must be non-empty
    if not result.run_id:
        errors.append("run_id must be non-empty")

    # request_id must be non-empty
    if not result.request_id:
        errors.append("request_id must be non-empty")

    # status must be a valid TaskRunStatus
    valid_statuses = {e.value for e in TaskRunStatus}
    if result.status not in valid_statuses:
        errors.append(f"invalid status: {result.status}")

    # execution_mode must be a valid ExecutionMode
    valid_modes = {e.value for e in ExecutionMode}
    if result.execution_mode not in valid_modes:
        errors.append(f"invalid execution_mode: {result.execution_mode}")

    # Blocked results must not indicate ANY real execution
    if result.status == TaskRunStatus.BLOCKED.value:
        blocked_flags = {
            "task_executed": result.task_executed,
            "mutation_performed": result.mutation_performed,
            "worker_started": result.worker_started,
            "executor_enabled": result.executor_enabled,
            "do_connected": result.do_connected,
            "real_rag_query_executed": result.real_rag_query_executed,
            "embedding_rebuild_executed": result.embedding_rebuild_executed,
        }
        for flag_name, flag_value in blocked_flags.items():
            if flag_value:
                errors.append(f"blocked result must not have {flag_name}=True")

    # Preview-only results must not indicate any real execution
    if result.status == TaskRunStatus.PREVIEW_ONLY.value:
        preview_flags = {
            "task_executed": result.task_executed,
            "mutation_performed": result.mutation_performed,
            "worker_started": result.worker_started,
            "executor_enabled": result.executor_enabled,
            "do_connected": result.do_connected,
            "real_rag_query_executed": result.real_rag_query_executed,
            "embedding_rebuild_executed": result.embedding_rebuild_executed,
        }
        for flag_name, flag_value in preview_flags.items():
            if flag_value:
                errors.append(f"preview_only result must not have {flag_name}=True")

    return errors


def _utc_now() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str = "GOAA-GTWY") -> str:
    """Generate a unique ID with prefix and timestamp."""
    ts = int(time.time() * 1000)
    return f"{prefix}-{ts}"


# ══════════════════════════════════════════════════════════════
# BUILDER HELPERS (pure, no side effects beyond timestamp)
# ══════════════════════════════════════════════════════════════

def build_task_run_request(
    task_id: str,
    envelope_id: str,
    intent: str,
    *,
    risk_level: Optional[str] = None,
    execution_mode: Optional[str] = None,
    approval_state: Optional[str] = None,
    approval_id: str = "",
    actor_id: str = "",
    requested_action: str = "",
    normalized_parameters: Optional[dict] = None,
    parameter_digest: str = "",
    source_message_hash: str = "",
    runtime_context: Optional[dict] = None,
    rollback_plan: Optional[RollbackPlan] = None,
    evidence_required: bool = False,
    policy_version: str = "",
) -> TaskRunRequest:
    """Build a TaskRunRequest with default values from the policy matrix.

    If risk_level / execution_mode / approval_state are not explicitly
    provided, they are derived from the intent policy matrix.
    """
    # Derive defaults from policy matrix
    default_mode = get_default_execution_mode(intent)
    default_approval = get_default_approval_state(intent)

    # Map TaskRiskLevel from intent based on existing envelope risk
    risk_map = {
        "pure_chat": TaskRiskLevel.L0_INFORMATION,
        "task_status": TaskRiskLevel.L0_INFORMATION,
        "topk_verify": TaskRiskLevel.L1_READONLY,
        "memory_fetch": TaskRiskLevel.L2_LOCAL_DRY_RUN,
        "approve_task": TaskRiskLevel.L3_LOCAL_MUTATION,
        "reject_task": TaskRiskLevel.L3_LOCAL_MUTATION,
        "embed": TaskRiskLevel.L4_CRITICAL_RUNTIME,
    }

    now_utc = _utc_now()
    request_id = _generate_id("GOAA-GTWY-REQ")

    return TaskRunRequest(
        request_id=request_id,
        task_id=task_id,
        envelope_id=envelope_id,
        intent=intent,
        risk_level=risk_level or risk_map.get(intent, TaskRiskLevel.L0_INFORMATION).value,
        execution_mode=execution_mode or default_mode.value,
        approval_state=approval_state or default_approval.value,
        approval_id=approval_id,
        actor_id=actor_id,
        requested_action=requested_action,
        normalized_parameters=normalized_parameters or {},
        parameter_digest=parameter_digest,
        created_at_utc=now_utc,
        source_message_hash=source_message_hash,
        runtime_context=runtime_context or {},
        rollback_plan=rollback_plan,
        evidence_required=evidence_required,
        policy_version=policy_version,
    )


def build_blocked_result(
    request_id: str,
    *,
    denial_reason: str = "",
) -> TaskRunResult:
    """Build a blocked TaskRunResult — the default safe posture.

    All execution flags default to False.  This is the only result that
    can be produced without explicit Tao approval.
    """
    run_id = _generate_id("GOAA-GTWY-RUN")
    now_utc = _utc_now()
    return TaskRunResult(
        run_id=run_id,
        request_id=request_id,
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        task_executed=False,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        real_rag_query_executed=False,
        embedding_rebuild_executed=False,
        started_at_utc=now_utc,
        completed_at_utc=now_utc,
        result_summary=denial_reason or "Blocked by default execution posture",
        error_code="BLOCKED_BY_DEFAULT" if not denial_reason else "BLOCKED",
        error_message=denial_reason or "Default execution posture: all requests blocked",
    )

class TaskRiskClassification(BaseModel):
    """P5-T4: Static risk classification and strategy matrix model for Package 5 tasks.

    Provides deterministic, pure data classification without side effects.
    """

    intent: str
    risk_level: TaskRiskLevel = TaskRiskLevel.L0_INFORMATION
    strategy: str = "preview_only"
    execution_policy: IntentExecutionPolicy = IntentExecutionPolicy.NEVER
    approval_required: bool = False
    blocked_reason: Optional[str] = None
    no_real_execution: bool = True


_STATIC_STRATEGY_MATRIX: dict[str, dict[str, Any]] = {
    "pure_chat": {
        "risk_level": TaskRiskLevel.L0_INFORMATION,
        "strategy": "preview_only",
        "execution_policy": IntentExecutionPolicy.NEVER,
        "approval_required": False,
        "blocked_reason": None,
    },
    "task_status": {
        "risk_level": TaskRiskLevel.L0_INFORMATION,
        "strategy": "plan_only",
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
        "approval_required": False,
        "blocked_reason": None,
    },
    "topk_verify": {
        "risk_level": TaskRiskLevel.L1_READONLY,
        "strategy": "plan_only",
        "execution_policy": IntentExecutionPolicy.NO_REAL_RAG,
        "approval_required": False,
        "blocked_reason": None,
    },
    "memory_fetch": {
        "risk_level": TaskRiskLevel.L2_LOCAL_DRY_RUN,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.NO_PRIVATE_ACCESS,
        "approval_required": True,
        "blocked_reason": "Memory fetch is blocked in Package 5",
    },
    "embed": {
        "risk_level": TaskRiskLevel.L4_CRITICAL_RUNTIME,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
        "approval_required": True,
        "blocked_reason": "Embed/vector operations are blocked in Package 5",
    },
    "vector": {
        "risk_level": TaskRiskLevel.L4_CRITICAL_RUNTIME,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
        "approval_required": True,
        "blocked_reason": "Vector/retrieval operations are blocked in Package 5",
    },
    "retrieval": {
        "risk_level": TaskRiskLevel.L4_CRITICAL_RUNTIME,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.NO_MUTATION,
        "approval_required": True,
        "blocked_reason": "Retrieval operations are blocked in Package 5",
    },
    "approve_task": {
        "risk_level": TaskRiskLevel.L3_LOCAL_MUTATION,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.APPROVAL_RECORD_ONLY,
        "approval_required": True,
        "blocked_reason": "Task approval is blocked in Package 5",
    },
    "reject_task": {
        "risk_level": TaskRiskLevel.L3_LOCAL_MUTATION,
        "strategy": "blocked",
        "execution_policy": IntentExecutionPolicy.REJECTION_RECORD_ONLY,
        "approval_required": True,
        "blocked_reason": "Task rejection is blocked in Package 5",
    },
}

_HIGH_RISK_KEYWORDS = {
    "executor",
    "shell",
    "exec",
    "deploy",
    "runtime_mutation",
    "systemctl",
    "doctl",
    "git_push",
    "git_merge",
    "merge",
    "mutation",
    "db_write",
}


def classify_task_intent(intent: str) -> TaskRiskClassification:
    """P5-T4: Static, deterministic risk classification and strategy matrix lookup.

    Pure function — no network, shell, DB, LLM, executor, or external calls.
    """
    if intent in _STATIC_STRATEGY_MATRIX:
        cfg = _STATIC_STRATEGY_MATRIX[intent]
        return TaskRiskClassification(
            intent=intent,
            risk_level=cfg["risk_level"],
            strategy=cfg["strategy"],
            execution_policy=cfg["execution_policy"],
            approval_required=cfg["approval_required"],
            blocked_reason=cfg["blocked_reason"],
            no_real_execution=True,
        )

    # Check for high-risk / executor / shell / deploy / systemctl / doctl / git push / merge intent
    normalized = intent.lower()
    if any(keyword in normalized for keyword in _HIGH_RISK_KEYWORDS):
        return TaskRiskClassification(
            intent=intent,
            risk_level=TaskRiskLevel.L4_CRITICAL_RUNTIME,
            strategy="blocked",
            execution_policy=IntentExecutionPolicy.NEVER,
            approval_required=True,
            blocked_reason=f"High-risk intent '{intent}' (executor/shell/deploy/mutation) is blocked in Package 5",
            no_real_execution=True,
        )

    # Default fallback for unknown intents: blocked with high risk
    return TaskRiskClassification(
        intent=intent,
        risk_level=TaskRiskLevel.L4_CRITICAL_RUNTIME,
        strategy="blocked",
        execution_policy=IntentExecutionPolicy.NEVER,
        approval_required=True,
        blocked_reason=f"Unknown intent '{intent}' is blocked in Package 5",
        no_real_execution=True,
    )


class RunnerTarget(BaseModel):
    """Package 5 plan-only runner target.

    This object describes where a future task could run.
    It must not enable or imply real execution in Package 5.
    """

    target_type: Literal[
        "local_console",
        "local_runner",
        "cloud_runner",
        "aika_box",
        "disabled",
    ] = "disabled"
    target_node: Optional[str] = None
    target_runtime: Optional[str] = None
    executor_required: bool = False
    executor_enabled: bool = False
    real_execution_allowed: bool = False

    @model_validator(mode="after")
    def enforce_no_execution(self) -> "RunnerTarget":
        if self.executor_enabled:
            raise ValueError("Package 5 RunnerTarget must not enable executor")
        if self.real_execution_allowed:
            raise ValueError("Package 5 RunnerTarget must not allow real execution")
        return self


class ExecutionPlan(BaseModel):
    """Package 5 non-executing execution plan."""

    plan_id: str
    request_id: str
    task_id: str
    intent: str
    actor_id: Optional[str] = None
    approval_state: ApprovalState = ApprovalState.REQUIRED
    execution_mode: ExecutionMode = ExecutionMode.PLAN_ONLY
    risk_level: str = "L1_readonly"
    strategy: Optional[str] = None
    execution_policy: Optional[str] = None
    approval_required: Optional[bool] = None
    blocked_reason: Optional[str] = None
    risk_classification: Optional[TaskRiskClassification] = None
    runner_target: RunnerTarget = Field(default_factory=RunnerTarget)
    planned_steps: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    forbidden_capabilities: list[str] = Field(default_factory=list)
    expected_inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    rollback_hint: Optional[str] = None
    no_execution: bool = True
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Literal["execution_plan_gateway"] = "execution_plan_gateway"

    @model_validator(mode="after")
    def enforce_plan_only_contract(self) -> "ExecutionPlan":
        allowed = {
            ExecutionMode.PLAN_ONLY,
            ExecutionMode.DRY_RUN_ONLY,
            ExecutionMode.BLOCKED,
            ExecutionMode.PREVIEW_ONLY,
        }
        if self.execution_mode not in allowed:
            raise ValueError("ExecutionPlan must use a non-executing execution mode")
        if self.no_execution is not True:
            raise ValueError("ExecutionPlan must keep no_execution=true")
        if self.runner_target.executor_enabled:
            raise ValueError("ExecutionPlan runner target must not enable executor")
        if self.runner_target.real_execution_allowed:
            raise ValueError("ExecutionPlan runner target must not allow real execution")
        return self


class DryRunResult(BaseModel):
    """Package 5 simulated, non-executing dry-run result."""

    dry_run_id: str
    plan_id: str
    status: Literal["dry_run_only"] = "dry_run_only"
    simulated: bool = True
    task_executed: bool = False
    mutation_performed: bool = False
    risk_classification: Optional[TaskRiskClassification] = None
    evidence_package: Optional[GatewayEvidencePackage] = None
    audit_log: Optional[AuditLog] = None

    @model_validator(mode="after")
    def enforce_dry_run_only_contract(self) -> "DryRunResult":
        if self.status != "dry_run_only":
            raise ValueError("DryRunResult status must be dry_run_only")
        if self.simulated is not True:
            raise ValueError("DryRunResult must be simulated")
        if self.task_executed:
            raise ValueError("DryRunResult must not execute tasks")
        if self.mutation_performed:
            raise ValueError("DryRunResult must not perform mutations")
        return self


