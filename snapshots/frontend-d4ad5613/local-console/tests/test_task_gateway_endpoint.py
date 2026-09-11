"""
GOAA Task Gateway Endpoint — Unit Tests (P4-T3 + P4-T4)
=========================================================
Tests for POST /tasks/run endpoint with approval gate enforcement.

Coverage:
- P4-T3 skeleton: endpoint exists, blocked/preview-only, no execution
- P4-T4 approval gate: approval_state enforces blocked/preview-only correctly
- No execution flags ever true
- Baton 8: execution_mode never approved_local_action or readonly_dry_run
- P4-T6: /ai/chat task_gateway_result integration
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── Valid approval state values for tests ──
_NOT_REQUIRED = "not_required"
_APPROVED = "approved_by_tao"
_REQUIRED = "required"
_REJECTED = "rejected_by_tao"
_EXPIRED = "expired"
_INVALID_STATE = "invalid_state"


# ══════════════════════════════════════════════════════════════
# P4-T3: Basic endpoint existence
# ══════════════════════════════════════════════════════════════

def test_endpoint_exists():
    """POST /tasks/run returns 200."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-001", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════
# Blocked intents (unaffected by approval_state)
# ══════════════════════════════════════════════════════════════

def test_unknown_intent_is_blocked():
    """Unknown intent returns blocked regardless of approval_state."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-unknown", "intent": "nonexistent_intent",
    })
    data = resp.json()
    assert data["ok"] is False
    assert "blocked" in data["run"]["status"]
    assert data["blocked_reason"]


def test_embed_intent_is_blocked():
    """High-risk embed is blocked regardless of approval_state."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-embed", "intent": "embed",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"


def test_memory_fetch_blocked():
    """memory_fetch is not preview-safe, so blocked."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-memory", "intent": "memory_fetch",
    })
    data = resp.json()
    assert data["ok"] is False


# ══════════════════════════════════════════════════════════════
# P4-T4: Approval gate — blocking states
# ══════════════════════════════════════════════════════════════

def test_approval_required_blocks_pure_chat():
    """approval_state=required blocks pure_chat."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-req", "intent": "pure_chat",
        "approval_state": _REQUIRED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"
    assert "required" in data["blocked_reason"].lower()


def test_approval_rejected_blocks_pure_chat():
    """approval_state=rejected_by_tao blocks pure_chat."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-rej", "intent": "pure_chat",
        "approval_state": _REJECTED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"
    assert "rejected" in data["blocked_reason"].lower()


def test_approval_expired_blocks_pure_chat():
    """approval_state=expired blocks pure_chat."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-exp", "intent": "pure_chat",
        "approval_state": _EXPIRED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"
    assert "expired" in data["blocked_reason"].lower()


def test_missing_approval_state_blocks():
    """Missing approval_state blocks pure_chat."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-nostate", "intent": "pure_chat",
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"


def test_invalid_approval_state_blocks():
    """Invalid approval_state value blocks pure_chat."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-invalid", "intent": "pure_chat",
        "approval_state": _INVALID_STATE,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"
    assert "invalid" in data["blocked_reason"].lower()


# ══════════════════════════════════════════════════════════════
# P4-T4: Approval gate — allowing states
# ══════════════════════════════════════════════════════════════

def test_approval_not_required_allows_pure_chat_preview():
    """approval_state=not_required allows pure_chat as preview_only."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-nr", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["run"]["status"] == "preview_only"


def test_approval_approved_allows_pure_chat_preview():
    """approval_state=approved_by_tao allows pure_chat as preview_only (not execution)."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["run"]["status"] == "preview_only"
    # Must not execute
    assert data["run"]["task_executed"] is False


def test_approval_approved_task_status_preview():
    """approval_state=approved_by_tao allows task_status as preview_only."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap-ts", "intent": "task_status",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["run"]["status"] == "preview_only"


def test_approval_approved_topk_verify_preview():
    """approval_state=approved_by_tao allows topk_verify as preview_only."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap-tk", "intent": "topk_verify",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["run"]["status"] == "preview_only"


# ══════════════════════════════════════════════════════════════
# P4-T4: approved_by_tao still blocks non-preview-safe intents
# ══════════════════════════════════════════════════════════════

def test_approved_embed_still_blocked():
    """Even approved_by_tao does NOT unblock high-risk embed."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap-emb", "intent": "embed",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"


def test_approved_memory_fetch_still_blocked():
    """Even approved_by_tao does NOT unblock non-preview-safe memory_fetch."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap-mem", "intent": "memory_fetch",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"


def test_approved_unknown_still_blocked():
    """Even approved_by_tao does NOT unblock unknown intent."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ap-unk", "intent": "nonexistent_xyz",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["ok"] is False
    assert data["run"]["status"] == "blocked"


# ══════════════════════════════════════════════════════════════
# execution_mode never approved_local_action or readonly_dry_run
# ══════════════════════════════════════════════════════════════

def test_execution_mode_never_approved_local_action():
    """No response ever returns execution_mode=approved_local_action."""
    payloads = [
        {"task_id": "t1", "intent": "pure_chat", "approval_state": _APPROVED},
        {"task_id": "t2", "intent": "pure_chat", "approval_state": _NOT_REQUIRED},
        {"task_id": "t3", "intent": "task_status", "approval_state": _APPROVED},
        {"task_id": "t4", "intent": "topk_verify", "approval_state": _NOT_REQUIRED},
        {"task_id": "t5", "intent": "embed", "approval_state": _APPROVED},
        {"task_id": "t6", "intent": "memory_fetch", "approval_state": _APPROVED},
        {"task_id": "t7", "intent": "pure_chat", "approval_state": _REQUIRED},
        {"task_id": "t8", "intent": "pure_chat", "approval_state": _REJECTED},
    ]
    for p in payloads:
        resp = client.post("/tasks/run", json=p)
        data = resp.json()
        assert data["run"]["execution_mode"] != "approved_local_action", f"for {p}"


def test_execution_mode_never_readonly_dry_run():
    """No response ever returns execution_mode=readonly_dry_run."""
    payloads = [
        {"task_id": "t1", "intent": "pure_chat", "approval_state": _APPROVED},
        {"task_id": "t2", "intent": "pure_chat", "approval_state": _NOT_REQUIRED},
        {"task_id": "t3", "intent": "task_status", "approval_state": _APPROVED},
        {"task_id": "t4", "intent": "topk_verify", "approval_state": _NOT_REQUIRED},
        {"task_id": "t5", "intent": "embed", "approval_state": _APPROVED},
        {"task_id": "t6", "intent": "pure_chat", "approval_state": _REQUIRED},
        {"task_id": "t7", "intent": "pure_chat", "approval_state": _EXPIRED},
    ]
    for p in payloads:
        resp = client.post("/tasks/run", json=p)
        data = resp.json()
        assert data["run"]["execution_mode"] != "readonly_dry_run", f"for {p}"


# ══════════════════════════════════════════════════════════════
# All execution flags false across all approval states
# ══════════════════════════════════════════════════════════════

def test_execution_flags_false_across_approval_states():
    """All execution flags false for every approval_state + preview-safe intent."""
    for state in [_NOT_REQUIRED, _APPROVED, _REQUIRED, _REJECTED, _EXPIRED, None, _INVALID_STATE]:
        payload = {"task_id": f"test-{state or 'none'}", "intent": "pure_chat"}
        if state is not None:
            payload["approval_state"] = state
        resp = client.post("/tasks/run", json=payload)
        data = resp.json()
        run = data["run"]
        assert run["task_executed"] is False, f"task_executed for state={state}"
        assert run["mutation_performed"] is False, f"mutation_performed for state={state}"
        assert run["worker_started"] is False, f"worker_started for state={state}"
        assert run["executor_enabled"] is False, f"executor_enabled for state={state}"
        assert run["do_connected"] is False, f"do_connected for state={state}"
        assert run["real_rag_query_executed"] is False, f"real_rag_query for state={state}"
        assert run["embedding_rebuild_executed"] is False, f"embed_rebuild for state={state}"


def test_execution_flags_false_non_preview_intents():
    """All execution flags false for blocked non-preview intents too."""
    for intent in ["embed", "memory_fetch", "approve_task", "reject_task", "unknown_xxx"]:
        resp = client.post("/tasks/run", json={
            "task_id": f"test-{intent}", "intent": intent,
        })
        data = resp.json()
        run = data["run"]
        assert run["task_executed"] is False
        assert run["mutation_performed"] is False
        assert run["worker_started"] is False
        assert run["executor_enabled"] is False
        assert run["do_connected"] is False
        assert run["real_rag_query_executed"] is False
        assert run["embedding_rebuild_executed"] is False


# ══════════════════════════════════════════════════════════════
# Baton 8: execution_mode semantics (preview_only / blocked only)
# ══════════════════════════════════════════════════════════════

def test_approved_preview_execution_mode_is_preview_only():
    """Approved preview-safe intent returns execution_mode=preview_only."""
    for intent in ["pure_chat", "task_status", "topk_verify"]:
        resp = client.post("/tasks/run", json={
            "task_id": f"test-{intent}", "intent": intent,
            "approval_state": _APPROVED,
        })
        data = resp.json()
        assert data["run"]["execution_mode"] == "preview_only", f"for {intent}"


def test_not_required_preview_execution_mode_is_preview_only():
    """Not_required preview-safe intent returns execution_mode=preview_only."""
    for intent in ["pure_chat", "task_status", "topk_verify"]:
        resp = client.post("/tasks/run", json={
            "task_id": f"test-{intent}", "intent": intent,
            "approval_state": _NOT_REQUIRED,
        })
        data = resp.json()
        assert data["run"]["execution_mode"] == "preview_only", f"for {intent}"


def test_blocked_intents_execution_mode_is_blocked():
    """All blocked intents return execution_mode=blocked."""
    for intent in ["embed", "memory_fetch", "approve_task", "reject_task", "nonexistent_xyz"]:
        resp = client.post("/tasks/run", json={
            "task_id": f"test-{intent}", "intent": intent,
        })
        data = resp.json()
        assert data["run"]["execution_mode"] == "blocked", f"expected blocked for {intent}"


def test_approval_blocked_execution_mode_is_blocked():
    """Approval-blocked requests return execution_mode=blocked."""
    for state in [_REQUIRED, _REJECTED, _EXPIRED]:
        resp = client.post("/tasks/run", json={
            "task_id": f"test-{state}", "intent": "pure_chat",
            "approval_state": state,
        })
        data = resp.json()
        assert data["run"]["execution_mode"] == "blocked", f"for state={state}"


def test_all_response_modes_valid():
    """Every /tasks/run response has execution_mode only in {blocked, preview_only}."""
    valid = {"blocked", "preview_only"}
    scenarios = [
        {"intent": "pure_chat", "approval_state": _APPROVED},
        {"intent": "pure_chat", "approval_state": _NOT_REQUIRED},
        {"intent": "pure_chat", "approval_state": _REQUIRED},
        {"intent": "pure_chat", "approval_state": _REJECTED},
        {"intent": "pure_chat", "approval_state": _EXPIRED},
        {"intent": "task_status", "approval_state": _APPROVED},
        {"intent": "topk_verify", "approval_state": _NOT_REQUIRED},
        {"intent": "embed"},
        {"intent": "memory_fetch"},
        {"intent": "approve_task"},
        {"intent": "reject_task"},
        {"intent": "unknown_intent_abc"},
    ]
    for s in scenarios:
        payload = {"task_id": f"test-{s['intent']}", "intent": s["intent"]}
        if "approval_state" in s:
            payload["approval_state"] = s["approval_state"]
        resp = client.post("/tasks/run", json=payload)
        data = resp.json()
        mode = data["run"]["execution_mode"]
        assert mode in valid, f"invalid mode '{mode}' for {s}"


# ══════════════════════════════════════════════════════════════
# No dangerous flags in any response
# ══════════════════════════════════════════════════════════════

def test_no_dangerous_flags():
    """All dangerous flags remain False for all intents + approval states."""
    scenarios = [
        {"intent": "pure_chat", "approval_state": _APPROVED},
        {"intent": "pure_chat", "approval_state": _NOT_REQUIRED},
        {"intent": "pure_chat", "approval_state": _REQUIRED},
        {"intent": "task_status", "approval_state": _APPROVED},
        {"intent": "topk_verify", "approval_state": _NOT_REQUIRED},
        {"intent": "embed"},
        {"intent": "memory_fetch"},
        {"intent": "approve_task"},
    ]
    for s in scenarios:
        payload = {"task_id": f"test-{s['intent']}", "intent": s["intent"]}
        if "approval_state" in s:
            payload["approval_state"] = s["approval_state"]
        resp = client.post("/tasks/run", json=payload)
        data = resp.json()
        run = data["run"]
        assert run["worker_started"] is False
        assert run["executor_enabled"] is False
        assert run["do_connected"] is False
        assert run["real_rag_query_executed"] is False
        assert run["embedding_rebuild_executed"] is False


# ══════════════════════════════════════════════════════════════
# Response schema stability
# ══════════════════════════════════════════════════════════════

def test_response_has_required_fields():
    """Response always carries ok, run, blocked_reason, note."""
    resp = client.post("/tasks/run", json={
        "task_id": "test", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    data = resp.json()
    assert "ok" in data
    assert "run" in data
    assert "blocked_reason" in data
    assert "note" in data


def test_blocked_response_has_error_code():
    """Blocked response carries error_code in run."""
    resp = client.post("/tasks/run", json={
        "task_id": "test", "intent": "embed",
    })
    data = resp.json()
    assert "error_code" in data["run"]
    assert data["run"]["error_code"] != ""


def test_preview_response_no_error_code():
    """Preview response has empty error_code."""
    resp = client.post("/tasks/run", json={
        "task_id": "test", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    code = data["run"].get("error_code", "")
    assert code == "" or code is None


# ══════════════════════════════════════════════════════════════
# No forbidden imports
# ══════════════════════════════════════════════════════════════

def test_endpoint_source_no_forbidden_imports():
    """main.py should not import network/subprocess/DB modules."""
    import main as main_module
    with open(main_module.__file__) as f:
        source = f.read()
    forbidden = [
        "import subprocess", "from subprocess",
        "import sqlite3", "from sqlite3",
        "import psycopg", "from psycopg",
        "import requests", "from requests",
        "os.system", "os.popen",
        "import paramiko", "from paramiko",
    ]
    for forbid in forbidden:
        assert forbid not in source, f"Forbidden import: {forbid}"


# ══════════════════════════════════════════════════════════════
# P4-T5: AuditLog & GatewayEvidencePackage metadata
# ══════════════════════════════════════════════════════════════

def test_audit_log_present_in_approved_response():
    """AuditLog dict is present in preview_only response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-audit-ok", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["audit_log"] is not None
    assert "audit_log_id" in data["audit_log"]
    assert data["audit_log"]["intent"] == "pure_chat"


def test_audit_log_present_in_blocked_response():
    """AuditLog dict is present in blocked response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-audit-block", "intent": "embed",
    })
    data = resp.json()
    assert data["audit_log"] is not None
    assert data["audit_log"]["decision"] == "blocked"


def test_evidence_package_present_in_approved_response():
    """GatewayEvidencePackage dict is present in preview_only response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evid-ok", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    assert data["evidence_package"] is not None
    assert "evidence_package_id" in data["evidence_package"]
    assert data["evidence_package"]["task_executed"] is False
    assert data["evidence_package"]["preview_only"] is True


def test_evidence_package_present_in_blocked_response():
    """GatewayEvidencePackage dict is present in blocked response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evid-block", "intent": "embed",
    })
    data = resp.json()
    assert data["evidence_package"] is not None
    assert data["evidence_package"]["task_executed"] is False
    assert data["evidence_package"]["preview_only"] is False


def test_audit_log_decision_preview_only():
    """AuditLog has decision=preview_only for approved preview-safe intent."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-decision-preview", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    data = resp.json()
    assert data["audit_log"]["decision"] == "preview_only"


def test_audit_log_decision_blocked_for_required():
    """AuditLog has decision=blocked for approval_state=required."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-decision-block", "intent": "pure_chat",
        "approval_state": _REQUIRED,
    })
    data = resp.json()
    assert data["audit_log"]["decision"] == "blocked"


def test_evidence_execution_flags_all_false():
    """All execution flags in evidence are False regardless of outcome."""
    for intent, state in [
        ("pure_chat", _APPROVED),
        ("pure_chat", _NOT_REQUIRED),
        ("pure_chat", _REQUIRED),
        ("embed", None),
        ("memory_fetch", None),
    ]:
        payload = {"task_id": f"test-evflags-{intent}", "intent": intent}
        if state:
            payload["approval_state"] = state
        resp = client.post("/tasks/run", json=payload)
        data = resp.json()
        ev = data["evidence_package"]
        assert ev is not None, f"missing evidence for {intent}"
        assert ev["task_executed"] is False, f"task_executed for {intent}"
        assert ev["runtime_mutation"] is False, f"runtime_mutation for {intent}"
        assert ev["worker_started"] is False, f"worker_started for {intent}"
        assert ev["executor_enabled"] is False, f"executor_enabled for {intent}"
        assert ev["do_connected"] is False, f"do_connected for {intent}"
        assert ev["real_rag_query_executed"] is False, f"real_rag_query for {intent}"
        assert ev["embedding_rebuild_executed"] is False, f"embed_rebuild for {intent}"


def test_audit_log_has_required_fields():
    """AuditLog has all required fields."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-audit-fields", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    aud = resp.json()["audit_log"]
    assert aud is not None
    for field in ["audit_log_id", "request_id", "actor_id", "intent",
                  "risk_level", "approval_state", "decision", "created_at_utc"]:
        assert field in aud, f"Missing audit_log field: {field}"


def test_evidence_package_has_required_fields():
    """GatewayEvidencePackage has all required fields."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evid-fields", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    ev = resp.json()["evidence_package"]
    assert ev is not None
    for field in ["evidence_package_id", "request_id", "run_id",
                  "task_executed", "preview_only", "readonly",
                  "evidence_summary", "created_at_utc"]:
        assert field in ev, f"Missing evidence field: {field}"
    # All execution flags
    for flag in ["runtime_mutation", "worker_started", "executor_enabled",
                 "do_connected", "real_rag_query_executed", "embedding_rebuild_executed"]:
        assert flag in ev, f"Missing evidence flag: {flag}"


# ══════════════════════════════════════════════════════════════
# P4-T5 Baton 8 fix: explicit safety metadata fields
# ══════════════════════════════════════════════════════════════

def test_audit_log_persisted_false():
    """audit_log['persisted'] is False."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-persist", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    aud = resp.json()["audit_log"]
    assert aud["persisted"] is False


def test_audit_log_source_tasks_run_gateway():
    """audit_log['source'] == 'tasks_run_gateway'."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-source", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    aud = resp.json()["audit_log"]
    assert aud["source"] == "tasks_run_gateway"


def test_audit_log_event_type_preview():
    """audit_log event_type is task_run_preview_only for preview response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evtype", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    aud = resp.json()["audit_log"]
    assert aud["event_type"] == "task_run_preview_only"


def test_audit_log_event_type_blocked():
    """audit_log event_type is task_run_blocked for blocked response."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evtype-blk", "intent": "embed",
    })
    aud = resp.json()["audit_log"]
    assert aud["event_type"] == "task_run_blocked"


def test_audit_log_has_task_id():
    """audit_log includes task_id from request."""
    resp = client.post("/tasks/run", json={
        "task_id": "my-specific-task-42", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    aud = resp.json()["audit_log"]
    assert aud["task_id"] == "my-specific-task-42"


def test_evidence_no_persistence_true():
    """evidence_package['no_persistence'] is True."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-np", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    ev = resp.json()["evidence_package"]
    assert ev["no_persistence"] is True


def test_evidence_no_execution_true():
    """evidence_package['no_execution'] is True."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-ne", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    ev = resp.json()["evidence_package"]
    assert ev["no_execution"] is True


def test_evidence_source_tasks_run_gateway():
    """evidence_package['source'] == 'tasks_run_gateway'."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evsrc", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    ev = resp.json()["evidence_package"]
    assert ev["source"] == "tasks_run_gateway"


def test_evidence_has_intent_and_decision():
    """evidence_package includes intent and decision fields."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evfield", "intent": "task_status",
        "approval_state": _APPROVED,
    })
    ev = resp.json()["evidence_package"]
    assert ev["intent"] == "task_status"
    assert ev["decision"] == "preview_only"


def test_evidence_has_approval_state():
    """evidence_package includes approval_state."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evas", "intent": "pure_chat",
        "approval_state": _NOT_REQUIRED,
    })
    ev = resp.json()["evidence_package"]
    assert ev["approval_state"] == "not_required"


def test_evidence_blocked_has_blocked_reason():
    """evidence_package includes blocked_reason for blocked requests."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-evbr", "intent": "embed",
    })
    ev = resp.json()["evidence_package"]
    assert ev["blocked_reason"]  # non-empty


def test_no_database_or_file_references():
    """No database/file write references in audit or evidence."""
    resp = client.post("/tasks/run", json={
        "task_id": "test-nodb", "intent": "pure_chat",
        "approval_state": _APPROVED,
    })
    data = resp.json()
    for key in ["audit_log", "evidence_package"]:
        s = str(data[key]).lower()
        assert "sqlite" not in s, f"sqlite in {key}"
        assert "psycopg" not in s, f"psycopg in {key}"
        assert "file_write" not in s, f"file_write in {key}"
        assert "open(" not in s, f"open( in {key}"


# ══════════════════════════════════════════════════════════════
# P4-T6: /ai/chat task_gateway_result integration
# ══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def mock_router_chat():
    """Mock the /chat POST to the DO Router so /ai/chat returns a known response."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={
        "ok": True,
        "response": {
            "text": "Hello from mock router",
            "model": "deepseek-mock",
        },
        "session_id": "mock-sess-001",
        "duration_ms": 100,
    })

    async def mock_post(*args, **kwargs):
        return mock_resp

    # Use AsyncMock so __aenter__ and __aexit__ work properly
    mock_client = MagicMock()
    mock_client.post = mock_post

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_client
    mock_async_client.__aexit__.return_value = None

    with patch("main.httpx.AsyncClient", return_value=mock_async_client):
        yield


class TestAIChatTaskGatewayResult:

    def test_gateway_result_present_for_executable_task(self):
        """task_gateway_result is present when intent is executable (not pure_chat)."""
        resp = client.post("/ai/chat", json={
            "prompt": "show me the task status",
        })
        data = resp.json()
        assert data["ok"] is True
        assert data["task_gateway_result"] is not None
        gw = data["task_gateway_result"]
        assert "execution_mode" in gw
        assert "status" in gw
        assert "audit_log" in gw
        assert "evidence_package" in gw

    def test_gateway_result_none_for_pure_chat(self):
        """task_gateway_result is None when intent is pure_chat."""
        resp = client.post("/ai/chat", json={
            "prompt": "hello how are you",
        })
        data = resp.json()
        assert data["ok"] is True
        # pure_chat has no gateway result
        assert data["task_gateway_result"] is None

    def test_gateway_result_audit_persisted_false(self):
        """task_gateway_result audit_log has persisted=False."""
        resp = client.post("/ai/chat", json={
            "prompt": "show task status",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert gw["audit_log"]["persisted"] is False

    def test_gateway_result_evidence_no_execution_true(self):
        """task_gateway_result evidence_package has no_execution=True."""
        resp = client.post("/ai/chat", json={
            "prompt": "check task status",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert gw["evidence_package"]["no_execution"] is True

    def test_gateway_result_evidence_no_persistence_true(self):
        """task_gateway_result evidence_package has no_persistence=True."""
        resp = client.post("/ai/chat", json={
            "prompt": "topk verification please",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert gw["evidence_package"]["no_persistence"] is True

    def test_gateway_result_source_tasks_run_gateway(self):
        """Both audit_log and evidence_package have source=tasks_run_gateway."""
        resp = client.post("/ai/chat", json={
            "prompt": "verify topk results",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert gw["audit_log"]["source"] == "tasks_run_gateway"
        assert gw["evidence_package"]["source"] == "tasks_run_gateway"

    def test_gateway_result_execution_modes_only_blocked_or_preview(self):
        """execution_mode is either blocked or preview_only."""
        resp = client.post("/ai/chat", json={
            "prompt": "show me the task status for project X",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert gw["execution_mode"] in ("blocked", "preview_only")

    def test_gateway_result_contains_note(self):
        """task_gateway_result includes a safety note."""
        resp = client.post("/ai/chat", json={
            "prompt": "embed the records",
        })
        data = resp.json()
        gw = data["task_gateway_result"]
        assert gw is not None
        assert len(gw["note"]) > 10
        assert "No task executed" in gw["note"]


    # ═══════════════════════════════════════════════════
    # P4-T6 Baton 8: valid approval_state values
    # ═══════════════════════════════════════════════════

    def test_gateway_result_high_risk_embed_approval_state_required(self):
        """Embed/high-risk intent -> approval_state=required."""
        resp = client.post("/ai/chat", json={
            "prompt": "embed all documents",
        })
        gw = resp.json()["task_gateway_result"]
        assert gw is not None
        assert gw["execution_mode"] == "blocked"
        assert gw["audit_log"]["approval_state"] == "required"
        assert gw["evidence_package"]["approval_state"] == "required"

    def test_gateway_result_task_status_approval_state_not_required(self):
        """task_status preview-safe intent -> approval_state=not_required."""
        resp = client.post("/ai/chat", json={
            "prompt": "show task status please",
        })
        gw = resp.json()["task_gateway_result"]
        assert gw is not None
        assert gw["audit_log"]["approval_state"] == "not_required"
        assert gw["evidence_package"]["approval_state"] == "not_required"

    def test_gateway_result_topk_verify_approval_state_not_required(self):
        """topk_verify preview-safe -> approval_state=not_required."""
        resp = client.post("/ai/chat", json={
            "prompt": "topk verify the results",
        })
        gw = resp.json()["task_gateway_result"]
        assert gw is not None
        assert gw["audit_log"]["approval_state"] == "not_required"
        assert gw["evidence_package"]["approval_state"] == "not_required"

    def test_gateway_result_no_invalid_approval_state(self):
        """No 'awaiting_tao_approval' in task_gateway_result approval_state."""
        for prompt in ["show task status", "topk verify", "embed documents", "hello"]:
            resp = client.post("/ai/chat", json={"prompt": prompt})
            data = resp.json()
            gw = data.get("task_gateway_result")
            if gw is None:
                continue  # pure_chat has no gateway result
            assert "awaiting_tao_approval" not in gw["audit_log"].get("approval_state", "")
            assert "awaiting_tao_approval" not in gw["evidence_package"].get("approval_state", "")


# ══════════════════════════════════════════════════════════════
# P4-T6 Baton 8: Local Console page UX tests
# ══════════════════════════════════════════════════════════════

class TestLocalConsolePageUX:

    def test_local_console_page_loads(self):
        """GET / returns 200."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_local_console_contains_render_task_gateway(self):
        """Page contains renderTaskGatewayResult JS function."""
        resp = client.get("/")
        assert "renderTaskGatewayResult" in resp.text

    def test_local_console_contains_task_gateway_text(self):
        """Page contains 'Task Gateway' text."""
        resp = client.get("/")
        assert "Task Gateway" in resp.text

    def test_local_console_contains_no_task_executed_text(self):
        """Page contains 'No task executed' safety text."""
        resp = client.get("/")
        assert "No task executed" in resp.text

    def test_local_console_contains_no_audit_persistence_text(self):
        """Page contains 'No audit persistence' safety text."""
        resp = client.get("/")
        assert "No audit persistence" in resp.text

    def test_local_console_contains_no_database_write_text(self):
        """Page contains 'No database write' safety text."""
        resp = client.get("/")
        assert "No database write" in resp.text


# ══════════════════════════════════════════════════════════════
# P5-T3: /tasks/plan endpoint skeleton
# ══════════════════════════════════════════════════════════════

def test_plan_endpoint_exists():
    """POST /tasks/plan returns 200."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-001", "intent": "task_status",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_plan_pure_chat_returns_no_plan():
    """pure_chat intent returns plan=None."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-002", "intent": "pure_chat",
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["plan"] is None
    assert data["dry_run"] is None


def test_plan_task_status_is_plan_only():
    """task_status intent returns plan_only execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-003", "intent": "task_status",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "plan_only"
    assert plan["no_execution"] is True
    assert plan["source"] == "execution_plan_gateway"
    assert len(plan["planned_steps"]) > 0
    assert plan["runner_target"]["executor_enabled"] is False
    assert plan["runner_target"]["real_execution_allowed"] is False


def test_plan_topk_verify_is_plan_only():
    """topk_verify intent returns plan_only execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-004", "intent": "topk_verify",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "plan_only"
    assert plan["no_execution"] is True
    assert len(plan["planned_steps"]) > 0


def test_plan_memory_fetch_is_blocked():
    """memory_fetch intent returns blocked execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-005", "intent": "memory_fetch",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"
    assert plan["no_execution"] is True


def test_plan_embed_is_blocked():
    """embed intent returns blocked execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-006", "intent": "embed",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"


def test_plan_approve_task_is_blocked():
    """approve_task intent returns blocked execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-007", "intent": "approve_task",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"


def test_plan_reject_task_is_blocked():
    """reject_task intent returns blocked execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-008", "intent": "reject_task",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"


def test_plan_unknown_intent_is_blocked():
    """unknown intent returns blocked execution plan."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-009", "intent": "unknown",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"


def test_plan_nonexistent_intent_is_blocked():
    """Nonexistent intents default to blocked."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-010", "intent": "nonexistent_intent",
    })
    data = resp.json()
    assert data["ok"] is True
    plan = data["plan"]
    assert plan is not None
    assert plan["execution_mode"] == "blocked"


def test_plan_never_executes_tasks():
    """All intents return no_execution=True and task_executed=False."""
    for intent in ("pure_chat", "task_status", "topk_verify", "memory_fetch", "embed", "approve_task", "reject_task", "unknown"):
        resp = client.post("/tasks/plan", json={
            "task_id": f"plan-safety-{intent}", "intent": intent,
        })
        assert resp.status_code == 200
        data = resp.json()
        if data["plan"] is not None:
            assert data["plan"]["no_execution"] is True, f"intent={intent} no_execution"
            rt = data["plan"]["runner_target"]
            assert rt["executor_enabled"] is False, f"intent={intent} executor_enabled"
            assert rt["real_execution_allowed"] is False, f"intent={intent} real_execution_allowed"


def test_plan_dry_run_result_is_non_executing():
    """DryRunResult in response has execution flags set to False."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-dr-001", "intent": "task_status",
    })
    data = resp.json()
    dr = data["dry_run"]
    assert dr is not None
    assert dr["status"] == "dry_run_only"
    assert dr["simulated"] is True
    assert dr["task_executed"] is False
    assert dr["mutation_performed"] is False


def test_plan_dry_run_evidence_is_non_executing():
    """EvidencePackage inside DryRunResult has all execution flags False."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-ev-001", "intent": "topk_verify",
    })
    data = resp.json()
    ev = data["dry_run"]["evidence_package"]
    assert ev is not None
    assert ev["task_executed"] is False
    assert ev["runtime_mutation"] is False
    assert ev["worker_started"] is False
    assert ev["executor_enabled"] is False
    assert ev["do_connected"] is False
    assert ev["real_rag_query_executed"] is False
    assert ev["embedding_rebuild_executed"] is False


def test_plan_dry_run_audit_log_contains_metadata():
    """AuditLog inside DryRunResult contains expected metadata."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-al-001", "intent": "task_status",
    })
    data = resp.json()
    al = data["dry_run"]["audit_log"]
    assert al is not None
    assert "audit_log_id" in al
    assert al["request_id"] is not None
    assert al["intent"] == "task_status"
    assert al["decision"] is not None


def test_plan_blocked_dry_run_audit_decision_is_blocked():
    """Blocked intent DryRunResult has decision=blocked in audit log."""
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-ba-001", "intent": "embed",
    })
    data = resp.json()
    al = data["dry_run"]["audit_log"]
    assert al is not None
    assert al["decision"] == "blocked"




# P5-T3 Baton 8 fix — top-level response contract

def test_plan_response_has_top_level_safety_fields_for_plan_only():
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-contract-001", "intent": "task_status",
    })
    data = resp.json()

    assert data["status"] == "plan_only"
    assert data["execution_mode"] == "plan_only"
    assert data["task_executed"] is False
    assert data["mutation_performed"] is False
    assert data["audit_persisted"] is False
    assert data["database_written"] is False
    assert data["executor_enabled"] is False
    assert data["real_execution_allowed"] is False
    assert data["source"] == "execution_plan_gateway"


def test_plan_response_has_top_level_safety_fields_for_blocked():
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-contract-002", "intent": "memory_fetch",
    })
    data = resp.json()

    assert data["status"] == "blocked"
    assert data["execution_mode"] == "blocked"
    assert data["task_executed"] is False
    assert data["mutation_performed"] is False
    assert data["audit_persisted"] is False
    assert data["database_written"] is False
    assert data["executor_enabled"] is False
    assert data["real_execution_allowed"] is False


def test_plan_audit_decision_is_plan_only_for_plan_only():
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-contract-003", "intent": "task_status",
    })
    data = resp.json()

    assert data["dry_run"]["audit_log"]["decision"] == "plan_only"


def test_tasks_run_dry_run_query_does_not_create_plan_or_dry_run_only():
    resp = client.post("/tasks/run?dry_run=true", json={
        "task_id": "plan-contract-004",
        "intent": "task_status",
        "approval_state": "not_required",
    })
    data = resp.json()

    assert "plan" not in data
    assert data["run"]["execution_mode"] in {"preview_only", "blocked"}
    assert data["run"]["execution_mode"] != "dry_run_only"


# Package 5 Task 4 — Strategy Matrix + Risk Classification Endpoint Tests

def test_plan_endpoint_surfaces_risk_classification():
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-t4-ep-001",
        "intent": "task_status",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["ok"] is True
    assert data["status"] == "plan_only"
    assert data["risk_level"] == "L0_information"
    assert data["strategy"] == "plan_only"
    assert data["execution_policy"] == "no_mutation"
    assert data["approval_required"] is False
    assert data["blocked_reason"] is None
    assert data["risk_classification"] is not None
    assert data["risk_classification"]["intent"] == "task_status"
    assert data["risk_classification"]["no_real_execution"] is True

    # Surface in plan and dry_run
    assert data["plan"]["risk_classification"] is not None
    assert data["plan"]["risk_classification"]["strategy"] == "plan_only"
    assert data["dry_run"]["risk_classification"] is not None
    assert data["dry_run"]["risk_classification"]["strategy"] == "plan_only"


def test_plan_endpoint_blocked_memory_fetch_surfaces_classification():
    resp = client.post("/tasks/plan", json={
        "task_id": "plan-t4-ep-002",
        "intent": "memory_fetch",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["ok"] is True
    assert data["status"] == "blocked"
    assert data["execution_mode"] == "blocked"
    assert data["strategy"] == "blocked"
    assert data["approval_required"] is True
    assert data["blocked_reason"] is not None
    assert "Memory fetch is blocked" in data["blocked_reason"]
    assert data["risk_classification"]["strategy"] == "blocked"


def test_plan_endpoint_high_risk_intents_surface_high_risk_blocked_classification():
    high_risk_intents = ["shell_command", "deploy", "systemctl", "git_push", "runtime_mutation", "executor"]
    for intent in high_risk_intents:
        resp = client.post("/tasks/plan", json={
            "task_id": f"plan-t4-hr-{intent}",
            "intent": intent,
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["ok"] is True
        assert data["status"] == "blocked", f"intent={intent} status"
        assert data["execution_mode"] == "blocked", f"intent={intent} mode"
        assert data["risk_level"] == "L4_critical_runtime", f"intent={intent} risk"
        assert data["strategy"] == "blocked", f"intent={intent} strategy"
        assert data["execution_policy"] == "never", f"intent={intent} policy"
        assert data["approval_required"] is True, f"intent={intent} approval"
        assert data["blocked_reason"] is not None, f"intent={intent} reason"
        assert "blocked" in data["blocked_reason"].lower(), f"intent={intent} reason text"

        # Safety fields
        assert data["task_executed"] is False
        assert data["mutation_performed"] is False
        assert data["audit_persisted"] is False
        assert data["database_written"] is False
        assert data["executor_enabled"] is False
        assert data["real_execution_allowed"] is False


def test_plan_endpoint_safety_invariants_preserved():
    for intent in ("pure_chat", "task_status", "topk_verify", "memory_fetch", "embed", "shell", "deploy", "unknown"):
        resp = client.post("/tasks/plan", json={
            "task_id": f"plan-t4-inv-{intent}",
            "intent": intent,
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["task_executed"] is False
        assert data["mutation_performed"] is False
        assert data["audit_persisted"] is False
        assert data["database_written"] is False
        assert data["executor_enabled"] is False
        assert data["real_execution_allowed"] is False

