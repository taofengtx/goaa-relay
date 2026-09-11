"""
GOAA Shell Capability V0 — Execution Plan Verification (刀 2A-1)
=============================================================
Independent 9-dimension policy verification layer that sits between
the Validator and the Executor.  Its job is to confirm that every
field in a ``ShellValidationResult`` matches what the current Policy
expects, catching any forged or corrupted result objects.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md §20
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from shell_policy import (
    ALLOWED_RESOURCE_NAMES,
    ALLOWED_TEMPLATE_IDS,
    APPROVED_UNITS,
    POLICY_VERSION,
    RESOURCE_MAP,
    TEMPLATE_POLICY,
    _template_argv,
)
from shell_schema import ShellValidationResult


# ── Verification result ────────────────────────────────────────────


@dataclass(frozen=True)
class PlanVerificationResult:
    """Result of an execution-plan verification."""

    verified: bool
    reason_code: str = ""
    details: str = ""


# ── Helpers ────────────────────────────────────────────────────────


def _recompute_expected_argv(
    result: ShellValidationResult,
) -> List[str]:
    """
    Recompute the expected argv from Policy for the given result.

    This is the key defense against forged ``ShellValidationResult``
    objects.  It calls ``_template_argv()`` from Policy and, for
    variable templates (git_rev_parse, systemctl_is_active), accepts
    any one of the valid argv variants.
    """
    tid = result.template_id

    # Templates with no variable parts — simple lookup
    if tid in ("pwd", "whoami", "hostname"):
        return _template_argv(tid)

    if tid == "date_iso":
        return _template_argv(tid)
    if tid == "uptime_pretty":
        return _template_argv(tid)
    if tid == "free_human":
        return _template_argv(tid)
    if tid == "df_summary":
        return _template_argv(tid)

    # Templates with variable parts — check against all valid variants

    if tid == "git_status_short":
        # Resolve <resolved_resource> placeholder
        resource = result.resource_name
        if resource not in RESOURCE_MAP:
            raise PlanRejected(f"git_status_short: unknown resource {resource!r}")
        expected = [
            "git", "-C", RESOURCE_MAP[resource], "status", "--short"
        ]
        return expected

    if tid == "git_rev_parse":
        resource = result.resource_name
        if resource not in RESOURCE_MAP:
            raise PlanRejected(f"git_rev_parse: unknown resource {resource!r}")
        rp = RESOURCE_MAP[resource]
        argv_head = ["git", "-C", rp, "rev-parse", "--short", "HEAD"]
        argv_branch = [
            "git", "-C", rp, "rev-parse", "--abbrev-ref", "HEAD"
        ]
        # Accept either variant
        if result.resolved_argv == argv_head:
            return result.resolved_argv
        if result.resolved_argv == argv_branch:
            return result.resolved_argv
        # Neither matched — forge detected
        raise PlanRejected(
            f"git_rev_parse argv mismatch: "
            f"expected {argv_head!r} or {argv_branch!r}, "
            f"got {result.resolved_argv!r}"
        )

    if tid == "systemctl_is_active":
        if not result.resolved_argv:
            raise PlanRejected("systemctl_is_active: empty argv")
        unit = result.resolved_argv[-1]
        if unit not in APPROVED_UNITS:
            raise PlanRejected(
                f"systemctl_is_active: unapproved unit {unit!r}"
            )
        return ["systemctl", "is-active", unit]

    raise PlanRejected(f"unknown template: {tid}")


class PlanRejected(Exception):
    """Raised when argv recomputation fails."""


# ── Main verification function ─────────────────────────────────────


def verify_execution_plan(
    result: ShellValidationResult,
) -> PlanVerificationResult:
    """
    Independently verify a ``ShellValidationResult`` against the
    current Policy across 9 dimensions.

    This is the **last gate before ``subprocess.run``**.  All 9
    dimensions must match exactly; any mismatch produces a
    ``PlanVerificationResult(verified=False)`` with a clear
    ``reason_code`` and ``details``.
    """
    tid = result.template_id
    rn = result.resource_name

    # ── 1. template_id ─────────────────────────────────────────────
    if tid not in ALLOWED_TEMPLATE_IDS:
        return PlanVerificationResult(
            verified=False,
            reason_code="UNKNOWN_TEMPLATE",
            details=f"template_id {tid!r} not in ALLOWED_TEMPLATE_IDS",
        )

    # ── 2. policy_version ──────────────────────────────────────────
    if result.policy_version != POLICY_VERSION:
        return PlanVerificationResult(
            verified=False,
            reason_code="POLICY_VERSION_MISMATCH",
            details=(
                f"expected {POLICY_VERSION!r}, "
                f"got {result.policy_version!r}"
            ),
        )

    # ── 3. resource_name ───────────────────────────────────────────
    policy = TEMPLATE_POLICY[tid]
    needs_resource: bool = policy[4]  # index 4 = needs_resource
    if needs_resource:
        if rn is None:
            return PlanVerificationResult(
                verified=False,
                reason_code="MISSING_RESOURCE",
                details=(
                    f"template {tid!r} requires a resource_name, "
                    f"got None"
                ),
            )
        if rn not in ALLOWED_RESOURCE_NAMES:
            return PlanVerificationResult(
                verified=False,
                reason_code="UNKNOWN_RESOURCE",
                details=(
                    f"resource_name {rn!r} not in "
                    f"ALLOWED_RESOURCE_NAMES"
                ),
            )

    # ── 4. resolved_argv ───────────────────────────────────────────
    try:
        expected_argv = _recompute_expected_argv(result)
    except PlanRejected as e:
        return PlanVerificationResult(
            verified=False,
            reason_code="ARGV_MISMATCH",
            details=str(e),
        )

    if result.resolved_argv != expected_argv:
        return PlanVerificationResult(
            verified=False,
            reason_code="ARGV_MISMATCH",
            details=(
                f"expected {expected_argv!r}, "
                f"got {result.resolved_argv!r}"
            ),
        )

    # ── 5. timeout_seconds ─────────────────────────────────────────
    expected_timeout: int = policy[0]
    if result.timeout_seconds != expected_timeout:
        return PlanVerificationResult(
            verified=False,
            reason_code="TIMEOUT_MISMATCH",
            details=(
                f"expected {expected_timeout}, "
                f"got {result.timeout_seconds}"
            ),
        )

    # ── 6. stdout_limit_bytes ──────────────────────────────────────
    expected_stdout: int = policy[1]
    if result.stdout_limit_bytes != expected_stdout:
        return PlanVerificationResult(
            verified=False,
            reason_code="STDOUT_LIMIT_MISMATCH",
            details=(
                f"expected {expected_stdout}, "
                f"got {result.stdout_limit_bytes}"
            ),
        )

    # ── 7. stderr_limit_bytes ──────────────────────────────────────
    expected_stderr: int = policy[2]
    if result.stderr_limit_bytes != expected_stderr:
        return PlanVerificationResult(
            verified=False,
            reason_code="STDERR_LIMIT_MISMATCH",
            details=(
                f"expected {expected_stderr}, "
                f"got {result.stderr_limit_bytes}"
            ),
        )

    # ── 8. risk_level ──────────────────────────────────────────────
    expected_risk: str = policy[3]
    if result.risk_level != expected_risk:
        return PlanVerificationResult(
            verified=False,
            reason_code="RISK_LEVEL_MISMATCH",
            details=(
                f"expected {expected_risk!r}, "
                f"got {result.risk_level!r}"
            ),
        )

    # ── 9. requires_approval ───────────────────────────────────────
    expected_approval: bool = policy[5]
    if result.requires_approval != expected_approval:
        return PlanVerificationResult(
            verified=False,
            reason_code="APPROVAL_MISMATCH",
            details=(
                f"expected requires_approval={expected_approval}, "
                f"got {result.requires_approval}"
            ),
        )

    return PlanVerificationResult(
        verified=True,
        reason_code="VERIFIED",
        details="all 9 dimensions match policy",
    )
