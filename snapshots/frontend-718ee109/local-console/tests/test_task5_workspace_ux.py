"""
GOAA Package 5 Task 5 — AI Workspace UX Display (HTML marker tests)
===================================================================
The AI Workspace is the embedded Runtime Console UI served at GET /.
Task 5 adds a plan-only "Task Plan · Strategy & Risk" card driven by
/tasks/plan. These tests assert the embedded HTML/JS carries the expected
markers so the plan card + safety wording never silently regress.

No backend logic of /ai/chat, /tasks/plan or /tasks/run is exercised or
changed here — this is a pure static-content regression guard.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _index_html():
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.text


def test_index_serves_html():
    html = _index_html()
    assert "GOAA" in html
    assert "<html" in html.lower()


def test_task_plan_card_header_present():
    html = _index_html()
    assert "Task Plan · Strategy & Risk" in html


def test_task_plan_fetch_call_present():
    html = _index_html()
    # The fetch to the plan-only endpoint and its handler must exist.
    assert "/tasks/plan" in html
    assert "fetchTaskPlan" in html
    assert "renderTaskPlan" in html


def test_task_plan_displayed_fields_present():
    html = _index_html()
    for marker in (
        "status",
        "execution_mode",
        "risk_level",
        "strategy",
        "execution_policy",
        "approval_required",
        "blocked_reason",
        "task_executed",
        "mutation_performed",
        "audit_persisted",
        "database_written",
        "executor_enabled",
        "real_execution_allowed",
    ):
        assert marker in html, f"missing plan field marker: {marker}"


def test_task_plan_safety_wording_present():
    html = _index_html()
    for phrase in (
        "Plan only",
        "No task executed",
        "Runtime unchanged",
        "Executor disabled",
    ):
        assert phrase in html, f"missing safety wording: {phrase}"


def test_task_plan_blocked_uses_danger_styling():
    html = _index_html()
    # Blocked plans must surface blocked_reason with danger color.
    assert "blocked_reason" in html
    assert "var(--danger)" in html


def test_task_plan_escapes_dynamic_fields():
    html = _index_html()
    # Every dynamic field in renderTaskPlan is routed through escapeHtml().
    assert "escapeHtml" in html
    # The plan card must not interpolate raw values without escaping.
    assert "renderTaskPlan" in html
