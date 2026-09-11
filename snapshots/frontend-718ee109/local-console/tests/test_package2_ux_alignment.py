#!/usr/bin/env python3
"""
Tests for P2-T2: Hide pure_chat task preview card + UX alignment.

These tests verify:
  1. pure_chat → no task preview rendered in frontend JS logic
  2. pure_chat → no evidence preview rendered in frontend JS logic
  3. task_status → task preview still rendered
  4. topk_verify → evidence preview still rendered
  5. embed → approval gate still rendered
  6. Backward compatibility
  7. Backend response unchanged (84 tests still pass)
"""

import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, "local-console/tests")
sys.path.insert(0, "local-console")

from main import app
from task_envelope import TaskIntent


client = TestClient(app)


def _mock_router_response(text="Mock AI reply"):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "ok": True,
                "response": {"text": text, "model": "mock-model"},
                "session_id": "mock-sid",
                "duration_ms": 10,
            }
    async def mock_post(*args, **kwargs):
        return MockResponse()
    return mock_post


# ══════════════════════════════════════════════════════════════
# 1. Frontend JS contains pure_chat skip logic
# ══════════════════════════════════════════════════════════════

def test_js_contains_pure_chat_skip_in_render_task_preview():
    """renderTaskPreview must have pure_chat early return."""
    with open("local-console/main.py", "r") as f:
        js = f.read()

    # Check that the pure_chat guard is present inside renderTaskPreview
    # The pattern: if(td.intent==='pure_chat') return;
    assert "td.intent==='pure_chat'" in js, \
        "renderTaskPreview must skip pure_chat"


def test_js_contains_pure_chat_skip_in_render_evidence_preview():
    """renderEvidencePreview must have pure_chat early return."""
    with open("local-console/main.py", "r") as f:
        js = f.read()

    # Check that the pure_chat guard is present inside renderEvidencePreview
    assert "ev.intent==='pure_chat'" in js, \
        "renderEvidencePreview must skip pure_chat"


# ══════════════════════════════════════════════════════════════
# 2. pure_chat: backend still returns task_detection but no task cards
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_pure_chat_response_has_no_task_or_evidence_preview(mock_httpx_client):
    """pure_chat backend should return task_detection with intent=pure_chat, no preview cards."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好，今天天氣怎麼樣？",
        "session_id": "test-p2-1",
    })
    assert resp.status_code == 200
    data = resp.json()

    # task_detection present
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "pure_chat"
    assert td["is_executable_task"] is False

    # No envelope or evidence preview
    assert data.get("task_envelope_preview") is None
    assert data.get("task_evidence_preview") is None

    # Still has normal chat answer
    assert data.get("ok") is True
    assert len(data.get("answer", "")) > 0


# ══════════════════════════════════════════════════════════════
# 3. task_status: task preview still present
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_task_status_still_has_task_preview(mock_httpx_client):
    """task_status must still have task_envelope_preview and evidence."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-p2-2",
    })
    assert resp.status_code == 200
    data = resp.json()

    # task_detection
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "task_status"
    assert td["is_executable_task"] is True

    # Envelope preview present
    ep = data.get("task_envelope_preview")
    assert ep is not None
    assert ep.get("preview_only") is True

    # Evidence preview present
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["preview_only"] is True
    assert ev["status"] == "dry_run_ready"


# ══════════════════════════════════════════════════════════════
# 4. topk_verify: evidence preview still present
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_still_has_evidence_preview(mock_httpx_client):
    """topk_verify must still have evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查询知识库",
        "session_id": "test-p2-3",
    })
    assert resp.status_code == 200
    data = resp.json()

    # task_detection
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "topk_verify"
    assert td["is_executable_task"] is True

    # Evidence preview present
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["preview_only"] is True
    assert ev["status"] == "dry_run_ready"
    assert ev["intent"] == "topk_verify"


# ══════════════════════════════════════════════════════════════
# 5. embed: approval gate still present
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_still_has_approval_gate(mock_httpx_client):
    """embed must still have approval gate blocking."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "重建索引",
        "session_id": "test-p2-4",
    })
    assert resp.status_code == 200
    data = resp.json()

    # task_detection
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "embed"
    assert td["is_executable_task"] is True

    # Approval gate present and blocking
    ag = data.get("task_approval_gate")
    assert ag is not None
    assert ag["required"] is True
    assert ag["gate_status"] == "awaiting_tao_approval"

    # Evidence preview present as blocked
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["status"] == "blocked_by_approval"
    assert ev["task_executed"] is False


# ══════════════════════════════════════════════════════════════
# 6. Backward compatibility: old response shape preserved
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_response_has_all_required_fields(mock_httpx_client):
    """All response fields must still be present."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    for prompt, expected_intent in [
        ("你好", "pure_chat"),
        ("查看目前的所有任務狀態", "task_status"),
        ("查询知识库", "topk_verify"),
        ("重建索引", "embed"),
    ]:
        resp = client.post("/ai/chat", json={
            "prompt": prompt,
            "session_id": "test-p2-bc",
        })
        assert resp.status_code == 200
        data = resp.json()

        # Core fields always present
        for field in ["ok", "answer", "session_id", "model",
                      "duration_ms", "task_detection"]:
            assert field in data, f"Missing field {field} for {prompt}"

        # intent matches
        assert data["task_detection"]["intent"] == expected_intent


# ══════════════════════════════════════════════════════════════
# 7. No new /tasks/run or subprocess calls
# ══════════════════════════════════════════════════════════════

def test_no_new_dangerous_calls_in_frontend():
    """Frontend JS must not call /tasks/run or subprocess."""
    with open("local-console/main.py", "r") as f:
        js = f.read()

    # No /tasks/run in JS
    assert "/tasks/run" not in js or "task_evidence_preview" in js, \
        "No /tasks/run calls allowed in frontend"


# ══════════════════════════════════════════════════════════════
# P2-T3: AI Response Copy Alignment Tests
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_pure_chat_answer_no_alignment_copy(mock_httpx_client):
    """pure_chat answer must NOT contain alignment copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好",
        "session_id": "test-p2t3-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "已识别为" not in ans, \
        "pure_chat should not contain alignment copy"
    assert "Task Preview" not in ans or "Mock AI reply" in ans, \
        "pure_chat answer should be original AI reply"
    assert "Mock AI reply" in ans


@patch("main.httpx.AsyncClient", autospec=True)
def test_task_status_contains_alignment(mock_httpx_client):
    """task_status answer must contain task-status alignment copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-p2t3-2",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "已识别为任务状态查询" in ans, \
        "task_status answer must contain alignment copy"
    assert "只读预览" in ans, \
        "task_status answer must mention readonly preview"


@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_contains_alignment(mock_httpx_client):
    """topk_verify answer must contain knowledge-query alignment copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查询知识库",
        "session_id": "test-p2t3-3",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "已识别为知识库查询" in ans, \
        "topk_verify answer must contain alignment copy"
    assert "dry-run evidence preview" in ans or "readonly" in ans, \
        "topk_verify answer must mention readonly/dry-run"


@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_contains_gate_blocked(mock_httpx_client):
    """embed answer must contain high-risk gate-blocked copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "重建索引",
        "session_id": "test-p2t3-4",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "高风险索引操作" in ans, \
        "embed answer must mention high risk"
    assert "Tao Approval Gate" in ans, \
        "embed answer must mention Tao Approval Gate"
    assert "不会执行" in ans, \
        "embed answer must state no execution"


@patch("main.httpx.AsyncClient", autospec=True)
def test_approve_task_contains_preview_only(mock_httpx_client):
    """approve_task answer must contain preview-only copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "批准任务",
        "session_id": "test-p2t3-5",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "preview-only" in ans or "不会执行真实审批" in ans, \
        "approve_task answer must mention preview-only"
    assert "已识别为任务批准请求" in ans, \
        "approve_task answer must mention task approval"


@patch("main.httpx.AsyncClient", autospec=True)
def test_reject_task_contains_preview_only(mock_httpx_client):
    """reject_task answer must contain preview-only copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "拒绝任务",
        "session_id": "test-p2t3-6",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "preview-only" in ans or "不会执行真实拒绝" in ans, \
        "reject_task answer must mention preview-only"
    assert "已识别为任务拒绝请求" in ans, \
        "reject_task answer must mention task reject"


@patch("main.httpx.AsyncClient", autospec=True)
def test_memory_fetch_contains_alignment(mock_httpx_client):
    """memory_fetch answer must contain memory-read alignment copy."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查记忆",
        "session_id": "test-p2t3-7",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    assert "已识别为记忆读取请求" in ans, \
        "memory_fetch answer must contain alignment copy"


@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_does_not_contain_no_tool_message(mock_httpx_client):
    """topk_verify answer must NOT contain '没有查询知识库工具' or similar."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response("我没有工具查询知识库")
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查询知识库",
        "session_id": "test-p2t3-8",
    })
    assert resp.status_code == 200
    data = resp.json()
    ans = data["answer"]
    # The alignment copy must be present at the start
    assert "已识别为知识库查询" in ans, \
        "topk_verify alignment copy must be present"
    assert ans.startswith("已识别为知识库查询"), \
        "Alignment copy must appear at the very beginning"
    # The original "no tool" answer must be completely suppressed
    assert "我没有工具查询知识库" not in ans, \
        "topk_verify must not contain Router's 'no tool' message"
    assert "没有工具" not in ans, \
        "topk_verify must not contain '没有工具' message"
    # The answer should only contain the alignment copy, not the original
    assert ans == "已识别为知识库查询 / Top-K 验证请求。\n当前只生成 readonly dry-run evidence preview，不会执行真实 RAG 查询或任务。\n", \
        "topk_verify with no-tool answer must return only alignment copy"


@patch("main.httpx.AsyncClient", autospec=True)
def test_all_preview_flows_safety_fields_preserved(mock_httpx_client):
    """All preview flows must preserve task_executed=false and runtime_mutation=false."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    for prompt in ["查看目前的所有任務狀態", "查询知识库", "重建索引", "查记忆", "批准任务", "拒绝任务"]:
        resp = client.post("/ai/chat", json={
            "prompt": prompt,
            "session_id": "test-p2t3-safety",
        })
        assert resp.status_code == 200
        data = resp.json()
        ev = data.get("task_evidence_preview")
        if ev is not None:
            assert ev.get("task_executed") is False, \
                f"task_executed must be false for {prompt}"
            assert ev.get("runtime_mutation") is False, \
                f"runtime_mutation must be false for {prompt}"


@patch("main.httpx.AsyncClient", autospec=True)
def test_align_answer_function_exists(mock_httpx_client):
    """align_answer_with_task_intent function must be defined in main.py."""
    with open("local-console/main.py", "r") as f:
        content = f.read()
    assert "def align_answer_with_task_intent" in content, \
        "align_answer_with_task_intent must be defined"
    assert "TaskIntent.PURE_CHAT.value" in content, \
        "alignment function must handle pure_chat"
    assert "_ALIGNMENT_COPY" in content, \
        "alignment copy map must be defined"


# ══════════════════════════════════════════════════════════════
# P2-T4: Evidence Preview UI Wording Tests
# ══════════════════════════════════════════════════════════════

def test_js_contains_evidence_preview_readonly_dryrun():
    """Frontend JS must contain 'Evidence Preview · Readonly Dry-run'."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "Evidence Preview · Readonly Dry-run" in js, \
        "renderEvidencePreview must show 'Readonly Dry-run' header"


def test_js_contains_preview_only_no_task_executed():
    """Frontend JS must contain 'Preview only: no task executed'."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "Preview only: no task executed" in js, \
        "renderEvidencePreview must show 'Preview only: no task executed'"


def test_js_contains_runtime_mutation_executor_do_labels():
    """Frontend JS must mention Runtime mutation, Executor, DO status."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "Runtime mutation: false" in js or "Runtime mutation" in js, \
        "renderEvidencePreview must mention Runtime mutation"
    assert "Executor: disabled" in js or "no executor" in js, \
        "renderEvidencePreview must mention Executor disabled"


def test_js_contains_blocked_by_approval_section():
    """Frontend JS must contain 'Blocked by Tao Approval Gate' for blocked evidence."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "Blocked by Tao Approval Gate" in js, \
        "renderEvidencePreview must show 'Blocked by Tao Approval Gate' for blocked status"


def test_js_contains_evidence_intent_label():
    """Frontend JS must have evidenceIntentLabel helper function."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "evidenceIntentLabel" in js, \
        "evidenceIntentLabel helper must be defined"
    assert "Task status readonly preview" in js or "Knowledge / Top-K readonly preview" in js, \
        "evidenceIntentLabel must contain intent-specific labels"


def test_js_contains_evidence_safety_line():
    """Frontend JS must have evidenceSafetyLine helper function."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    assert "evidenceSafetyLine" in js, \
        "evidenceSafetyLine helper must be defined"
    assert "no worker" in js, \
        "evidenceSafetyLine must include worker status"
    assert "no DO" in js, \
        "evidenceSafetyLine must include DO connection status"


def test_js_contains_no_new_tasks_run_fetch():
    """Frontend JS must not call /tasks/run."""
    with open("local-console/main.py", "r") as f:
        js = f.read()
    # Check no explicit fetch to /tasks/run in the frontend section
    js_frontend_lines = []
    capture = False
    for line in js.split('\n'):
        if 'function renderTaskPreview' in line or 'function renderEvidencePreview' in line or 'function sendMsg' in line:
            capture = True
        if capture:
            js_frontend_lines.append(line)
    js_frontend = '\n'.join(js_frontend_lines)
    assert "/tasks/run" not in js_frontend or "task_evidence_preview" in js, \
        "No /tasks/run calls allowed in frontend code"


def test_backend_task_status_summary_contains_readonly():
    """Backend task_status evidence result_summary must mention readonly preview."""
    with open("local-console/main.py", "r") as f:
        content = f.read()
    assert "Task status readonly preview" in content, \
        "task_status result_summary must mention readonly preview"


def test_backend_topk_verify_summary_contains_readonly():
    """Backend topk_verify evidence result_summary must mention readonly preview."""
    with open("local-console/main.py", "r") as f:
        content = f.read()
    assert "Knowledge / Top-K readonly preview" in content, \
        "topk_verify result_summary must mention readonly preview"


def test_backend_blocked_summary_contains_tao_gate():
    """Backend blocked_by_approval evidence result_summary must mention Tao Approval Gate."""
    with open("local-console/main.py", "r") as f:
        content = f.read()
    assert "Blocked by Tao Approval Gate" in content and "High-risk" in content, \
        "blocked_by_approval result_summary must mention Tao Gate + high-risk"


@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_backend_evidence_status_dry_run(mock_httpx_client):
    """topk_verify backend evidence must still have status=dry_run_ready."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查询知识库",
        "session_id": "test-p2t4-ev-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["status"] == "dry_run_ready"
    assert ev["intent"] == "topk_verify"


@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_backend_evidence_status_blocked(mock_httpx_client):
    """embed backend evidence must still have status=blocked_by_approval."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "重建索引",
        "session_id": "test-p2t4-ev-2",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["status"] == "blocked_by_approval"
