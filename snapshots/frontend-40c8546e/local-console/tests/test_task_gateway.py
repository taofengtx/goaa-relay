"""
GOAA Task Gateway Pure Data Models — Unit Tests (P4-T2)
========================================================
Test coverage requirements (per spec):

1. default execution mode is preview_only or blocked per spec
2. real execution cannot be represented as approved without explicit approval_state
3. forbidden / high-risk modes remain blocked by default
4. request model rejects empty task_id or invalid intent/action
5. result model carries blocked / preview-only status
6. evidence metadata can be represented without reading files
7. no mutable default lists/dicts
8. enum values are stable and lowercase/string-safe
9. serialization is deterministic if implemented
10. tests do not call network, subprocess, DO, Runtime, executor, or service restart
"""
import json
import sys
import pytest
from copy import deepcopy
from pathlib import Path

# Ensure the local-console module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from task_gateway import (
    ApprovalState,
    AuditLog,
    Decision,
    ExecutionMode,
    GatewayEvidencePackage,
    IntentExecutionPolicy,
    RollbackPlan,
    TaskRiskLevel,
    TaskRunRequest,
    TaskRunResult,
    ExecutionPlan,
    RunnerTarget,
    DryRunResult,
    TaskRunStatus,
    ThreeTruthLayers,
    TaskRiskClassification,
    classify_task_intent,
    build_blocked_result,
    build_task_run_request,
    get_default_approval_state,
    get_default_execution_mode,
    is_effectively_blocked,
    is_real_execution_represented,
    validate_task_run_request,
    validate_task_run_result,
)


# ══════════════════════════════════════════════════════════════
# 1. Default execution mode is preview_only or blocked per spec
# ══════════════════════════════════════════════════════════════

def test_default_mode_pure_chat_is_preview_only():
    """pure_chat defaults to preview_only (spec section 9)."""
    mode = get_default_execution_mode("pure_chat")
    assert mode == ExecutionMode.PREVIEW_ONLY


def test_default_mode_embed_is_blocked():
    """embed defaults to blocked (spec section 9)."""
    mode = get_default_execution_mode("embed")
    assert mode == ExecutionMode.BLOCKED


def test_default_mode_unknown_intent_is_blocked():
    """Unknown intent defaults to blocked."""
    mode = get_default_execution_mode("nonexistent_intent")
    assert mode == ExecutionMode.BLOCKED


def test_default_mode_topk_verify_is_readonly_dry_run():
    """topk_verify defaults to readonly_dry_run (spec section 9)."""
    mode = get_default_execution_mode("topk_verify")
    assert mode == ExecutionMode.READONLY_DRY_RUN


def test_default_mode_task_status_is_readonly_dry_run():
    """task_status defaults to readonly_dry_run (spec section 9)."""
    mode = get_default_execution_mode("task_status")
    assert mode == ExecutionMode.READONLY_DRY_RUN


def test_build_request_uses_default_execution_mode():
    """build_task_run_request applies default execution mode from policy matrix."""
    req = build_task_run_request(
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
    )
    assert req.execution_mode == ExecutionMode.PREVIEW_ONLY.value

    req2 = build_task_run_request(
        task_id="task-002",
        envelope_id="env-002",
        intent="embed",
    )
    assert req2.execution_mode == ExecutionMode.BLOCKED.value


def test_build_request_accepts_explicit_execution_mode():
    """Explicit execution_mode overrides the default."""
    req = build_task_run_request(
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        execution_mode=ExecutionMode.READONLY_DRY_RUN.value,
    )
    assert req.execution_mode == ExecutionMode.READONLY_DRY_RUN.value


def test_blocked_result_is_default_safe_posture():
    """build_blocked_result produces a blocked result with no execution flags."""
    result = build_blocked_result(request_id="req-001")
    assert result.execution_mode == ExecutionMode.BLOCKED.value
    assert result.status == TaskRunStatus.BLOCKED.value
    assert result.task_executed is False
    assert result.mutation_performed is False
    assert result.worker_started is False
    assert result.executor_enabled is False
    assert result.do_connected is False
    assert result.real_rag_query_executed is False
    assert result.embedding_rebuild_executed is False
    assert result.error_code == "BLOCKED_BY_DEFAULT"


# ══════════════════════════════════════════════════════════════
# 2. Real execution cannot be represented as approved without
#    explicit approval_state
# ══════════════════════════════════════════════════════════════

def test_approved_execution_requires_non_blocked_mode():
    """Real execution must use approved_local_action mode, not blocked."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.BLOCKED.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


def test_approved_execution_requires_approved_state():
    """Real execution requires approval_state=approved_by_tao."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.REQUIRED.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


def test_approved_execution_detected_when_all_conditions_met():
    """is_real_execution_represented returns True when conditions are met."""
    assert is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=True,
        mutation_performed=True,
        worker_started=True,
        executor_enabled=True,
        do_connected=False,
    )


def test_rejected_execution_not_represented():
    """Rejected state prevents real execution representation."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.REJECTED_BY_TAO.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


def test_expired_execution_not_represented():
    """Expired state prevents real execution representation."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.EXPIRED.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


# ══════════════════════════════════════════════════════════════
# 2B. Baton 8 safety: is_real_execution_represented strict conditions
# ══════════════════════════════════════════════════════════════

def test_real_execution_requires_approved_local_action_exactly():
    """readonly_dry_run + approved_by_tao does NOT count as real execution."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.READONLY_DRY_RUN.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


def test_real_execution_requires_approved_by_tao_exactly():
    """approved_local_action + not_required does NOT count as real execution."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.NOT_REQUIRED.value,
        task_executed=True,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
    )


def test_real_execution_with_real_rag_query():
    """real_rag_query_executed flag is recognized as real execution."""
    assert is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=False,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        real_rag_query_executed=True,
    )


def test_real_execution_with_embedding_rebuild():
    """embedding_rebuild_executed flag is recognized as real execution."""
    assert is_real_execution_represented(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=False,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        embedding_rebuild_executed=True,
    )


def test_preview_only_with_real_rag_is_not_real_execution():
    """Preview-only mode with rag flag still returns False."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=False,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        real_rag_query_executed=True,
    )


def test_blocked_with_rag_not_real_execution():
    """Blocked mode with rag flag still returns False."""
    assert not is_real_execution_represented(
        execution_mode=ExecutionMode.BLOCKED.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
        task_executed=False,
        mutation_performed=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        real_rag_query_executed=True,
        embedding_rebuild_executed=True,
    )


# ══════════════════════════════════════════════════════════════
# 3. Forbidden / high-risk modes remain blocked by default
# ══════════════════════════════════════════════════════════════

def test_embed_approval_required():
    """embed intent: default approval_state is required (spec section 9)."""
    state = get_default_approval_state("embed")
    assert state == ApprovalState.REQUIRED


def test_memory_fetch_approval_required():
    """memory_fetch intent: default approval_state is required (spec section 9)."""
    state = get_default_approval_state("memory_fetch")
    assert state == ApprovalState.REQUIRED


def test_unknown_intent_approval_required():
    """Unknown intent defaults to required approval."""
    state = get_default_approval_state("undefined_intent")
    assert state == ApprovalState.REQUIRED


def test_pure_chat_not_required():
    """pure_chat does not require approval."""
    state = get_default_approval_state("pure_chat")
    assert state == ApprovalState.NOT_REQUIRED


def test_is_effectively_blocked_for_embed():
    """embed with default values is effectively blocked."""
    assert is_effectively_blocked(
        execution_mode=ExecutionMode.BLOCKED.value,
        approval_state=ApprovalState.REQUIRED.value,
    )


def test_is_effectively_blocked_for_preview_only():
    """preview_only mode is effectively blocked (no real execution)."""
    assert is_effectively_blocked(
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
    )


def test_not_blocked_for_approved_local_action():
    """approved_local_action with approved state is not blocked."""
    assert not is_effectively_blocked(
        execution_mode=ExecutionMode.APPROVED_LOCAL_ACTION.value,
        approval_state=ApprovalState.APPROVED_BY_TAO.value,
    )


# ══════════════════════════════════════════════════════════════
# 4. Request model rejects empty task_id or invalid intent/action
# ══════════════════════════════════════════════════════════════

def test_validate_empty_request_id():
    """Validation rejects empty request_id."""
    req = TaskRunRequest(
        request_id="",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("request_id must be non-empty" in e for e in errors)


def test_validate_empty_task_id():
    """Validation rejects empty task_id."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("task_id must be non-empty" in e for e in errors)


def test_validate_empty_envelope_id():
    """Validation rejects empty envelope_id."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("envelope_id must be non-empty" in e for e in errors)


def test_validate_invalid_intent():
    """Validation rejects unknown intent."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="hack_the_planet",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("unknown intent" in e and "hack_the_planet" in e for e in errors)


def test_validate_invalid_risk_level():
    """Validation rejects invalid risk_level string."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L5_impossible",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("invalid risk_level" in e for e in errors)


def test_validate_invalid_execution_mode():
    """Validation rejects invalid execution_mode."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="lets_gooo",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert any("invalid execution_mode" in e for e in errors)


def test_validate_invalid_approval_state():
    """Validation rejects invalid approval_state."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="maybe_later",
    )
    errors = validate_task_run_request(req)
    assert any("invalid approval_state" in e for e in errors)


def test_validate_missing_digest_with_params():
    """Validation requires parameter_digest when normalized_parameters present."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
        normalized_parameters={"query": "hello"},
        parameter_digest="",
    )
    errors = validate_task_run_request(req)
    assert any("parameter_digest" in e for e in errors)


def test_validate_valid_request():
    """Valid request passes validation with no errors."""
    req = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    errors = validate_task_run_request(req)
    assert errors == []


# ══════════════════════════════════════════════════════════════
# 5. Result model carries blocked / preview-only status
# ══════════════════════════════════════════════════════════════

def test_blocked_result_status():
    """build_blocked_result carries blocked status."""
    result = build_blocked_result(request_id="req-001")
    assert result.status == TaskRunStatus.BLOCKED.value
    assert result.execution_mode == ExecutionMode.BLOCKED.value


def test_blocked_result_has_denial_reason():
    """build_blocked_result includes denial reason when provided."""
    result = build_blocked_result(
        request_id="req-001",
        denial_reason="Tao approval not granted",
    )
    assert "Tao approval not granted" in result.result_summary
    assert result.error_code == "BLOCKED"


def test_preview_only_result_not_blocked_by_validate():
    """Validate allows preview_only result as valid."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.PREVIEW_ONLY.value,
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
    )
    errors = validate_task_run_result(result)
    assert errors == []


def test_result_empty_run_id_rejected_by_validate():
    """Validation rejects result with empty run_id."""
    result = TaskRunResult(
        run_id="",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
    )
    errors = validate_task_run_result(result)
    assert any("run_id" in e for e in errors)


def test_result_empty_request_id_rejected_by_validate():
    """Validation rejects result with empty request_id."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
    )
    errors = validate_task_run_result(result)
    assert any("request_id" in e for e in errors)


def test_result_invalid_status_rejected_by_validate():
    """Validation rejects result with unknown status."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status="unknown_status",
        execution_mode=ExecutionMode.BLOCKED.value,
    )
    errors = validate_task_run_result(result)
    assert any("invalid status" in e for e in errors)


def test_blocked_result_must_not_have_task_executed():
    """Validation rejects blocked result that claims task_executed=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        task_executed=True,
    )
    errors = validate_task_run_result(result)
    assert any("blocked result must not have task_executed=True" in e for e in errors)


def test_blocked_result_must_not_have_mutation():
    """Validation rejects blocked result that claims mutation."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        mutation_performed=True,
    )
    errors = validate_task_run_result(result)
    assert any("blocked result must not have mutation_performed=True" in e for e in errors)


def test_blocked_result_must_not_have_worker_started():
    """Validation rejects blocked result that claims worker_started=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        worker_started=True,
    )
    errors = validate_task_run_result(result)
    assert any("worker_started" in e for e in errors)


def test_blocked_result_must_not_have_executor_enabled():
    """Validation rejects blocked result that claims executor_enabled=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        executor_enabled=True,
    )
    errors = validate_task_run_result(result)
    assert any("executor_enabled" in e for e in errors)


def test_blocked_result_must_not_have_do_connected():
    """Validation rejects blocked result that claims do_connected=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        do_connected=True,
    )
    errors = validate_task_run_result(result)
    assert any("do_connected" in e for e in errors)


def test_blocked_result_must_not_have_real_rag():
    """Validation rejects blocked result that claims real_rag_query_executed=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        real_rag_query_executed=True,
    )
    errors = validate_task_run_result(result)
    assert any("real_rag_query_executed" in e for e in errors)


def test_blocked_result_must_not_have_embedding_rebuild():
    """Validation rejects blocked result that claims embedding_rebuild_executed=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        embedding_rebuild_executed=True,
    )
    errors = validate_task_run_result(result)
    assert any("embedding_rebuild_executed" in e for e in errors)


def test_blocked_result_rejects_all_flags_together():
    """Validation rejects blocked result with ALL execution flags True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
        task_executed=True,
        mutation_performed=True,
        worker_started=True,
        executor_enabled=True,
        do_connected=True,
        real_rag_query_executed=True,
        embedding_rebuild_executed=True,
    )
    errors = validate_task_run_result(result)
    assert len(errors) >= 7


def test_preview_only_must_not_have_mutation():
    """Validation rejects preview_only result that claims mutation."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.PREVIEW_ONLY.value,
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        mutation_performed=True,
    )
    errors = validate_task_run_result(result)
    assert any("preview_only result must not have mutation_performed=True" in e for e in errors)


def test_preview_only_must_not_have_any_execution_flag():
    """Validation rejects preview_only result with ANY execution flag True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.PREVIEW_ONLY.value,
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        worker_started=True,
    )
    errors = validate_task_run_result(result)
    assert any("worker_started" in e for e in errors)


def test_preview_only_must_not_have_real_rag():
    """Validation rejects preview_only result with real_rag_query_executed=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.PREVIEW_ONLY.value,
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        real_rag_query_executed=True,
    )
    errors = validate_task_run_result(result)
    assert any("real_rag_query_executed" in e for e in errors)


def test_preview_only_must_not_have_embedding_rebuild():
    """Validation rejects preview_only result with embedding_rebuild_executed=True."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.PREVIEW_ONLY.value,
        execution_mode=ExecutionMode.PREVIEW_ONLY.value,
        embedding_rebuild_executed=True,
    )
    errors = validate_task_run_result(result)
    assert any("embedding_rebuild_executed" in e for e in errors)


def test_valid_blocked_result_passes():
    """A blocked result with all execution flags False passes validation."""
    result = TaskRunResult(
        run_id="run-001",
        request_id="req-001",
        status=TaskRunStatus.BLOCKED.value,
        execution_mode=ExecutionMode.BLOCKED.value,
    )
    errors = validate_task_run_result(result)
    assert errors == []


# ══════════════════════════════════════════════════════════════
# 6. Evidence metadata can be represented without reading files
# ══════════════════════════════════════════════════════════════

def test_gateway_evidence_package_constructable():
    """GatewayEvidencePackage can be constructed without file I/O."""
    evidence = GatewayEvidencePackage(
        evidence_package_id="EP-001",
        request_id="req-001",
        run_id="run-001",
        readonly=True,
        preview_only=False,
        evidence_summary="Dry-run completed, no files read",
    )
    assert evidence.evidence_package_id == "EP-001"
    assert evidence.readonly is True
    assert evidence.task_executed is False


def test_gateway_evidence_package_serialization():
    """GatewayEvidencePackage serialization is deterministic."""
    evidence = GatewayEvidencePackage(
        evidence_package_id="EP-001",
        request_id="req-001",
        run_id="run-001",
    )
    d1 = evidence.to_dict()
    d2 = evidence.to_dict()
    assert d1 == d2


def test_gateway_evidence_package_json():
    """GatewayEvidencePackage JSON output is valid JSON."""
    evidence = GatewayEvidencePackage(
        evidence_package_id="EP-001",
        request_id="req-001",
        run_id="run-001",
    )
    parsed = json.loads(evidence.to_json())
    assert parsed["evidence_package_id"] == "EP-001"
    assert parsed["request_id"] == "req-001"


def test_audit_log_constructable():
    """AuditLog can be constructed without file I/O or DB."""
    audit = AuditLog(
        audit_log_id="AUDIT-001",
        request_id="req-001",
        actor_id="tao",
        intent="embed",
        risk_level="L4_critical_runtime",
        approval_state="required",
        decision="blocked",
        denial_reason="Runtime mutation not authorized",
    )
    assert audit.audit_log_id == "AUDIT-001"
    assert audit.decision == Decision.BLOCKED.value


def test_audit_log_with_three_truths():
    """AuditLog can carry ThreeTruthLayers without file I/O."""
    truths = ThreeTruthLayers(
        runtime_truth={"active": True, "port": 5188},
        git_truth={"branch": "main", "commit": "abc123"},
        documentation_truth={"spec": "V0.1", "policy": "V1"},
    )
    audit = AuditLog(
        audit_log_id="AUDIT-002",
        request_id="req-002",
        actor_id="system",
        intent="task_status",
        risk_level="L0_information",
        approval_state="not_required",
        decision="allowed",
        three_truths=truths,
    )
    assert audit.three_truths is not None
    assert audit.three_truths.runtime_truth["port"] == 5188


# ══════════════════════════════════════════════════════════════
# 7. No mutable default lists/dicts
# ══════════════════════════════════════════════════════════════

def test_no_mutable_defaults_in_task_run_request():
    """TaskRunRequest uses field(default_factory) for mutable types."""
    req1 = TaskRunRequest(
        request_id="req-001",
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
        risk_level="L0_information",
        execution_mode="preview_only",
        approval_state="not_required",
    )
    req2 = TaskRunRequest(
        request_id="req-002",
        task_id="task-002",
        envelope_id="env-002",
        intent="topk_verify",
        risk_level="L1_readonly",
        execution_mode="readonly_dry_run",
        approval_state="not_required",
    )
    # Mutating one request's normalized_parameters must not affect the other
    req1.normalized_parameters["foo"] = "bar"
    assert "foo" not in req2.normalized_parameters


def test_no_mutable_defaults_in_task_run_result():
    """TaskRunResult does not share mutable defaults across instances."""
    r1 = TaskRunResult(run_id="r1", request_id="q1", status="blocked", execution_mode="blocked")
    r2 = TaskRunResult(run_id="r2", request_id="q2", status="blocked", execution_mode="blocked")
    # No mutable fields to test, but ensure no crash
    assert r1.run_id != r2.run_id


def test_no_mutable_defaults_in_rollback_plan():
    """RollbackPlan uses field(default_factory) for rollback_steps."""
    rp1 = RollbackPlan(rollback_available=True)
    rp2 = RollbackPlan(rollback_available=False)
    rp1.rollback_steps.append("step1")
    assert len(rp2.rollback_steps) == 0


def test_no_mutable_defaults_in_audit_log():
    """AuditLog uses field(default_factory) for dictionary fields."""
    a1 = AuditLog(
        audit_log_id="A1",
        request_id="R1",
        actor_id="test",
        intent="pure_chat",
        risk_level="L0_information",
        approval_state="not_required",
        decision="allowed",
    )
    a2 = AuditLog(
        audit_log_id="A2",
        request_id="R2",
        actor_id="test",
        intent="embed",
        risk_level="L4_critical_runtime",
        approval_state="required",
        decision="blocked",
    )
    a1.runtime_truth_snapshot["foo"] = "bar"
    assert "foo" not in a2.runtime_truth_snapshot


# ══════════════════════════════════════════════════════════════
# 8. Enum values are stable and lowercase/string-safe
# ══════════════════════════════════════════════════════════════

def test_execution_mode_values_stable():
    """ExecutionMode values are stable (not auto-numbered)."""
    assert ExecutionMode.PREVIEW_ONLY.value == "preview_only"
    assert ExecutionMode.READONLY_DRY_RUN.value == "readonly_dry_run"
    assert ExecutionMode.APPROVED_LOCAL_ACTION.value == "approved_local_action"
    assert ExecutionMode.BLOCKED.value == "blocked"


def test_approval_state_values_stable():
    """ApprovalState values are stable."""
    assert ApprovalState.NOT_REQUIRED.value == "not_required"
    assert ApprovalState.REQUIRED.value == "required"
    assert ApprovalState.APPROVED_BY_TAO.value == "approved_by_tao"
    assert ApprovalState.REJECTED_BY_TAO.value == "rejected_by_tao"
    assert ApprovalState.EXPIRED.value == "expired"


def test_task_risk_level_values_stable():
    """TaskRiskLevel values are stable and use L prefix convention."""
    assert TaskRiskLevel.L0_INFORMATION.value == "L0_information"
    assert TaskRiskLevel.L1_READONLY.value == "L1_readonly"
    assert TaskRiskLevel.L2_LOCAL_DRY_RUN.value == "L2_local_dry_run"
    assert TaskRiskLevel.L3_LOCAL_MUTATION.value == "L3_local_mutation"
    assert TaskRiskLevel.L4_CRITICAL_RUNTIME.value == "L4_critical_runtime"


def test_task_run_status_values_stable():
    """TaskRunStatus values are stable."""
    assert TaskRunStatus.BLOCKED.value == "blocked"
    assert TaskRunStatus.PREVIEW_ONLY.value == "preview_only"
    assert TaskRunStatus.DRY_RUN.value == "dry_run"
    assert TaskRunStatus.APPROVED_PENDING.value == "approved_pending"
    assert TaskRunStatus.COMPLETED.value == "completed"
    assert TaskRunStatus.FAILED.value == "failed"
    assert TaskRunStatus.REJECTED.value == "rejected"


def test_decision_values_stable():
    """Decision values are stable."""
    assert Decision.ALLOWED.value == "allowed"
    assert Decision.BLOCKED.value == "blocked"
    assert Decision.PREVIEW_ONLY.value == "preview_only"
    assert Decision.REQUIRES_APPROVAL.value == "requires_approval"
    assert Decision.REJECTED.value == "rejected"
    assert Decision.EXPIRED.value == "expired"


def test_all_enum_values_are_strings():
    """All enum values in task_gateway are strings (JSON-safe)."""
    for enum_cls in [ExecutionMode, ApprovalState, TaskRiskLevel, TaskRunStatus, Decision, IntentExecutionPolicy]:
        for member in enum_cls:
            assert isinstance(member.value, str), (
                f"{enum_cls.__name__}.{member.name} value is not str: {type(member.value)}"
            )


# ══════════════════════════════════════════════════════════════
# 9. Serialization is deterministic if implemented
# ══════════════════════════════════════════════════════════════

def test_task_run_request_serialization_deterministic():
    """TaskRunRequest serialization produces identical output across calls."""
    req = build_task_run_request(
        task_id="task-001",
        envelope_id="env-001",
        intent="pure_chat",
    )
    j1 = req.to_json(indent=2)
    j2 = req.to_json(indent=2)
    assert j1 == j2


def test_task_run_request_sha256_deterministic():
    """TaskRunRequest.compute_sha256() is deterministic."""
    req = build_task_run_request(
        task_id="task-001",
        envelope_id="env-001",
        intent="topk_verify",
    )
    h1 = req.compute_sha256()
    h2 = req.compute_sha256()
    assert h1 == h2


def test_task_run_result_serialization_deterministic():
    """TaskRunResult serialization produces identical output across calls."""
    result = build_blocked_result(request_id="req-001")
    j1 = result.to_json(indent=2)
    j2 = result.to_json(indent=2)
    assert j1 == j2


def test_task_run_result_sha256_deterministic():
    """TaskRunResult.compute_sha256() is deterministic."""
    result = build_blocked_result(request_id="req-001")
    h1 = result.compute_sha256()
    h2 = result.compute_sha256()
    assert h1 == h2


def test_evidence_package_serialization_deterministic():
    """GatewayEvidencePackage serialization is deterministic."""
    ep = GatewayEvidencePackage(
        evidence_package_id="EP-001",
        request_id="req-001",
        run_id="run-001",
        readonly=True,
        preview_only=True,
    )
    j1 = ep.to_json(indent=2)
    j2 = ep.to_json(indent=2)
    assert j1 == j2


def test_audit_log_serialization_deterministic():
    """AuditLog serialization is deterministic."""
    audit = AuditLog(
        audit_log_id="AUDIT-001",
        request_id="req-001",
        actor_id="test",
        intent="embed",
        risk_level="L4_critical_runtime",
        approval_state="required",
        decision="blocked",
    )
    j1 = audit.to_json(indent=2)
    j2 = audit.to_json(indent=2)
    assert j1 == j2


# ══════════════════════════════════════════════════════════════
# 10. No network / subprocess / DO / Runtime mutation
# ══════════════════════════════════════════════════════════════

def test_no_imports_with_side_effects():
    """Module imports should not import network/subprocess/IO modules."""
    import task_gateway
    module_source = task_gateway.__file__
    with open(module_source) as f:
        source = f.read()
    forbidden_imports = [
        "import subprocess", "from subprocess",
        "os.system", "os.popen",
        "import socket", "from socket",
        "import paramiko", "from paramiko",
        "import requests", "from requests",
        "import aiohttp", "from aiohttp",
        "import httpx", "from httpx",
        "import sqlite3", "from sqlite3",
        "import psycopg", "from psycopg",
        "import shutil", "from shutil",
    ]
    for forbid in forbidden_imports:
        assert forbid not in source, f"Forbidden import found in source: {forbid}"


def test_no_executor_enabled_by_default():
    """build_blocked_result never enables executor."""
    result = build_blocked_result(request_id="req-001")
    assert result.executor_enabled is False
    assert result.worker_started is False
    assert result.do_connected is False
    assert result.real_rag_query_executed is False
    assert result.embedding_rebuild_executed is False


def test_rollback_plan_defaults():
    """RollbackPlan has safe defaults for optional fields."""
    rp = RollbackPlan(rollback_available=False)
    assert rp.rollback_steps == []
    assert rp.rollback_risk == ""
    assert rp.rollback_owner == ""
    assert rp.rollback_test == ""


def test_rollback_plan_serialization():
    """RollbackPlan serialization works."""
    rp = RollbackPlan(
        rollback_available=True,
        rollback_steps=["git checkout main", "systemctl restart"],
        rollback_risk="medium",
        rollback_owner="tao",
        rollback_test="verify 5188 responds",
    )
    d = rp.to_dict()
    assert d["rollback_available"] is True
    assert len(d["rollback_steps"]) == 2
    assert d["rollback_risk"] == "medium"
    # JSON round-trip
    parsed = json.loads(rp.to_json())
    assert parsed["rollback_available"] is True


def test_build_request_with_rollback_plan():
    """build_task_run_request accepts RollbackPlan."""
    rp = RollbackPlan(rollback_available=True, rollback_steps=["git revert"])
    req = build_task_run_request(
        task_id="task-001",
        envelope_id="env-001",
        intent="embed",
        rollback_plan=rp,
    )
    assert req.rollback_plan is not None
    assert req.rollback_plan.rollback_available is True


def test_three_truth_layers_serialization():
    """ThreeTruthLayers serializes correctly."""
    truths = ThreeTruthLayers(
        runtime_truth={"runtime": "systemd", "port": 5188},
        git_truth={"branch": "main", "commit": "abc"},
        documentation_truth={"spec": "V0.1"},
    )
    d = truths.to_dict()
    assert d["runtime_truth"]["port"] == 5188
    assert d["git_truth"]["commit"] == "abc"
    assert d["documentation_truth"]["spec"] == "V0.1"



# Package 5 Task 2 — ExecutionPlan / RunnerTarget / DryRunResult models

def test_package5_runner_target_defaults_are_non_executing():
    target = RunnerTarget()
    assert target.target_type == "disabled"
    assert target.executor_required is False
    assert target.executor_enabled is False
    assert target.real_execution_allowed is False


def test_package5_runner_target_rejects_executor_enabled():
    with pytest.raises(ValueError):
        RunnerTarget(executor_enabled=True)


def test_package5_runner_target_rejects_real_execution_allowed():
    with pytest.raises(ValueError):
        RunnerTarget(real_execution_allowed=True)


def test_package5_execution_plan_defaults_to_plan_only_no_execution():
    plan = ExecutionPlan(
        plan_id="plan_001",
        request_id="req_001",
        task_id="task_001",
        intent="task_status",
    )
    assert plan.execution_mode == ExecutionMode.PLAN_ONLY
    assert plan.no_execution is True
    assert plan.source == "execution_plan_gateway"
    assert plan.runner_target.executor_enabled is False
    assert plan.runner_target.real_execution_allowed is False


def test_package5_execution_plan_rejects_no_execution_false():
    with pytest.raises(ValueError):
        ExecutionPlan(
            plan_id="plan_001",
            request_id="req_001",
            task_id="task_001",
            intent="task_status",
            no_execution=False,
        )


def test_package5_execution_plan_rejects_runner_executor_enabled():
    with pytest.raises(ValueError):
        ExecutionPlan(
            plan_id="plan_001",
            request_id="req_001",
            task_id="task_001",
            intent="task_status",
            runner_target=RunnerTarget.model_construct(
                target_type="disabled",
                executor_required=False,
                executor_enabled=True,
                real_execution_allowed=False,
            ),
        )


def test_package5_execution_plan_rejects_runner_real_execution_allowed():
    with pytest.raises(ValueError):
        ExecutionPlan(
            plan_id="plan_001",
            request_id="req_001",
            task_id="task_001",
            intent="task_status",
            runner_target=RunnerTarget.model_construct(
                target_type="disabled",
                executor_required=False,
                executor_enabled=False,
                real_execution_allowed=True,
            ),
        )


def test_package5_dry_run_result_defaults_are_simulated_non_executing():
    result = DryRunResult(dry_run_id="dry_001", plan_id="plan_001")
    assert result.status == "dry_run_only"
    assert result.simulated is True
    assert result.task_executed is False
    assert result.mutation_performed is False


def test_package5_dry_run_result_rejects_task_executed():
    with pytest.raises(ValueError):
        DryRunResult(dry_run_id="dry_001", plan_id="plan_001", task_executed=True)


def test_package5_dry_run_result_rejects_mutation_performed():
    with pytest.raises(ValueError):
        DryRunResult(dry_run_id="dry_001", plan_id="plan_001", mutation_performed=True)


# Package 5 Task 4 — Strategy Matrix + Risk Classification

def test_p5_t4_low_risk_plan_only_intents_classification():
    c_status = classify_task_intent("task_status")
    assert c_status.intent == "task_status"
    assert c_status.risk_level == TaskRiskLevel.L0_INFORMATION
    assert c_status.strategy == "plan_only"
    assert c_status.execution_policy == IntentExecutionPolicy.NO_MUTATION
    assert c_status.approval_required is False
    assert c_status.blocked_reason is None
    assert c_status.no_real_execution is True

    c_verify = classify_task_intent("topk_verify")
    assert c_verify.intent == "topk_verify"
    assert c_verify.risk_level == TaskRiskLevel.L1_READONLY
    assert c_verify.strategy == "plan_only"
    assert c_verify.execution_policy == IntentExecutionPolicy.NO_REAL_RAG
    assert c_verify.approval_required is False
    assert c_verify.blocked_reason is None
    assert c_verify.no_real_execution is True


def test_p5_t4_pure_chat_classification():
    c_chat = classify_task_intent("pure_chat")
    assert c_chat.intent == "pure_chat"
    assert c_chat.risk_level == TaskRiskLevel.L0_INFORMATION
    assert c_chat.strategy == "preview_only"
    assert c_chat.execution_policy == IntentExecutionPolicy.NEVER
    assert c_chat.approval_required is False
    assert c_chat.no_real_execution is True


def test_p5_t4_memory_fetch_blocked_classification():
    c_mem = classify_task_intent("memory_fetch")
    assert c_mem.intent == "memory_fetch"
    assert c_mem.strategy == "blocked"
    assert c_mem.approval_required is True
    assert c_mem.blocked_reason is not None
    assert "Memory fetch is blocked" in c_mem.blocked_reason
    assert c_mem.no_real_execution is True


def test_p5_t4_embed_vector_retrieval_blocked_classification():
    for intent in ("embed", "vector", "retrieval"):
        c = classify_task_intent(intent)
        assert c.intent == intent
        assert c.risk_level == TaskRiskLevel.L4_CRITICAL_RUNTIME
        assert c.strategy == "blocked"
        assert c.approval_required is True
        assert c.blocked_reason is not None
        assert c.no_real_execution is True


def test_p5_t4_high_risk_intents_classified_high_risk_blocked():
    high_risk_intents = [
        "executor",
        "run_executor",
        "shell",
        "shell_command",
        "exec",
        "system_exec",
        "deploy",
        "runtime_mutation",
        "systemctl",
        "doctl",
        "git_push",
        "git_merge",
        "merge_branch",
        "db_write",
    ]
    for intent in high_risk_intents:
        c = classify_task_intent(intent)
        assert c.intent == intent, f"intent={intent}"
        assert c.risk_level == TaskRiskLevel.L4_CRITICAL_RUNTIME, f"intent={intent} risk"
        assert c.strategy == "blocked", f"intent={intent} strategy"
        assert c.execution_policy == IntentExecutionPolicy.NEVER, f"intent={intent} policy"
        assert c.approval_required is True, f"intent={intent} approval"
        assert c.blocked_reason is not None, f"intent={intent} reason"
        assert "blocked" in c.blocked_reason.lower(), f"intent={intent} reason text"
        assert c.no_real_execution is True, f"intent={intent} no_real_execution"


def test_p5_t4_unknown_intent_classified_blocked():
    c = classify_task_intent("some_random_unrecognized_intent")
    assert c.intent == "some_random_unrecognized_intent"
    assert c.risk_level == TaskRiskLevel.L4_CRITICAL_RUNTIME
    assert c.strategy == "blocked"
    assert c.execution_policy == IntentExecutionPolicy.NEVER
    assert c.approval_required is True
    assert c.blocked_reason is not None
    assert "Unknown intent" in c.blocked_reason
    assert c.no_real_execution is True


def test_p5_t4_classification_model_and_plan_integration():
    classification = classify_task_intent("task_status")
    plan = ExecutionPlan(
        plan_id="plan_t4_001",
        request_id="req_t4_001",
        task_id="task_t4_001",
        intent="task_status",
        strategy=classification.strategy,
        execution_policy=classification.execution_policy.value,
        approval_required=classification.approval_required,
        risk_classification=classification,
    )
    assert plan.strategy == "plan_only"
    assert plan.execution_policy == "no_mutation"
    assert plan.approval_required is False
    assert plan.risk_classification is not None
    assert plan.risk_classification.intent == "task_status"
    assert plan.no_execution is True
    assert plan.runner_target.executor_enabled is False
    assert plan.runner_target.real_execution_allowed is False

    dr = DryRunResult(
        dry_run_id="dr_t4_001",
        plan_id=plan.plan_id,
        risk_classification=classification,
    )
    assert dr.risk_classification is not None
    assert dr.risk_classification.strategy == "plan_only"
    assert dr.task_executed is False
    assert dr.mutation_performed is False

