"""
GOAA Rule-based Intent Detection (P1-T2-U3)
============================================
Local-first, keyword/pattern-based intent classification for the
conversation→task dispatch pipeline.

No external side effects: no IO, no network, no shell, no LLM calls,
no cloud egress, no runtime mutation, no DO access.

Spec  section 2 — Intent Detection (MVP: rule_based_local_first)
Source: docs/runtime/GOAA_AI_WORKSPACE_CONVERSATION_TASK_FLOW_V0.1.yaml
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_envelope import (
    TaskIntent,
    DetectionMethod,
    TaskEnvelope,
    build_task_envelope,
    _has_secret_like_params,
)


# ══════════════════════════════════════════════════════════════
# RESULT DATACLASS
# ══════════════════════════════════════════════════════════════

@dataclass
class IntentDetectionResult:
    """Result of a single intent detection pass.

    Can be fed directly to build_task_envelope() for envelope construction.

    Fields
    ------
    intent : str
        Detected intent string (TaskIntent value).
    detection_method : str
        How the intent was detected (always 'rule_based' in MVP).
    confidence : float
        Detection confidence (0.0 .. 1.0).
    params : dict
        Extracted parameters (no secrets, no raw RAG text).
    message_clean : str
        The original message (for traceability).  Not passed to envelope.
        Useful for debugging and evidence traceability.
    """
    intent: str
    detection_method: str
    confidence: float
    params: dict
    message_clean: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════
# KEYWORD-BASED INTENT RULES
# ══════════════════════════════════════════════════════════════
# Order matters: rules are checked in priority order.
# More specific rules (e.g. approve/reject) take precedence over
# general ones (e.g. topk_verify).

_IntentRule = tuple[str, list[str], float]  # (intent, keywords, confidence)

_INTENT_RULES: list[_IntentRule] = [
    # approve / reject — exact phrases first to avoid false matches
    ("reject_task",  ["reject task", "deny task", "cancel task", "cancel", "don't approve",
                      "do not approve", "不同意", "拒绝任务"], 0.90),
    ("approve_task", ["approve task", "yes approve", "go ahead",
                      "批准任务", "同意"], 0.90),
    # embed — requires file/save/store intent
    ("embed",        ["rebuild index", "reindex", "build index",
                      "store corpus", "save corpus", "embed corpus",
                      "embedding", "重建索引"], 0.85),
    ("embed",        ["embed", "save file", "store data"], 0.60),
    # memory_fetch — prior context / recall
    ("memory_fetch", ["remember", "recall", "what did", "prior context",
                      "last session", "previous conversation",
                      "读取记忆", "查 session"], 0.80),
    ("memory_fetch", ["memory fetch", "查记忆"], 0.75),
    # topk_verify — search/lookup/query
    ("topk_verify",  ["search memory", "query rag", "search rag",
                      "lookup", "find in memory", "查 RAG",
                      "搜索记忆", "查询知识库", "查找"], 0.85),
    ("topk_verify",  ["topk", "verify", "rag", "search", "find",
                      "query"], 0.60),
    # task_status — check on tasks
    ("task_status",  ["task status", "task progress", "check task",
                      "有几个任务", "全部任务", "任务状态",
                      "查看任务", "当前任务", "有什么任务",
                      "任務狀態", "查看任務", "目前任務",
                      "任务在跑"], 0.85),
    ("task_status",  ["status", "progress", "envelope",
                      "查任务", "今天任务"], 0.65),
]

# Secret-like input patterns that must not enter params
_SECRET_VALUE_PATTERNS: list[str] = [
    r'secret\s*[:=]\s*\S+',
    r'token\s*[:=]\s*\S+',
    r'password\s*[:=]\s*\S+',
    r'private_key\s*[:=]\s*\S+',
    r'api_key\s*[:=]\s*\S+',
    r'ssh\s*key',
    r'id_rsa',
    r'id_ed25519',
]


# ══════════════════════════════════════════════════════════════
# DETECTOR
# ══════════════════════════════════════════════════════════════

def detect_intent_from_message(
    message: str,
    intent_hint: Optional[str] = None,
) -> IntentDetectionResult:
    """Classify user message intent using local rule-based matching.

    No external side effects — no IO, no network, no shell, no LLM calls,
    no cloud egress, no runtime mutation.

    Parameters
    ----------
    message : str
        The user's chat message.  Empty/whitespace-only messages return
        pure_chat with confidence 0.0.
    intent_hint : str or None
        Optional explicit intent hint from the caller.  If set to a valid
        TaskIntent value (not 'auto'), it overrides rule-based detection.
        If 'auto' or None, rule-based detection runs.

    Returns
    -------
    IntentDetectionResult
        The detection result with intent, confidence, and extracted params.

    Raises
    ------
    ValueError
        If intent_hint is set to an invalid TaskIntent value.
    """
    # Handle empty/whitespace-only messages
    if not message or not message.strip():
        return IntentDetectionResult(
            intent=TaskIntent.PURE_CHAT.value,
            detection_method=DetectionMethod.RULE_BASED.value,
            confidence=0.0,
            params={},
            message_clean="",
        )

    message_clean = message.strip()
    message_lower = message_clean.lower()

    # ── Override via intent_hint ──────────────────────────────
    if intent_hint and intent_hint != "auto":
        # Validate the hint is a known intent
        valid_intents = {e.value for e in TaskIntent}
        if intent_hint not in valid_intents:
            raise ValueError(
                f"Invalid intent_hint: '{intent_hint}'. "
                f"Must be one of: {sorted(valid_intents)}"
            )
        params = _extract_params(message_clean, intent_hint)
        params = _sanitize_params(params)
        return IntentDetectionResult(
            intent=intent_hint,
            detection_method=DetectionMethod.USER_HINT.value,
            confidence=1.0,
            params=params,
            message_clean=message_clean,
        )

    # ── Rule-based keyword matching ───────────────────────────
    # Check rules in priority order
    for intent, keywords, confidence in _INTENT_RULES:
        for keyword in keywords:
            if keyword in message_lower:
                params = _extract_params(message_clean, intent)
                # Safety: strip secret-like values from params
                params = _sanitize_params(params)
                return IntentDetectionResult(
                    intent=intent,
                    detection_method=DetectionMethod.RULE_BASED.value,
                    confidence=confidence,
                    params=params,
                    message_clean=message_clean,
                )

    # ── Default: pure_chat (no task dispatch) ─────────────────
    return IntentDetectionResult(
        intent=TaskIntent.PURE_CHAT.value,
        detection_method=DetectionMethod.RULE_BASED.value,
        confidence=0.50,
        params={},
        message_clean=message_clean,
    )


def _extract_params(message: str, intent: str) -> dict:
    """Extract task parameters from the message based on intent.

    No secrets, no raw RAG text, no private key paths.
    """
    params: dict = {}

    if intent == TaskIntent.TOPK_VERIFY.value:
        # Extract query text after/search/ keywords
        query = _extract_query_text(message)
        if query:
            params["query"] = query

    elif intent == TaskIntent.MEMORY_FETCH.value:
        query = _extract_query_text(message)
        if query:
            params["query"] = query

    elif intent == TaskIntent.EMBED.value:
        # Only store safe metadata, never file paths
        params["source"] = "conversation_input"

    elif intent == TaskIntent.APPROVE_TASK.value:
        # Extract task ID if present
        task_id = _extract_task_id(message)
        if task_id:
            params["task_id"] = task_id

    elif intent == TaskIntent.REJECT_TASK.value:
        task_id = _extract_task_id(message)
        if task_id:
            params["task_id"] = task_id
        reason = _extract_reject_reason(message)
        if reason:
            params["reason"] = reason

    # task_status and pure_chat: no params needed

    return params


def _extract_query_text(message: str) -> Optional[str]:
    """Extract the query portion from a search/lookup message.

    Tries to find text after common query prefixes.
    Returns None if no query text can be safely extracted.
    """
    patterns = [
        r'(?:search|find|query|lookup|查)\s+(?:for\s+|about\s+)?[""]?(.+?)[""]?$',
        r'(?:记忆|知识库)\s*(?:中|里)?\s*(?:的)?\s*(.+)$',
        r'[""]?(.+?)[""]?\s*(?:的)?(?:查询|搜索|查找)',
    ]
    for pattern in patterns:
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
            # Safety: cap length to avoid dumping large text
            if len(text) > 200:
                text = text[:200]
            return text
    return None


def _extract_task_id(message: str) -> Optional[str]:
    """Extract task ID from approval/rejection messages."""
    patterns = [
        r'task[_\s]?(?:id|#)?\s*[:=]?\s*(\S+)',
        r'任务\s*(?:id|#)?\s*[:=]?\s*(\S+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_reject_reason(message: str) -> Optional[str]:
    """Extract rejection reason from a reject message."""
    patterns = [
        r'(?:reason|because)\s*(?:[:=]\s*)?(.+?)$',
        r'reject\s+(?:task\s+)?(?:because|since|as|:)\s*(.+?)$',
    ]
    for pattern in patterns:
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            text = m.group(1).strip().strip('"').strip("'")
            if len(text) > 200:
                text = text[:200]
            return text
    return None


def _sanitize_params(params: dict) -> dict:
    """Remove secret-like content from params.

    Checks both keys and values for secret-like patterns.
    If a param key is secret-like, the entire key is removed.
    If a param value matches a secret pattern, the value is replaced
    with '<redacted>'.
    """
    if not params:
        return params

    sanitized: dict = {}
    for k, v in params.items():
        # Check if key itself is secret-like
        if _has_secret_like_params({k: v}):
            continue  # Skip secret-like keys entirely
        # Check if value matches secret patterns
        if isinstance(v, str):
            for pattern in _SECRET_VALUE_PATTERNS:
                if re.search(pattern, v, re.IGNORECASE):
                    sanitized[k] = "<redacted>"
                    break
            else:
                sanitized[k] = v
        else:
            sanitized[k] = v
    return sanitized


def build_envelope_from_detection(
    result: IntentDetectionResult,
    session_id: str,
    target_node: str = "local-aika-core-01",
) -> TaskEnvelope:
    """Build a TaskEnvelope from an IntentDetectionResult.

    Convenience wrapper that connects intent detection output to
    the envelope builder.  No external side effects.

    Parameters
    ----------
    result : IntentDetectionResult
        The detection result from detect_intent_from_message().
    session_id : str
        The source conversation session ID.
    target_node : str
        Target execution node.

    Returns
    -------
    TaskEnvelope
        The constructed task envelope.
    """
    return build_task_envelope(
        intent=result.intent,
        detection_method=result.detection_method,
        confidence=result.confidence,
        session_id=session_id,
        params=result.params,
        target_node=target_node,
    )
