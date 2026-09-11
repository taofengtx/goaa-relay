"""
GOAA Shell Capability V0 — Validator (刀 1)
============================================
Pure validation logic: schema checks, template resolution, blocklist
scanning.  No subprocess, no os.system, no file system reads.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md
Policy version: shell-v0.1-knife1
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from shell_schema import (
    ApprovedUnit,
    GitRevParseMode,
    ShellTaskRequest,
    ShellValidationResult,
    ValidationStatus,
)
from shell_policy import (
    ALLOWED_RESOURCE_NAMES,
    ALLOWED_TEMPLATE_IDS,
    APPROVED_UNITS,
    BLOCKED_COMMANDS,
    BLOCKED_PATH_GLOBS,
    BLOCKED_PATH_NAMES,
    BLOCKED_PATH_PREFIXES,
    BLOCKED_PATH_SUFFIXES,
    BLOCKED_SHELL_CHARS,
    GIT_REV_PARSE_MODES,
    POLICY_VERSION,
    RESOURCE_MAP,
    TEMPLATE_POLICY,
    _template_argv,
)

# ── Metadata keys that MUST NOT control argv generation ────────────
# If any of these appear in request.metadata the request is rejected.

RESERVED_METADATA_KEYS: frozenset = frozenset({
    "option", "mode", "git_mode", "unit", "unit_name",
    "argv", "command", "raw_command", "cwd", "env",
})

# ── Helpers ────────────────────────────────────────────────────────


def _contains_blocked_token(text: str) -> Tuple[bool, str]:
    """Check *text* for blocked shell tokens.  Returns (found, detail)."""
    tokens_lower = text.lower()
    for cmd in BLOCKED_COMMANDS:
        pattern = re.compile(rf'\b{re.escape(cmd)}\b')
        if pattern.search(tokens_lower):
            return True, f"blocked command: {cmd}"

    for ch in BLOCKED_SHELL_CHARS:
        if ch in text:
            return True, f"blocked shell character: {repr(ch)}"

    if "\n" in text or "\r" in text:
        return True, "newline character in request field"

    return False, ""


def _contains_blocked_path(text: str) -> Tuple[bool, str]:
    """Check if *text* references a blocked path pattern."""
    for prefix in BLOCKED_PATH_PREFIXES:
        if text.startswith(prefix):
            return True, f"blocked path prefix: {prefix}"

    for suffix in BLOCKED_PATH_SUFFIXES:
        if text.endswith(suffix):
            return True, f"blocked path suffix: {suffix}"

    for name in BLOCKED_PATH_NAMES:
        if f"/{name}" in text or text == name:
            return True, f"blocked path name: {name}"

    for globp in BLOCKED_PATH_GLOBS:
        if text.startswith(globp.rstrip("*")):
            return True, f"blocked path glob: {globp}"

    if ".." in text.split("/"):
        return True, "path traversal: .."

    if "~" in text:
        return True, "tilde path expansion"

    return False, ""


# ── Runtime type guard helpers ─────────────────────────────────────


def _check_git_mode_type(git_mode: object) -> Optional[ShellValidationResult]:
    """Return a rejection if *git_mode* is not a GitRevParseMode or None."""
    if git_mode is not None and not isinstance(git_mode, GitRevParseMode):
        return _reject(
            ValidationStatus.REJECTED_ARGUMENT,
            "INVALID_GIT_MODE_TYPE",
            f"git_mode must be GitRevParseMode, got {type(git_mode).__name__}",
        )
    return None


def _check_unit_name_type(unit_name: object) -> Optional[ShellValidationResult]:
    """Return a rejection if *unit_name* is not an ApprovedUnit or None."""
    if unit_name is not None and not isinstance(unit_name, ApprovedUnit):
        return _reject(
            ValidationStatus.REJECTED_ARGUMENT,
            "INVALID_UNIT_NAME_TYPE",
            f"unit_name must be ApprovedUnit, got {type(unit_name).__name__}",
        )
    return None


# ── Main validator ─────────────────────────────────────────────────


def validate_request(request: ShellTaskRequest) -> ShellValidationResult:
    """Validate a ``ShellTaskRequest`` against the V0 knife 1 policy.

    This is a pure function: no side effects, no I/O, no subprocess.
    """

    # ── 1. Schema-level checks ─────────────────────────────────────
    if not request.task_id or not request.task_id.strip():
        return _reject(ValidationStatus.REJECTED_ARGUMENT,
                       "EMPTY_TASK_ID", "task_id must not be empty")
    if not request.template_id or not request.template_id.strip():
        return _reject(ValidationStatus.REJECTED_ARGUMENT,
                       "EMPTY_TEMPLATE_ID", "template_id must not be empty")

    # ── 2. Reserved metadata keys ──────────────────────────────────
    # metadata is for audit labels only; it must NEVER control argv.
    for key in request.metadata:
        if key in RESERVED_METADATA_KEYS:
            return _reject(
                ValidationStatus.REJECTED_ARGUMENT,
                "RESERVED_METADATA_KEY",
                f"metadata key '{key}' is reserved and must not control argv",
            )

    # ── 3. Block-token scan on all string fields ───────────────────
    scan_fields: Dict[str, str] = {
        "task_id": request.task_id,
        "template_id": request.template_id,
    }
    if request.resource_name:
        scan_fields["resource_name"] = request.resource_name
    if request.requested_by:
        scan_fields["requested_by"] = request.requested_by
    if request.approval_id:
        scan_fields["approval_id"] = request.approval_id

    for field_name, field_value in scan_fields.items():
        found, detail = _contains_blocked_token(field_value)
        if found:
            return _reject(ValidationStatus.REJECTED_POLICY,
                           "BLOCKED_TOKEN",
                           f"blocked token in {field_name}: {detail}")

    # ── 4. Template validation ─────────────────────────────────────
    tid = request.template_id.strip()
    if tid not in ALLOWED_TEMPLATE_IDS:
        return _reject(ValidationStatus.REJECTED_TEMPLATE,
                       "UNKNOWN_TEMPLATE",
                       f"unknown template_id: {request.template_id!r}")

    # ── 5. Resource validation ─────────────────────────────────────
    resource_name: Optional[str] = request.resource_name
    template_needs_resource, _ = _template_requires_resource(tid)
    if template_needs_resource:
        if not resource_name:
            return _reject(ValidationStatus.REJECTED_RESOURCE,
                           "MISSING_RESOURCE",
                           f"{tid} requires a resource")
        resource_stripped = resource_name.strip()
        if resource_stripped not in ALLOWED_RESOURCE_NAMES:
            return _reject(ValidationStatus.REJECTED_RESOURCE,
                           "UNKNOWN_RESOURCE",
                           f"unknown resource: {resource_name!r}")
        found, detail = _contains_blocked_token(resource_stripped)
        if found:
            return _reject(ValidationStatus.REJECTED_POLICY,
                           "BLOCKED_TOKEN",
                           f"blocked token in resource_name: {detail}")
        found, detail = _contains_blocked_path(resource_stripped)
        if found:
            return _reject(ValidationStatus.REJECTED_POLICY,
                           "BLOCKED_PATH",
                           f"blocked path in resource_name: {detail}")
    else:
        if resource_name:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNEXPECTED_RESOURCE",
                           f"{tid} does not accept a resource")

    # ── 5b. Runtime type guard: git_mode / unit_name ───────────────
    # Check BEFORE accessing .value to prevent AttributeError.
    rejection = _check_git_mode_type(request.git_mode)
    if rejection is not None:
        return rejection
    rejection = _check_unit_name_type(request.unit_name)
    if rejection is not None:
        return rejection

    # ── 6. Template-specific explicit field validation ─────────────
    # git_rev_parse → git_mode required, unit_name forbidden
    # systemctl_is_active → unit_name required, git_mode forbidden
    # all others → git_mode AND unit_name must be None

    if tid == "git_rev_parse":
        if request.git_mode is None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "MISSING_GIT_MODE",
                           "git_rev_parse requires git_mode (HEAD_SHORT|BRANCH_NAME)")
        if request.unit_name is not None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNEXPECTED_UNIT_NAME",
                           "git_rev_parse must not have unit_name")
        mode_value = request.git_mode.value
        if mode_value not in GIT_REV_PARSE_MODES:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "INVALID_GIT_MODE",
                           f"invalid git_rev_parse mode: {mode_value!r}")
        found, detail = _contains_blocked_token(mode_value)
        if found:
            return _reject(ValidationStatus.REJECTED_POLICY,
                           "BLOCKED_TOKEN",
                           f"blocked token in git_mode: {detail}")

    elif tid == "systemctl_is_active":
        if request.unit_name is None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "MISSING_UNIT_NAME",
                           "systemctl_is_active requires unit_name")
        if request.git_mode is not None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNEXPECTED_GIT_MODE",
                           "systemctl_is_active must not have git_mode")
        unit_value = request.unit_name.value
        if unit_value not in APPROVED_UNITS:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNKNOWN_UNIT",
                           f"unapproved systemd unit: {unit_value!r}")
        found, detail = _contains_blocked_token(unit_value)
        if found:
            return _reject(ValidationStatus.REJECTED_POLICY,
                           "BLOCKED_TOKEN",
                           f"blocked token in unit_name: {detail}")

    else:
        # Simple templates must not have git_mode or unit_name
        if request.git_mode is not None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNEXPECTED_GIT_MODE",
                           f"{tid} must not have git_mode")
        if request.unit_name is not None:
            return _reject(ValidationStatus.REJECTED_ARGUMENT,
                           "UNEXPECTED_UNIT_NAME",
                           f"{tid} must not have unit_name")

    # ── 7. Resolve argv from Policy ────────────────────────────────
    try:
        if tid == "git_rev_parse":
            resolved_argv = _template_argv(tid, request.git_mode.value)
        elif tid == "systemctl_is_active":
            resolved_argv = _template_argv(tid, request.unit_name.value)
        else:
            resolved_argv = _template_argv(tid)
    except (KeyError, ValueError) as exc:
        return _reject(
            ValidationStatus.REJECTED_TEMPLATE,
            "ARGV_RESOLVE_FAILURE",
            str(exc),
        )

    # ── 8. Substitute resource path ────────────────────────────────
    if template_needs_resource and resource_name:
        resolved_path = RESOURCE_MAP[resource_name.strip()]
        resolved_argv = [
            arg.replace("<resolved_resource>", resolved_path)
            for arg in resolved_argv
        ]

    # ── 9. Build result ────────────────────────────────────────────
    pol = TEMPLATE_POLICY[tid]
    return ShellValidationResult(
        status=ValidationStatus.VALID,
        template_id=tid,
        resource_name=resource_name.strip() if resource_name else None,
        resolved_argv=resolved_argv,
        timeout_seconds=pol[0],
        stdout_limit_bytes=pol[1],
        stderr_limit_bytes=pol[2],
        risk_level=pol[3],
        requires_approval=pol[5],
        policy_version=POLICY_VERSION,
    )


def _reject(status: ValidationStatus, code: str, reason: str,
            tid: str = "", resource: Optional[str] = None
            ) -> ShellValidationResult:
    """Convenience: return a rejection result."""
    return ShellValidationResult(
        status=status,
        template_id=tid,
        resource_name=resource,
        reason_code=code,
        reason=reason,
        policy_version=POLICY_VERSION,
    )


def _template_requires_resource(tid: str) -> Tuple[bool, str]:
    """Return (needs_resource, risk_level) for *tid*."""
    pol = TEMPLATE_POLICY.get(tid)
    if pol is None:
        return False, "low"
    return pol[4], pol[3]
