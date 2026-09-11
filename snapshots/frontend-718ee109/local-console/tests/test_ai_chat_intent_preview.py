#!/usr/bin/env python3
"""
Tests for P1-T2-U4: /ai/chat → Intent Detection + Task Envelope Preview.

These tests verify that /ai/chat correctly:
  1. Returns intent detection alongside the AI reply
  2. Builds a task envelope preview for executable intents
  3. Sets preview_only=true (never actually executes the task)
  4. Sanitizes secret-like content from task_detection.params
  5. Preserves backward compatibility (old fields still present)
  6. Returns None envelope for pure_chat intents
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
# 1. /ai/chat 普通聊天 (pure_chat)
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_casual_pure_chat(mock_httpx_client):
    """Casual chat should detect pure_chat, no envelope preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "你好，今天天氣怎麼樣？",
        "session_id": "test-session-1",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Backward compatibility: old fields exist
    assert "ok" in data
    assert "answer" in data
    assert "session_id" in data
    assert "model" in data

    # Task detection present
    assert "task_detection" in data
    td = data["task_detection"]
    assert td["intent"] == TaskIntent.PURE_CHAT.value
    assert td["detection_method"] == "rule_based"
    assert td["confidence"] > 0
    assert td["is_executable_task"] is False

    # No envelope preview for pure_chat
    assert data["task_envelope_preview"] is None


# ══════════════════════════════════════════════════════════════
# 2. /ai/chat task status 查詢
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_task_status(mock_httpx_client):
    """Task status queries should detect task_status intent and generate preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "查一下任務狀態",
        "session_id": "test-session-2",
    })
    assert resp.status_code == 200
    data = resp.json()

    td = data["task_detection"]
    assert td["intent"] == TaskIntent.TASK_STATUS.value
    assert td["detection_method"] == "rule_based"
    assert td["confidence"] >= 0.85
    assert td["is_executable_task"] is True

    # Envelope preview present
    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["intent"] == TaskIntent.TASK_STATUS.value
    assert ep["risk_level"] == 0  # readonly
    assert ep["approval_required"] is False
    assert ep["preview_only"] is True
    assert ep["status"] == "pending"
    assert "envelope_id" in ep
    assert "target_node" in ep


# ══════════════════════════════════════════════════════════════
# 3. /ai/chat topk_verify 查詢
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_topk_verify(mock_httpx_client):
    """Search queries should detect topk_verify intent and generate preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "search memory for GOAA protocol",
        "session_id": "test-session-3",
    })
    assert resp.status_code == 200
    data = resp.json()

    td = data["task_detection"]
    assert td["intent"] == TaskIntent.TOPK_VERIFY.value
    assert td["is_executable_task"] is True

    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["intent"] == TaskIntent.TOPK_VERIFY.value
    assert ep["preview_only"] is True
    assert ep["status"] == "pending"

    # Params should contain the query (sanitized)
    assert td["params"].get("query", "") != ""


# ══════════════════════════════════════════════════════════════
# 4. /ai/chat embed / reindex (risk_level=4, requires approval)
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_embed_risk4(mock_httpx_client):
    """Rebuild index should detect embed intent, risk=4, approval_required=true."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "rebuild index for all knowledge bases",
        "session_id": "test-session-4",
    })
    assert resp.status_code == 200
    data = resp.json()

    td = data["task_detection"]
    assert td["intent"] == TaskIntent.EMBED.value
    assert td["is_executable_task"] is True

    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["intent"] == TaskIntent.EMBED.value
    assert ep["risk_level"] == 4
    assert ep["approval_required"] is True
    assert ep["preview_only"] is True
    assert ep["status"] == "awaiting_approval"  # risk>=4 → auto-pending approval


# ══════════════════════════════════════════════════════════════
# 5. Secret/token safe — NOT in response JSON params
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_secret_sanitized(mock_httpx_client):
    """Secret-like content in prompt must NOT appear in response JSON."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "search for token=ghp_abc123def456",
        "session_id": "test-session-5",
    })
    assert resp.status_code == 200
    data = resp.json()
    td = data["task_detection"]

    # Secret must not appear anywhere in the response
    resp_str = json.dumps(data)
    assert "ghp_abc123def456" not in resp_str
    assert "abc123def456" not in resp_str

    # But params should still have a query (non-empty, sanitized)
    if td["params"].get("query"):
        assert "token=" not in td["params"]["query"]


# ══════════════════════════════════════════════════════════════
# 6. Backward compatibility — old fields still present
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_backward_compatible(mock_httpx_client):
    """Old AIChatResp fields must still exist for frontend compatibility."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "what is GOAA",
        "session_id": "test-session-6",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Core fields (existed before P1-T2-U4)
    assert "ok" in data
    assert "answer" in data
    assert "session_id" in data
    assert "model" in data
    assert "duration_ms" in data
    assert "cost_usd" in data
    assert "mock" in data
    assert "route" in data

    # New fields (P1-T2-U4 additions)
    assert "task_detection" in data
    assert "task_envelope_preview" in data


# ══════════════════════════════════════════════════════════════
# 7. No task execution — preview_only=true only
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_no_execution(mock_httpx_client):
    """/ai/chat must NEVER execute a task — only generate preview."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "search for important documents about AI safety",
        "session_id": "test-session-7",
    })
    assert resp.status_code == 200
    data = resp.json()

    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["preview_only"] is True
    assert ep["status"] == "pending"
    # Ensure no execution fields are set
    assert "execution_started" not in ep
    assert "executed_by" not in ep
    assert "completed_at" not in ep


# ══════════════════════════════════════════════════════════════
# 8. Approve/reject tasks — preview only
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_approve_reject_preview(mock_httpx_client):
    """Approve/reject messages get detection + preview, no execution."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "approve task 42",
        "session_id": "test-session-8",
    })
    assert resp.status_code == 200
    data = resp.json()

    td = data["task_detection"]
    assert td["intent"] == TaskIntent.APPROVE_TASK.value
    assert td["is_executable_task"] is True

    ep = data["task_envelope_preview"]
    assert ep is not None
    assert ep["intent"] == TaskIntent.APPROVE_TASK.value
    assert ep["preview_only"] is True
    assert ep["status"] == "pending"
    # task_id should be in params
    assert td["params"].get("task_id") == "42"


# ══════════════════════════════════════════════════════════════
# 9. Empty/whitespace prompt — graceful handling
# ══════════════════════════════════════════════════════════════

def test_ai_chat_empty_prompt():
    """Empty prompt should still produce a valid response."""
    resp = client.post("/ai/chat", json={
        "prompt": "",
        "session_id": "test-session-9",
    })
    # FastAPI validation may reject empty prompt at model level
    assert resp.status_code in (200, 422)


# ══════════════════════════════════════════════════════════════
# 10. Envelope has all required fields
# ══════════════════════════════════════════════════════════════

@patch("main.httpx.AsyncClient", autospec=True)
def test_ai_chat_envelope_fields_complete(mock_httpx_client):
    """Task envelope preview must contain all required fields."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value.post = _mock_router_response()
    mock_httpx_client.return_value = mock_ctx

    resp = client.post("/ai/chat", json={
        "prompt": "檢查全部任務狀態",
        "session_id": "test-session-10",
    })
    assert resp.status_code == 200
    data = resp.json()
    ep = data["task_envelope_preview"]

    assert ep is not None
    required = [
        "envelope_id", "intent", "risk_level",
        "approval_required", "status", "target_node",
        "preview_only",
    ]
    for field in required:
        assert field in ep, f"Missing field: {field}"
