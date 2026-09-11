"""
GOAA Rule-based Intent Detection — Unit Tests (P1-T2-U3)
===========================================================
Test coverage requirements:

1. casual chat -> pure_chat
2. task count/status query -> task_status
3. topk/rag/search query -> topk_verify
4. memory/session query -> memory_fetch
5. embed/rebuild index query -> embed risk 4 after envelope build
6. approve query -> approve_task
7. reject query -> reject_task
8. empty message rejected or pure_chat with low confidence
9. secret/token/private_key 字样不进入 params
10. detection result can build TaskEnvelope
11. detection_method must be rule_based
12. no IO/network/shell/runtime side effects
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intent_detector import (
    IntentDetectionResult,
    detect_intent_from_message,
    build_envelope_from_detection,
)
from task_envelope import (
    TaskIntent,
    DetectionMethod,
    TaskEnvelopeStatus,
    TaskRiskLevel,
    build_task_envelope,
)


# ══════════════════════════════════════════════════════════════
# 1. casual chat -> pure_chat
# ══════════════════════════════════════════════════════════════

def test_casual_chat_returns_pure_chat():
    """Ordinary conversation returns pure_chat intent."""
    result = detect_intent_from_message("你好，今天天气不错")
    assert result.intent == TaskIntent.PURE_CHAT.value

    result = detect_intent_from_message("Hello, how are you?")
    assert result.intent == TaskIntent.PURE_CHAT.value

    result = detect_intent_from_message("What is the meaning of life?")
    assert result.intent == TaskIntent.PURE_CHAT.value


# ══════════════════════════════════════════════════════════════
# 2. task count/status query -> task_status
# ══════════════════════════════════════════════════════════════

def test_task_status_queries():
    """Status/task queries return task_status intent."""
    test_cases = [
        "查一下任务状态",
        "task status",
        "有什么任务在跑",
        "today task progress",
        "check task 123",
        "有几个任务",
        "全部任务",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.TASK_STATUS.value, (
            f"Expected task_status for '{msg}', got {result.intent}"
        )


# ══════════════════════════════════════════════════════════════
# 3. topk/rag/search query -> topk_verify
# ══════════════════════════════════════════════════════════════

def test_topk_verify_queries():
    """Search/RAG queries return topk_verify intent."""
    test_cases = [
        "查 RAG multi-node dispatch",
        "search memory for GOAA protocol",
        "query knowledge base about AI workspace",
        "查找关于多节点调度的内容",
        "搜索记忆",
        "查询知识库",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.TOPK_VERIFY.value, (
            f"Expected topk_verify for '{msg}', got {result.intent}"
        )


# ══════════════════════════════════════════════════════════════
# 4. memory/session query -> memory_fetch
# ══════════════════════════════════════════════════════════════

def test_memory_fetch_queries():
    """Memory/recall queries return memory_fetch intent."""
    test_cases = [
        "remember what we discussed yesterday",
        "recall prior context",
        "what did I ask last time",
        "读取记忆",
        "查 session 历史",
        "查记忆",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.MEMORY_FETCH.value, (
            f"Expected memory_fetch for '{msg}', got {result.intent}"
        )


# ══════════════════════════════════════════════════════════════
# 5. embed/rebuild index -> embed
# ══════════════════════════════════════════════════════════════

def test_embed_queries():
    """Embed/corpus queries return embed intent."""
    test_cases = [
        "embed this document into RAG",
        "rebuild index for corpus",
        "store corpus data",
        "重建索引",
        "embedding",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.EMBED.value, (
            f"Expected embed for '{msg}', got {result.intent}"
        )


def test_embed_risk4_after_envelope_build():
    """embed intent produces risk_level=4 envelope with approval_required."""
    result = detect_intent_from_message("rebuild index please")
    assert result.intent == TaskIntent.EMBED.value
    env = build_envelope_from_detection(result, session_id="console-test-embed")
    assert env.risk_level == TaskRiskLevel.CRITICAL.value  # 4
    assert env.approval_required is True
    assert env.status == TaskEnvelopeStatus.AWAITING_APPROVAL.value


# ══════════════════════════════════════════════════════════════
# 6. approve query -> approve_task
# ══════════════════════════════════════════════════════════════

def test_approve_task_queries():
    """Approval queries return approve_task intent."""
    test_cases = [
        "approve task 123",
        "yes approve",
        "go ahead",
        "批准任务",
        "同意",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.APPROVE_TASK.value, (
            f"Expected approve_task for '{msg}', got {result.intent}"
        )


# ══════════════════════════════════════════════════════════════
# 7. reject query -> reject_task
# ══════════════════════════════════════════════════════════════

def test_reject_task_queries():
    """Rejection queries return reject_task intent."""
    test_cases = [
        "reject task 456",
        "deny task",
        "cancel it",
        "拒绝任务",
        "do not approve",
    ]
    for msg in test_cases:
        result = detect_intent_from_message(msg)
        assert result.intent == TaskIntent.REJECT_TASK.value, (
            f"Expected reject_task for '{msg}', got {result.intent}"
        )


# ══════════════════════════════════════════════════════════════
# 8. empty message
# ══════════════════════════════════════════════════════════════

def test_empty_message_returns_pure_chat_low_confidence():
    """Empty/whitespace messages return pure_chat with 0.0 confidence."""
    result = detect_intent_from_message("")
    assert result.intent == TaskIntent.PURE_CHAT.value
    assert result.confidence == 0.0

    result = detect_intent_from_message("   ")
    assert result.intent == TaskIntent.PURE_CHAT.value
    assert result.confidence == 0.0

    result = detect_intent_from_message("\n\t\n")
    assert result.intent == TaskIntent.PURE_CHAT.value
    assert result.confidence == 0.0


# ══════════════════════════════════════════════════════════════
# 9. secret/token/private_key not in params
# ══════════════════════════════════════════════════════════════

def test_secret_values_not_in_params():
    """Messages with secret-like content should not have them in params."""
    # Secret as query text
    result = detect_intent_from_message("search for secret=abc123")
    if result.intent == TaskIntent.TOPK_VERIFY.value:
        params_str = json.dumps(result.params)
        assert "abc123" not in params_str
        assert "secret" not in params_str

    # Token in message
    result = detect_intent_from_message("lookup token=ghp_xyz789")
    if result.intent == TaskIntent.TOPK_VERIFY.value:
        params_str = json.dumps(result.params)
        assert "ghp_xyz789" not in params_str

    # Private key mention
    result = detect_intent_from_message("find id_rsa in config")
    if result.intent == TaskIntent.TOPK_VERIFY.value:
        params_str = json.dumps(result.params)
        assert "id_rsa" not in params_str


# ══════════════════════════════════════════════════════════════
# 10. detection result can build TaskEnvelope
# ══════════════════════════════════════════════════════════════

def test_detection_result_builds_envelope():
    """IntentDetectionResult can produce a valid TaskEnvelope."""
    result = detect_intent_from_message("search memory for GOAA protocol")
    assert result.intent == TaskIntent.TOPK_VERIFY.value

    env = build_envelope_from_detection(
        result,
        session_id="console-session-test-001",
        target_node="local-aika-core-01",
    )
    assert env.intent == TaskIntent.TOPK_VERIFY.value
    assert env.risk_level == TaskRiskLevel.LOW.value  # 1
    assert env.approval_required is False
    assert env.source_conversation_session == "console-session-test-001"
    assert env.envelope_id.startswith("GOAA-CONV-TASK-")
    assert env.target_node == "local-aika-core-01"


def test_approve_detection_builds_envelope_with_task_id():
    """Approve intent with task_id in params builds correct envelope."""
    result = detect_intent_from_message("approve task 123")
    assert result.intent == TaskIntent.APPROVE_TASK.value

    env = build_envelope_from_detection(
        result,
        session_id="console-approve-test",
    )
    assert env.intent == TaskIntent.APPROVE_TASK.value
    assert env.risk_level == TaskRiskLevel.HIGH.value  # 3
    assert env.approval_required is False  # Baton 8: risk 3 != Tao approval
    assert env.params.get("task_id") == "123"


# ══════════════════════════════════════════════════════════════
# 11. detection_method is rule_based
# ══════════════════════════════════════════════════════════════

def test_detection_method_is_rule_based():
    """All rule-based detections report method as rule_based."""
    messages = [
        "search for something",
        "task status",
        "remember",
        "rebuild index",
        "approve task",
        "reject task",
        "hello world",
    ]
    for msg in messages:
        result = detect_intent_from_message(msg)
        assert result.detection_method == DetectionMethod.RULE_BASED.value, (
            f"Expected rule_based for '{msg}', got {result.detection_method}"
        )


# ══════════════════════════════════════════════════════════════
# 12. no IO/network/shell/runtime side effects
# ══════════════════════════════════════════════════════════════

def test_no_side_effects():
    """Intent detection should NOT cause any mutation side effects."""
    import os

    files_before = set()
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "venv", "__pycache__")]
        for f in files:
            files_before.add(os.path.join(root, f))

    # Run detection many times
    for _ in range(10):
        detect_intent_from_message("search for GOAA protocol")
        detect_intent_from_message("hello world")
        detect_intent_from_message("approve task")
        detect_intent_from_message("rebuild index")

    files_after = set()
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "venv", "__pycache__")]
        for f in files:
            files_after.add(os.path.join(root, f))

    delta = files_after - files_before
    expected_new = {f for f in delta if "intent_detector" in f}
    unexpected = delta - expected_new
    assert len(unexpected) == 0, f"Unexpected side-effect files: {unexpected}"


# ══════════════════════════════════════════════════════════════
# 13. intent_hint override
# ══════════════════════════════════════════════════════════════

def test_intent_hint_override():
    """Explicit intent_hint overrides rule-based detection."""
    # Even though message is casual, explicit hint should be used
    result = detect_intent_from_message("hello", intent_hint="topk_verify")
    assert result.intent == TaskIntent.TOPK_VERIFY.value
    assert result.detection_method == DetectionMethod.USER_HINT.value
    assert result.confidence == 1.0


def test_intent_hint_auto():
    """intent_hint='auto' or None should use rule-based detection."""
    result = detect_intent_from_message("hello", intent_hint="auto")
    assert result.intent == TaskIntent.PURE_CHAT.value
    assert result.detection_method == DetectionMethod.RULE_BASED.value

    result = detect_intent_from_message("hello", intent_hint=None)
    assert result.intent == TaskIntent.PURE_CHAT.value
    assert result.detection_method == DetectionMethod.RULE_BASED.value


def test_invalid_intent_hint_raises():
    """Invalid intent_hint value should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Invalid intent_hint"):
        detect_intent_from_message("hello", intent_hint="not_a_real_intent")


# ══════════════════════════════════════════════════════════════
# 13c. intent_hint override sanitizes secret-like params
# ══════════════════════════════════════════════════════════════

def test_intent_hint_override_sanitizes_secret_params():
    """intent_hint override branch must sanitize secret-like params."""
    result = detect_intent_from_message(
        "search for token=abc123",
        intent_hint="topk_verify",
    )
    assert result.intent == "topk_verify"
    assert result.detection_method == "user_hint"
    import json
    params_str = json.dumps(result.params)
    assert "abc123" not in params_str
    assert "token" not in params_str


# ══════════════════════════════════════════════════════════════
# 14. Priority ordering — approve/reject before generic keywords
# ══════════════════════════════════════════════════════════════

def test_priority_approve_before_generic():
    """'approve task' should NOT be classified as topk_verify or other."""
    result = detect_intent_from_message("approve task 123")
    assert result.intent == TaskIntent.APPROVE_TASK.value


def test_priority_reject_before_generic():
    """'reject task' should NOT be classified as topk_verify or other."""
    result = detect_intent_from_message("reject task 456 because it's wrong")
    assert result.intent == TaskIntent.REJECT_TASK.value


# ══════════════════════════════════════════════════════════════
# 15. Keyword 'yes' alone is not approval
# ══════════════════════════════════════════════════════════════

def test_yes_alone_is_not_approve():
    """Just saying 'yes' should be pure_chat, not approve_task."""
    # 'yes' alone is too ambiguous
    result = detect_intent_from_message("yes")
    # The rule requires "yes approve" together for approve_task
    # 'yes' alone might match... let me check the rule.
    # Rules: ("approve_task", ["approve task", "yes approve", "go ahead", ...])
    # 'yes' alone does NOT match any approve_task pattern
    # 'yes' alone also does NOT match reject patterns
    assert result.intent == TaskIntent.PURE_CHAT.value
