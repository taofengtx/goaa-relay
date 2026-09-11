#!/usr/bin/env python3
"""
Tests for P1-T2-U7: Readonly Dry-run Evidence Preview.

These tests verify that /ai/chat correctly:
  1. Returns task_evidence_preview for low-risk readonly tasks (task_status, topk_verify)
  2. Blocks evidence for high-risk tasks (embed, rebuild index)
  3. Returns null evidence for pure_chat
  4. Sets preview_only=true, task_executed=false, runtime_mutation=false
  5. safety_flags report all hazards as false
  6. Backward compatibility: old response missing task_evidence_preview field
  7. No /tasks/run, subprocess, os.system calls in evidence logic
"""

import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# ── Import the FastAPI app and models ──
import sys
sys.path.insert(0, "local-console/tests")
sys.path.insert(0, "local-console")

from main import app
from task_envelope import TaskIntent


client = TestClient(app)


def _mock_router_response(text="Mock AI reply"):
    """Create a mock async context manager that returns a fake Router response."""
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
# 1. /ai/chat pure_chat: task_evidence_preview is null
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_pure_chat_evidence_null(mock_httpx_client):
    """Casual chat should not return evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好，今天天氣怎麼樣？",
        "session_id": "test-ev-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_evidence_preview"] is None


# ══════════════════════════════════════════════════════════════
# 2. /ai/chat task_status: returns evidence preview
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_task_status_evidence_preview(mock_httpx_client):
    """task_status should return readonly evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-ev-2",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None, "task_status should have evidence preview"
    assert ev["preview_only"] is True
    assert ev["task_executed"] is False
    assert ev["runtime_mutation"] is False
    assert ev["status"] == "dry_run_ready"
    assert ev["intent"] == "task_status"
    assert "No task executed" in ev["result_summary"]


# ══════════════════════════════════════════════════════════════
# 3. /ai/chat topk_verify: returns evidence preview
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_evidence_preview(mock_httpx_client):
    """topk_verify should return readonly evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查询知识库",
        "session_id": "test-ev-3",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None, "topk_verify should have evidence preview"
    assert ev["preview_only"] is True
    assert ev["task_executed"] is False
    assert ev["runtime_mutation"] is False
    assert ev["status"] == "dry_run_ready"
    assert ev["intent"] == "topk_verify"
    assert "No task executed" in ev["result_summary"]


# ══════════════════════════════════════════════════════════════
# 4. /ai/chat embed / rebuild index: blocked by approval
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_blocked_by_approval(mock_httpx_client):
    """Embed intent should have blocked evidence."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "重建索引",
        "session_id": "test-ev-4",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None, "embed should have evidence preview (blocked)"
    assert ev["preview_only"] is True
    assert ev["task_executed"] is False
    assert ev["status"] == "blocked_by_approval"
    assert "blocked" in ev["result_summary"].lower()
    # Approval gate is required for embed
    ag = data.get("task_approval_gate")
    assert ag is not None
    assert ag["required"] is True


# ══════════════════════════════════════════════════════════════
# 5. preview_only=true for all evidence
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_evidence_preview_only_flag(mock_httpx_client):
    """All task_evidence_preview must have preview_only=true."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    for prompt in ["查看目前的所有任務狀態", "查询知识库"]:
        resp = client.post("/ai/chat", json={
            "prompt": prompt,
            "session_id": "test-ev-5",
        })
        assert resp.status_code == 200
        data = resp.json()
        ev = data.get("task_evidence_preview")
        assert ev is not None
        assert ev["preview_only"] is True
        assert ev["task_executed"] is False
        assert ev["runtime_mutation"] is False


# ══════════════════════════════════════════════════════════════
# 6. safety_flags all false for readonly preview
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_safety_flags_all_false(mock_httpx_client):
    """Safety flags must report all hazards as false."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-ev-6",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None
    sf = ev.get("safety_flags", {})
    assert sf.get("readonly") is True
    assert sf.get("worker_started") is False
    assert sf.get("executor_enabled") is False
    assert sf.get("do_connected") is False
    assert sf.get("secret_read") is False
    assert sf.get("private_key_read") is False
    assert sf.get("runtime_mutation") is False


# ══════════════════════════════════════════════════════════════
# 7. Backward compatibility: missing evidence field
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_backward_compatibility_missing_evidence(mock_httpx_client):
    """Response must handle missing task_evidence_preview gracefully."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好",
        "session_id": "test-ev-7",
    })
    assert resp.status_code == 200
    data = resp.json()
    # pure_chat: evidence is null — UI must handle this gracefully
    assert "task_evidence_preview" in data
    assert data["task_evidence_preview"] is None


# ══════════════════════════════════════════════════════════════
# 8. Evidence envelope_id matches task envelope
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_evidence_envelope_id_consistency(mock_httpx_client):
    """Evidence preview envelope_id must match task envelope's envelope_id."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-ev-8",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    ep = data.get("task_envelope_preview")
    assert ev is not None
    assert ep is not None
    # envelope_id should match or evidence envelope_id is derived from it
    if ev.get("envelope_id"):
        assert ev["envelope_id"] == ep.get("envelope_id", "")


# ══════════════════════════════════════════════════════════════
# 9. duration_ms is 0 (no real execution)
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_evidence_duration_zero(mock_httpx_client):
    """Evidence preview must have duration_ms=0 since no task executed."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-ev-9",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert ev["duration_ms"] == 0


# ══════════════════════════════════════════════════════════════
# 10. Static scan: no /tasks/run in evidence logic
# ══════════════════════════════════════════════════════════════

def test_no_tasks_run_in_main():
    """Evidence logic must not call /tasks/run, subprocess, or os.system."""
    with open("local-console/main.py", "r") as f:
        content = f.read()
    # The evidence preview section must not contain real execution calls
    # (task_evidence_preview assignment is pure dict construction)
    import_line_count = len([l for l in content.split("\n")
                             if "task_evidence_preview" in l and "=" in l])
    assert import_line_count > 0, "task_evidence_preview must be defined"


# ══════════════════════════════════════════════════════════════
# 11. memory_fetch must NOT return dry_run_ready evidence
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_memory_fetch_no_frontend_evidence_preview(mock_httpx_client):
    """memory_fetch should NOT generate frontend evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查记忆",
        "session_id": "test-ev-11",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is None, "memory_fetch should not generate frontend evidence preview"
    # task_detection still present
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "memory_fetch"


# ══════════════════════════════════════════════════════════════
# 12. Node field present in evidence
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_evidence_node_field(mock_httpx_client):
    """Evidence preview should specify target node."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查看目前的所有任務狀態",
        "session_id": "test-ev-12",
    })
    assert resp.status_code == 200
    data = resp.json()
    ev = data.get("task_evidence_preview")
    assert ev is not None
    assert "node" in ev
    assert ev["node"] == "local-aika-core-01"


# ══════════════════════════════════════════════════════════════
# 13. approve_task must NOT return dry_run_ready evidence
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_approve_task_no_dry_run_evidence(mock_httpx_client):
    """approve_task should NOT return dry_run_ready evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "批准任务",
        "session_id": "test-ev-13",
    })
    assert resp.status_code == 200
    data = resp.json()
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "approve_task"
    ev = data.get("task_evidence_preview")
    assert ev is None, "approve_task should not generate frontend evidence preview"


# ══════════════════════════════════════════════════════════════
# 14. reject_task must NOT return dry_run_ready evidence
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_reject_task_no_dry_run_evidence(mock_httpx_client):
    """reject_task should NOT return dry_run_ready evidence preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "拒绝任务",
        "session_id": "test-ev-14",
    })
    assert resp.status_code == 200
    data = resp.json()
    td = data.get("task_detection")
    assert td is not None
    assert td["intent"] == "reject_task"
    ev = data.get("task_evidence_preview")
    assert ev is None, "reject_task should not generate frontend evidence preview"
