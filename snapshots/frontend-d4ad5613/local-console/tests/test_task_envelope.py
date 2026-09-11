"""
GOAA Task Envelope Model — Unit Tests (P1-T2-U2)
==================================================
Test coverage requirements:

1. pure_chat does not require approval
2. topk_query risk low / no Tao approval
3. status_check readonly
4. embed_corpus_full_envelope_only risk 4 / approval_required true
5. approval_required false for risk level 3
6. invalid intent rejected
7. envelope serialization stable enough for evidence output
8. no execution side effects
"""
import json
import sys
from pathlib import Path

# Ensure the local-console module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from task_envelope import (
    SafetyFlags,
    TaskEnvelope,
    TaskEnvelopeStatus,
    TaskIntent,
    TaskRiskLevel,
    EvidencePackage,
    build_task_envelope,
    build_evidence_package,
    classify_risk_for_intent,
    is_approval_required,
)


# ══════════════════════════════════════════════════════════════
# 1. pure_chat — no task, no approval
# ══════════════════════════════════════════════════════════════

def test_pure_chat_does_not_require_approval():
    """pure_chat intent: risk=0, approval_required=false, no side effects."""
    env = build_task_envelope(
        intent="pure_chat",
        detection_method="rule_based",
        confidence=1.0,
        session_id="console-abc123",
    )
    assert env.intent == "pure_chat"
    assert env.risk_level == 0
    assert env.approval_required is False
    assert env.status == TaskEnvelopeStatus.PENDING.value
    assert env.target_node == "local-aika-core-01"


# ══════════════════════════════════════════════════════════════
# 2. topk_query — low risk, no approval
# ══════════════════════════════════════════════════════════════

def test_topk_query_low_risk_no_approval():
    """topk_verify intent: risk=1, approval_required=false."""
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.85,
        session_id="console-xyz789",
        params={"query": "GOAA multi-node dispatch"},
    )
    assert env.intent == "topk_verify"
    assert env.risk_level == TaskRiskLevel.LOW.value  # 1
    assert env.approval_required is False
    assert env.status == TaskEnvelopeStatus.PENDING.value


# ══════════════════════════════════════════════════════════════
# 3. status_check — readonly, no risk
# ══════════════════════════════════════════════════════════════

def test_status_check_readonly():
    """task_status intent: risk=0, readonly, no approval."""
    env = build_task_envelope(
        intent="task_status",
        detection_method="user_hint",
        confidence=0.95,
        session_id="console-status-001",
    )
    assert env.intent == "task_status"
    assert env.risk_level == TaskRiskLevel.INFORMATION_ONLY.value  # 0
    assert env.approval_required is False
    assert env.status == TaskEnvelopeStatus.PENDING.value


# ══════════════════════════════════════════════════════════════
# 4. embed_corpus_full_envelope_only — risk 4, approval_required
# ══════════════════════════════════════════════════════════════

def test_embed_risk4_approval_required():
    """embed intent: risk=4, approval_required=true, status=awaiting_approval."""
    env = build_task_envelope(
        intent="embed",
        detection_method="rule_based",
        confidence=0.78,
        session_id="console-embed-001",
        params={"source": "/data/corpus/new_docs.txt"},
    )
    assert env.intent == "embed"
    assert env.risk_level == TaskRiskLevel.CRITICAL.value  # 4
    assert env.approval_required is True
    assert env.status == TaskEnvelopeStatus.AWAITING_APPROVAL.value


# ══════════════════════════════════════════════════════════════
# 5. approval_required false for risk level 3
# ══════════════════════════════════════════════════════════════

def test_approval_not_required_for_risk3():
    """risk_level=3 (approve/reject): approval_required=false (role-gated, not Tao)."""
    for intent_name in ("approve_task", "reject_task"):
        env = build_task_envelope(
            intent=intent_name,
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-gate-001",
        )
        assert env.intent == intent_name
        assert env.risk_level == TaskRiskLevel.HIGH.value  # 3
        assert env.approval_required is False, (
            f"risk_level=3 should NOT require Tao approval for intent={intent_name}"
        )
        assert env.status == TaskEnvelopeStatus.PENDING.value


# ══════════════════════════════════════════════════════════════
# 6. invalid intent rejected
# ══════════════════════════════════════════════════════════════

def test_invalid_intent_rejected():
    """Invalid intent string should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Invalid intent"):
        build_task_envelope(
            intent="non_existent_intent",
            detection_method="rule_based",
            confidence=0.5,
            session_id="console-invalid-001",
        )


# ══════════════════════════════════════════════════════════════
# 7. envelope serialization — stable for evidence
# ══════════════════════════════════════════════════════════════

def test_envelope_serialization_stable():
    """JSON serialization and SHA256 are stable and deterministic."""
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.85,
        session_id="console-serial-001",
        params={"query": "test stability"},
    )
    # JSON round-trip
    json_str = env.to_json()
    parsed = json.loads(json_str)
    assert parsed["intent"] == "topk_verify"
    assert parsed["risk_level"] == 1
    assert parsed["approval_required"] is False
    assert isinstance(parsed["envelope_id"], str)
    assert parsed["envelope_id"].startswith("GOAA-CONV-TASK-")

    # SHA256 is deterministic
    sha1 = env.compute_sha256()
    json_str2 = env.to_json()
    parsed2 = json.loads(json_str2)
    env2 = TaskEnvelope(**parsed2)
    sha2 = env2.compute_sha256()
    assert sha1 == sha2, "SHA256 should be deterministic across serialization cycles"

    # Evidence package uses envelope SHA256
    evidence = build_evidence_package(
        task_id="task-001",
        envelope=env,
        status="completed",
        executor="task_runner",
        duration_ms=120,
        output_summary="Top-k query returned 5 rows",
    )
    assert evidence.evidence_sha256 == sha1
    assert evidence.envelope_id == env.envelope_id
    assert evidence.final_marker.startswith("GOAA_TOPK_VERIFY_")


# ══════════════════════════════════════════════════════════════
# 8. no execution side effects
# ══════════════════════════════════════════════════════════════

def test_no_execution_side_effects():
    """Building envelopes should NOT cause any mutation side effects."""
    import os

    # Check no unexpected file writes
    files_before = set()
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip .git and node_modules
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "venv", "__pycache__")]
        for f in files:
            files_before.add(os.path.join(root, f))

    # Build several envelopes
    for _ in range(5):
        env = build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-side-001",
        )
        _ = env.to_json()

    # Check files after
    files_after = set()
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "venv", "__pycache__")]
        for f in files:
            files_after.add(os.path.join(root, f))

    # Only the test file itself and the module may be new
    delta = files_after - files_before
    # Filter out expected new files (the envelope module and test files)
    expected_new = {f for f in delta if "task_envelope" in f}
    unexpected = delta - expected_new
    assert len(unexpected) == 0, f"Unexpected side-effect files created: {unexpected}"


# ══════════════════════════════════════════════════════════════
# 9. classify_risk_for_intent boundary tests
# ══════════════════════════════════════════════════════════════

def test_classify_risk_pure_chat():
    assert classify_risk_for_intent("pure_chat") == 0


def test_classify_risk_topk():
    assert classify_risk_for_intent("topk_verify") == 1


def test_classify_risk_memory_fetch():
    assert classify_risk_for_intent("memory_fetch") == 2


def test_classify_risk_approve_reject():
    assert classify_risk_for_intent("approve_task") == 3
    assert classify_risk_for_intent("reject_task") == 3


def test_classify_risk_embed():
    assert classify_risk_for_intent("embed") == 4


def test_classify_risk_unknown_intent_defaults_0():
    assert classify_risk_for_intent("unknown_intent_xyz") == 0


def test_classify_risk_params_path_escalation():
    """Params with path patterns escalate to risk 4."""
    risk = classify_risk_for_intent("topk_verify", {"path": "/home/aika/private"})
    assert risk == 4, f"Expected 4, got {risk}"


def test_classify_risk_params_secret_pattern():
    """Params with secret-like key names escalate to risk 4."""
    risk = classify_risk_for_intent("topk_verify", {"secret_key": "abc123"})
    assert risk == 4


# ══════════════════════════════════════════════════════════════
# 10. is_approval_required boundary tests
# ══════════════════════════════════════════════════════════════

def test_approval_required_false_for_level_0():
    assert is_approval_required(0) is False


def test_approval_required_false_for_level_1():
    assert is_approval_required(1) is False


def test_approval_required_false_for_level_2():
    assert is_approval_required(2) is False


def test_approval_required_false_for_level_3():
    """Baton 8 fix: risk_level 3 is role-gated, NOT Tao approval."""
    assert is_approval_required(3) is False


def test_approval_required_true_for_level_4():
    assert is_approval_required(4) is True


# ══════════════════════════════════════════════════════════════
# 11. EvidencePackage safety_flags
# ══════════════════════════════════════════════════════════════

def test_evidence_package_default_safety_flags():
    """Default safety flags: repo_not_modified, envelope_persist_allowed."""
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.9,
        session_id="console-evidence-001",
    )
    evidence = build_evidence_package(
        task_id="task-evidence-001",
        envelope=env,
        status="completed",
        executor="task_runner",
        duration_ms=95,
        output_summary="Returned 3 matches",
    )
    flags = evidence.safety_flags
    assert flags["repo_or_source_file_modified"] is False
    assert flags["task_envelope_persisted_allowed"] is True
    assert flags["commit_performed"] is False
    assert flags["push_performed"] is False
    assert flags["merge_performed"] is False
    assert flags["do_connected"] is False
    assert flags["secret_read_attempted"] is False
    assert flags["private_key_content_read_attempted"] is False
    assert flags["worker_started"] is False
    assert flags["executor_enabled"] is False
    assert flags["deploy_performed"] is False
    assert flags["runtime_mutated"] is False


# ══════════════════════════════════════════════════════════════
# 12. Confidence validation
# ══════════════════════════════════════════════════════════════

def test_invalid_confidence_rejected():
    """Confidence outside [0.0, 1.0] should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Confidence must be in range"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=1.5,
            session_id="console-conf-001",
        )
    with pytest.raises(ValueError, match="Confidence must be in range"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=-0.1,
            session_id="console-conf-002",
        )


# ══════════════════════════════════════════════════════════════
# 13. detection_method validation (Baton 8 fix)
# ══════════════════════════════════════════════════════════════

def test_invalid_detection_method_rejected():
    """Invalid detection_method string should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Invalid detection_method"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="unknown_method_xyz",
            confidence=0.9,
            session_id="console-dm-001",
        )


# ══════════════════════════════════════════════════════════════
# 14. Secret-like params rejected (Baton 8 fix)
# ══════════════════════════════════════════════════════════════

def test_build_envelope_rejects_secret_like_params():
    """Secret-like param keys (secret, token, password, etc.) raise ValueError."""
    import pytest
    # secret key
    with pytest.raises(ValueError, match="secret-like"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-sec-001",
            params={"query": "test", "secret": "abc123"},
        )
    # token key
    with pytest.raises(ValueError, match="secret-like"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-sec-002",
            params={"api_key": "sk-12345"},
        )
    # password key
    with pytest.raises(ValueError, match="secret-like"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-sec-003",
            params={"password": "hunter2"},
        )
    # private_key key
    with pytest.raises(ValueError, match="secret-like"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-sec-004",
            params={"private_key": "AAAA..."},
        )
    # id_rsa in value
    with pytest.raises(ValueError, match="secret-like"):
        build_task_envelope(
            intent="topk_verify",
            detection_method="rule_based",
            confidence=0.9,
            session_id="console-sec-005",
            params={"path": "/home/user/.ssh/id_rsa"},
        )
    # Normal non-secret params should NOT raise
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.9,
        session_id="console-sec-006",
        params={"query": "safe query", "top_k": 5},
    )
    assert env.intent == "topk_verify"
    assert env.risk_level == 1


def test_secret_like_params_not_serialized():
    """Envelope JSON must never contain secret-like values (verify by rejection)."""
    import pytest
    # Verify that the safety check catches various secret-like key forms
    secret_cases = [
        {"token": "ghp_abc123"},
        {"secret_key": "s3kr3t"},
        {"ssh_key": "AAAA..."},
        {"credential": "admin:pass"},
        {"key_file": "/path/to/key"},
    ]
    for bad_params in secret_cases:
        with pytest.raises(ValueError, match="secret-like"):
            build_task_envelope(
                intent="topk_verify",
                detection_method="rule_based",
                confidence=0.9,
                session_id="console-serial-sec",
                params=bad_params,
            )


# ══════════════════════════════════════════════════════════════
# 15. Substring key patterns (Baton 8 fix)
# ══════════════════════════════════════════════════════════════

def test_secret_like_substring_keys_rejected():
    """Substring key patterns (github_token, openai_api_key, etc.) rejected."""
    import pytest
    # Substring patterns that should be caught
    substring_cases = [
        {"github_token": "ghp_abc123"},
        {"openai_api_key": "sk-abc123"},
        {"my_secret_value": "s3kr3t"},
        {"ssh_private_key": "AAAA..."},
        {"access-token": "tok_xyz"},
    ]
    for bad_params in substring_cases:
        with pytest.raises(ValueError, match="secret-like"):
            build_task_envelope(
                intent="topk_verify",
                detection_method="rule_based",
                confidence=0.9,
                session_id="console-substr-sec",
                params=bad_params,
            )


def test_envelope_id_format():
    """Envelope ID matches spec format: GOAA-CONV-TASK-{YYYYMMDD}-{NNN}."""
    import re
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.9,
        session_id="console-id-001",
    )
    pattern = r"^GOAA-CONV-TASK-\d{8}-\d{3}$"
    assert re.match(pattern, env.envelope_id), (
        f"envelope_id '{env.envelope_id}' does not match pattern {pattern}"
    )


# ══════════════════════════════════════════════════════════════
# 14. SafetyFlags explicit overrides
# ══════════════════════════════════════════════════════════════

def test_safety_flags_custom():
    """Custom safety flags can be passed to evidence package."""
    flags = SafetyFlags(
        repo_or_source_file_modified=False,
        task_envelope_persisted_allowed=True,
        commit_performed=True,
        push_performed=False,
        merge_performed=False,
        do_connected=False,
        secret_read_attempted=False,
        private_key_content_read_attempted=False,
        worker_started=False,
        executor_enabled=False,
        service_restarted=False,
        deploy_performed=False,
        runtime_mutated=False,
    )
    env = build_task_envelope(
        intent="topk_verify",
        detection_method="rule_based",
        confidence=0.9,
        session_id="console-flags-001",
    )
    evidence = build_evidence_package(
        task_id="task-flags-001",
        envelope=env,
        status="completed",
        executor="task_runner",
        duration_ms=100,
        output_summary="Done",
        safety_flags=flags,
    )
    assert evidence.safety_flags["commit_performed"] is True
    assert evidence.safety_flags["push_performed"] is False
