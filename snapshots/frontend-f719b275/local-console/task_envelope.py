"""
GOAA Task Envelope Model & Builder (P1-T2-U2)
==============================================
Dataclasses and builders for the conversation→task dispatch envelope.

No external side effects: no IO, no network, no shell, no runtime mutation,
no secrets, no DO access.  The only in-process state is an in-memory monotonic
counter for envelope ID generation, which is not persisted across restarts.

Spec  source: docs/runtime/GOAA_AI_WORKSPACE_CONVERSATION_TASK_FLOW_V0.1.yaml
Breakdown:   docs/runtime/GOAA_AI_WORKSPACE_CONVERSATION_TASK_IMPLEMENTATION_BREAKDOWN_V0.1.yaml
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════

class TaskIntent(str, Enum):
    """Intents that map to structured task dispatch (spec section 2)."""
    EMBED = "embed"
    TOPK_VERIFY = "topk_verify"
    MEMORY_FETCH = "memory_fetch"
    TASK_STATUS = "task_status"
    APPROVE_TASK = "approve_task"
    REJECT_TASK = "reject_task"
    # pure_chat is NOT a dispatchable intent — it means "no task"
    PURE_CHAT = "pure_chat"


class DetectionMethod(str, Enum):
    """How the intent was detected (spec section 2.2)."""
    RULE_BASED = "rule_based"
    USER_HINT = "user_hint"
    OVERRIDE = "override"
    LLM_GUIDED_POST_MVP = "llm_guided_post_mvp"


class TaskRiskLevel(int, Enum):
    """Risk classification aligned with existing Router (1-4) + 0 (info-only).

    spec section 4 — Risk Classification.
    """
    INFORMATION_ONLY = 0     # No risk; pure chat, status check
    LOW = 1                  # Readonly query (e.g. topk_verify)
    MEDIUM = 2               # Memory fetch (readonly, in-memory)
    HIGH = 3                 # Role-gated / admin-gated (approve/reject)
    CRITICAL = 4             # Requires Tao approval (embed mutation)


class TaskEnvelopeStatus(str, Enum):
    """Lifecycle status for a task envelope (spec section 3).

    approved_envelope_only: MVP-specific — envelope is approved but actual
    mutation execution is deferred to post-MVP.
    """
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED_ENVELOPE_ONLY = "approved_envelope_only"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ══════════════════════════════════════════════════════════════
# DATACLASSES
# ══════════════════════════════════════════════════════════════

@dataclass
class TaskEnvelope:
    """Structured dispatch envelope (spec section 3 — task_envelope_schema).

    Created by intent detection before /tasks/run dispatch.  Pure data
    container — no methods that cause side effects.
    """
    envelope_id: str
    source_conversation_session: str
    intent: str                        # one of TaskIntent values (as string)
    detection_method: str              # one of DetectionMethod values (as string)
    confidence: float                  # 0.0 .. 1.0
    params: dict                       # task-specific parameters
    risk_level: int                    # 0..4
    status: str                        # one of TaskEnvelopeStatus values (as string)
    approval_required: bool
    target_node: str = "local-aika-core-01"
    created_at_utc: str = field(default_factory=lambda: _utc_now())

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-safe, no secrets)."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string.

        No raw RAG text, no secrets, no private keys.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def compute_sha256(self) -> str:
        """Deterministic hash of the JSON-serialized envelope.

        Used for evidence integrity checking.
        """
        return hashlib.sha256(self.to_json(indent=2).encode("utf-8")).hexdigest()


@dataclass
class EvidencePackage:
    """Evidence package returned after task lifecycle (spec section 7)."""
    task_id: str
    envelope_id: str
    source_session: str
    intent: str
    executor: str
    status: str
    started_at_utc: str
    completed_at_utc: str
    duration_ms: int
    output_summary: str
    evidence_sha256: str
    safety_flags: dict
    final_marker: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class SafetyFlags:
    """Safety flags for evidence package (spec section 7)."""
    repo_or_source_file_modified: bool = False
    task_envelope_persisted_allowed: bool = True
    commit_performed: bool = False
    push_performed: bool = False
    merge_performed: bool = False
    do_connected: bool = False
    secret_read_attempted: bool = False
    private_key_content_read_attempted: bool = False
    worker_started: bool = False
    executor_enabled: bool = False
    service_restarted: bool = False
    deploy_performed: bool = False
    runtime_mutated: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════
# BUILDERS (no external side effects: no IO/network/shell/runtime mutation)
# ══════════════════════════════════════════════════════════════

# Envelope ID counter — in-memory only, not persisted.
# The _next_sequence is a module-level monotonic counter for generating
# unique envelope IDs within the same process lifetime.  This is not
# a "pure function" — it mutates module state — but it has zero external
# side effects (no IO, network, shell, or disk writes).
_next_sequence: int = 0


def _generate_envelope_id() -> str:
    """Generate envelope ID in format GOAA-CONV-TASK-{YYYYMMDD}-{NNN}.

    This is a local-only, non-persistent counter.  In production the
    sequence would persist to /opt/goaa/task_results/.
    """
    global _next_sequence
    _next_sequence += 1
    seq = f"{_next_sequence:03d}"
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"GOAA-CONV-TASK-{today}-{seq}"


# Substring patterns for detecting secret-like param keys.
# Normalized key (lowercased, dashes/spaces → underscores) is checked
# against these patterns using substring matching, so e.g.
# "github_token", "openai_api_key", "my_secret_value" are all caught.
_SECRET_LIKE_KEY_PATTERNS = (
    "secret",
    "token",
    "password",
    "private_key",
    "key_file",
    "ssh",
    "api_key",
    "credential",
    "access_key",
)


def _has_secret_like_params(params: Optional[dict]) -> bool:
    """Check if params contains secret-like keys.

    Uses substring matching on normalized key names to catch variations
    like ``github_token``, ``my_secret_value``, ``ssh_private_key``.

    Returns True if any param key matches a secret-like pattern, or any
    string param value contains a path to sensitive locations.

    No false positives for short common words like ``"key"``, ``"file"``,
    or ``"id"`` — those are NOT in the pattern list.
    """
    if not params or not isinstance(params, dict):
        return False
    for k, v in params.items():
        key_normalized = k.lower().replace("-", "_").replace(" ", "_")
        if any(pattern in key_normalized for pattern in _SECRET_LIKE_KEY_PATTERNS):
            return True
        if isinstance(v, str):
            v_lower = v.lower()
            if any(p in v_lower for p in ("~/.ssh/", "id_rsa", "id_ed25519")):
                return True
    return False


def classify_risk_for_intent(intent: str, params: Optional[dict] = None) -> int:
    """Classify risk level (0-4) based on intent and optional params.

    spec section 4 — Risk Classification.

    Rule-based mapping:
      - pure_chat / task_status → 0 (information only)
      - topk_verify → 1 (low, readonly)
      - memory_fetch → 2 (medium, readonly in-memory)
      - approve_task / reject_task → 3 (high, role-gated)
      - embed → 4 (critical, requires Tao approval)

    Param-based escalation:
      - If params contains keys suggesting path/secret patterns → 4.
    """
    intent_lower = intent.lower().strip() if intent else ""

    # Base mapping
    base_map: dict[str, int] = {
        "pure_chat": 0,
        "task_status": 0,
        "topk_verify": 1,
        "memory_fetch": 2,
        "approve_task": 3,
        "reject_task": 3,
        "embed": 4,
    }

    level = base_map.get(intent_lower, 0)

    # Params-based escalation: path/secret patterns → 4
    if params and isinstance(params, dict):
        param_keys = [k.lower() for k in params.keys()]
        suspicious_patterns = ["path", "secret", "token", "password", "key_file", "private_key", "ssh"]
        if any(any(p in k for p in suspicious_patterns) for k in param_keys):
            level = max(level, 4)
        # String values containing path-like patterns
        for k, v in params.items():
            if isinstance(v, str):
                lower_v = v.lower()
                if "/home/" in lower_v or "/etc/" in lower_v or "~/.ssh/" in lower_v:
                    level = max(level, 4)
                    break

    return level


def is_approval_required(risk_level: int) -> bool:
    """Determine if Tao approval is required.

    spec section 5 — Tao Approval Gate:
      True only if risk_level >= 4.  risk_level 3 is role-gated/admin-gated,
      not Tao approval by default.

    spec Baton 8 fix: approval_required ONLY for risk_level >= 4.
    """
    return risk_level >= 4


def build_task_envelope(
    intent: str,
    detection_method: str,
    confidence: float,
    session_id: str,
    params: Optional[dict] = None,
    target_node: str = "local-aika-core-01",
) -> TaskEnvelope:
    """Build a TaskEnvelope from detection results.

    No external side effects — no IO, no network, no shell, no disk writes.
    The only mutable state is an in-memory envelope ID counter.

    Parameters
    ----------
    intent : str
        Detected intent. Must be a valid TaskIntent value or "pure_chat".
    detection_method : str
        How the intent was detected. Must be a valid DetectionMethod value.
    confidence : float
        Detection confidence (0.0 .. 1.0).
    session_id : str
        The source conversation session ID.
    params : dict or None
        Task-specific parameters (no secrets, no raw RAG text).
        Secret-like keys are rejected with ValueError.
    target_node : str
        Target execution node. Defaults to local-aika-core-01.

    Returns
    -------
    TaskEnvelope
        The constructed envelope with status, risk level, and
        approval_required pre-computed.

    Raises
    ------
    ValueError
        If intent is invalid, detection_method is invalid, confidence is
        out of range, or params contain secret-like keys.
    """
    # Validate intent
    valid_intents = {e.value for e in TaskIntent}
    if intent not in valid_intents:
        raise ValueError(
            f"Invalid intent: '{intent}'. "
            f"Must be one of: {sorted(valid_intents)}"
        )

    # Validate detection_method
    valid_methods = {e.value for e in DetectionMethod}
    if detection_method not in valid_methods:
        raise ValueError(
            f"Invalid detection_method: '{detection_method}'. "
            f"Must be one of: {sorted(valid_methods)}"
        )

    # Validate confidence
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(
            f"Confidence must be in range [0.0, 1.0], got {confidence}"
        )

    # Reject secret-like params that must not enter envelope JSON
    if _has_secret_like_params(params):
        raise ValueError(
            "Params contain secret-like keys (e.g. secret, token, password, "
            "private_key) and must not enter envelope JSON. "
            "Remove or replace before calling build_task_envelope."
        )

    # Pure chat: no task envelope needed
    if intent == "pure_chat":
        return TaskEnvelope(
            envelope_id=_generate_envelope_id(),
            source_conversation_session=session_id,
            intent=intent,
            detection_method=detection_method,
            confidence=confidence,
            params=params or {},
            risk_level=0,
            status=TaskEnvelopeStatus.PENDING.value,
            approval_required=False,
            target_node=target_node,
        )

    # Compute risk level
    risk_level = classify_risk_for_intent(intent, params)
    approval_required = is_approval_required(risk_level)

    # Determine initial status
    if approval_required:
        status = TaskEnvelopeStatus.AWAITING_APPROVAL.value
    else:
        status = TaskEnvelopeStatus.PENDING.value

    return TaskEnvelope(
        envelope_id=_generate_envelope_id(),
        source_conversation_session=session_id,
        intent=intent,
        detection_method=detection_method,
        confidence=confidence,
        params=params or {},
        risk_level=risk_level,
        status=status,
        approval_required=approval_required,
        target_node=target_node,
    )


def build_evidence_package(
    task_id: str,
    envelope: TaskEnvelope,
    status: str,
    executor: str,
    duration_ms: int,
    output_summary: str,
    safety_flags: Optional[SafetyFlags] = None,
) -> EvidencePackage:
    """Build an EvidencePackage from a completed task envelope.

    No external side effects — no IO, no network, no shell, no disk writes.
    """
    now_utc = _utc_now()
    flags = safety_flags or SafetyFlags()
    evidence = EvidencePackage(
        task_id=task_id,
        envelope_id=envelope.envelope_id,
        source_session=envelope.source_conversation_session,
        intent=envelope.intent,
        executor=executor,
        status=status,
        started_at_utc=envelope.created_at_utc,
        completed_at_utc=now_utc,
        duration_ms=duration_ms,
        output_summary=output_summary,
        evidence_sha256=envelope.compute_sha256(),
        safety_flags=flags.to_dict(),
        final_marker=f"GOAA_{envelope.intent.upper()}_{envelope.envelope_id}_EVIDENCE_PACKAGE",
    )
    return evidence


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _utc_now() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
