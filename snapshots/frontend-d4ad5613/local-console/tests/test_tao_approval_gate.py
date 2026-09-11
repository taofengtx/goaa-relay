#!/usr/bin/env python3
"""
Tests for P1-T2-U6: Tao Approval Gate.

These tests verify that /ai/chat correctly:
  1. Includes task_approval_gate for executable tasks
  2. Sets gate_status='awaiting_tao_approval' for risk_level>=4
  3. Sets gate_status='not_required' for risk_level<4
  4. Sets execution_allowed=false always (preview only)
  5. Missing task_approval_gate is backward compatible
  6. No /tasks/run calls, no worker/executor/DO
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
# 1. Pure chat — no approval gate
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_pure_chat_no_approval_gate(mock_httpx_client):
    """Casual chat has no approval gate."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好，今天天氣怎麼樣？",
        "session_id": "test-gate-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    # pure_chat → no approval gate
    assert data["task_approval_gate"] is None


# ══════════════════════════════════════════════════════════════
# 2. Task status — approval not required
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_task_status_gate_not_required(mock_httpx_client):
    """Task status (risk=0) should have gate not_required."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查一下任務狀態",
        "session_id": "test-gate-2",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    assert ag is not None
    assert ag["required"] is False
    assert ag["gate_status"] == "not_required"
    assert ag["execution_allowed"] is False


# ══════════════════════════════════════════════════════════════
# 3. Topk verify — approval not required
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_topk_verify_gate_not_required(mock_httpx_client):
    """Topk verify (risk=1) should have gate not_required."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "search memory for GOAA protocol",
        "session_id": "test-gate-3",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    assert ag is not None
    assert ag["required"] is False
    assert ag["gate_status"] == "not_required"
    assert ag["execution_allowed"] is False


# ══════════════════════════════════════════════════════════════
# 4. Embed / rebuild index — approval required
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_risk4_gate_awaiting_tao(mock_httpx_client):
    """Embed (risk=4) should have gate awaiting_tao_approval."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "rebuild index for all knowledge bases",
        "session_id": "test-gate-4",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    assert ag is not None
    assert ag["required"] is True
    assert ag["gate_status"] == "awaiting_tao_approval"
    assert ag["execution_allowed"] is False
    assert "risk_level=4" in ag["reason"]


# ══════════════════════════════════════════════════════════════
# 5. Embed response — execution_allowed is always false
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_embed_execution_not_allowed(mock_httpx_client):
    """Embed response must always have execution_allowed=false."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "rebuild index",
        "session_id": "test-gate-5",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    assert ag["execution_allowed"] is False


# ══════════════════════════════════════════════════════════════
# 6. Frontend renders approval gate without error
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_response_shape_has_approval_gate_fields(mock_httpx_client):
    """Response must contain all required task_approval_gate fields."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "rebuild index",
        "session_id": "test-gate-6",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    required = ["required", "gate_status", "reason", "approved_by_tao", "execution_allowed"]
    for field in required:
        assert field in ag, f"Missing field: {field}"


# ══════════════════════════════════════════════════════════════
# 7. Missing task_approval_gate — backward compatible
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_missing_approval_gate_backward_compatible(mock_httpx_client):
    """Old response without task_approval_gate should still work."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "what is GOAA",
        "session_id": "test-gate-7",
    })
    assert resp.status_code == 200
    data = resp.json()
    # pure_chat → gate is None (compatible with old clients)
    assert "task_approval_gate" in data
    # Old fields still present
    assert "ok" in data
    assert "answer" in data
    assert "session_id" in data
    assert "model" in data


# ══════════════════════════════════════════════════════════════
# 8. Approve/reject tasks — gate not_required (risk=2)
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_approve_task_gate_not_required(mock_httpx_client):
    """Approve task (risk=2) should have gate not_required."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "approve task 42",
        "session_id": "test-gate-8",
    })
    assert resp.status_code == 200
    data = resp.json()
    ag = data["task_approval_gate"]
    assert ag is not None
    assert ag["required"] is False
    assert ag["gate_status"] == "not_required"
    assert ag["execution_allowed"] is False


# ══════════════════════════════════════════════════════════════
# 9. Frontend card renders without error for all fields
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_envelope_preview_still_has_preview_only(mock_httpx_client):
    """Envelope preview must still have preview_only=true."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "search memory",
        "session_id": "test-gate-9",
    })
    assert resp.status_code == 200
    data = resp.json()
    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["preview_only"] is True


# ══════════════════════════════════════════════════════════════
# 10. No execution fields in approval gate
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_execution_not_started_in_response(mock_httpx_client):
    """Response must not contain any execution fields."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "rebuild index for all",
        "session_id": "test-gate-10",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Verify no execution indicators (P1-T2-U7: safety_flags now introspect but do not start execution)
    resp_str = json.dumps(data)
    assert "execution_started" not in resp_str

    # But our fields are present
    assert "task_approval_gate" in data
    assert "task_detection" in data
    assert "task_envelope_preview" in data
    # P1-T2-U7: evidence preview present for blocked tasks
    assert "task_evidence_preview" in data
    if data.get("task_evidence_preview"):
        ep = data["task_evidence_preview"]
        assert ep.get("preview_only") is True
        assert ep.get("task_executed") is False
        assert ep.get("runtime_mutation") is False
        # safety_flags remain introspective only
        sf = ep.get("safety_flags", {})
        assert sf.get("worker_started") is False
        assert sf.get("executor_enabled") is False
