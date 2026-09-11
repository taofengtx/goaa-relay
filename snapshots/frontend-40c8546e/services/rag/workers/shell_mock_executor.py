"""
GOAA Shell Capability V0 — Mock Executor (刀 2A-1)
===================================================
Pure mock of the Shell Executor, suitable for unit testing.
No subprocess, no os.system, no os.popen — all execution is
simulated based on template_id alone.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md §20
Usage:
    from shell_mock_executor import MockShellExecutor
    executor = MockShellExecutor()
    result = executor.execute_shell(validated_result)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional

from shell_schema import ShellValidationResult, ValidationStatus

from shell_execution_plan import (
    PlanVerificationResult,
    verify_execution_plan,
)
from shell_resource_policy import (
    RESOURCE_POLICIES,
    verify_runtime_path_evidence,
)


# ── Executor result type ───────────────────────────────────────────


class ExecutorStatus:
    """Executor result status strings."""

    SUCCESS = "succeeded"
    EXECUTION_FAILED = "failed"
    EXECUTION_TIMED_OUT = "timed_out"
    POLICY_MISMATCH = "policy_mismatch"
    PLAN_REJECTED = "plan_rejected"
    EXECUTION_PATH_REJECTED = "path_rejected"
    EXECUTION_INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class ExecutorResult:
    """Result of a shell executor call (mock or real)."""

    status: str
    exit_code: int = 0
    stdout_redacted: str = ""
    stderr_redacted: str = ""
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    timed_out: bool = False
    redaction_hits: int = 0
    duration_ms: int = 0
    error: str = ""
    resolved_argv_hash: str = ""


# ── Mock output database ──────────────────────────────────────────
# Each simulated command returns predictable mock output.

MOCK_OUTPUTS: dict[str, tuple[str, str, int]] = {
    "pwd": ("/home/aika/Projects/goaa-ai-main\n", "", 0),
    "whoami": ("aika\n", "", 0),
    "hostname": ("aika-core-01\n", "", 0),
    "date_iso": ("2026-06-15T10:30:00-07:00\n", "", 0),
    "uptime_pretty": ("up 3 days, 14 hours, 22 minutes\n", "", 0),
    "free_human": (
        "               total        used        free      shared  "
        "buff/cache   available\n"
        "Mem:            31Gi        12Gi        11Gi       1.0Gi  "
        "        8Gi        18Gi\n"
        "Swap:          8.0Gi       256Mi       7.8Gi\n",
        "",
        0,
    ),
    "git_rev_parse_head": ("a1b2c3d\n", "", 0),
    "git_rev_parse_branch": ("main\n", "", 0),
    "systemctl_is_active_active": ("active\n", "", 0),
    "systemctl_is_active_inactive": ("inactive\n", "", 0),
    "df_summary": (
        "Filesystem      Size  Used  Avail  Use%  Mounted on\n"
        "/dev/sda1       100G   45G    55G   45%  /\n",
        "",
        0,
    ),
    "git_status_short": (" M README.md\n?? new_file.txt\n", "", 0),
}


def _sha256_hex(data: List[str]) -> str:
    """Return SHA-256 hex digest of the joined argv."""
    return hashlib.sha256("".join(data).encode("utf-8")).hexdigest()


# ── Mock truncation helper ─────────────────────────────────────────


def _mock_truncate(text: str, limit: int) -> tuple[str, bool]:
    """Truncate *text* at *limit* bytes if exceeded."""
    if len(text.encode("utf-8")) > limit:
        truncated = text[:limit] + "\n-- TRUNCATED at N bytes --\n"
        return truncated, True
    return text, False


# ── Mock executor class ────────────────────────────────────────────


class MockShellExecutor:
    """
    A pure mock of the Shell Executor.

    Simulates execution by returning pre-defined mock output based on
    ``template_id``.  No real subprocess is launched.
    """

    def __init__(self, min_cwd: str = "/") -> None:
        self.min_cwd = min_cwd

    def execute_shell(
        self,
        result: ShellValidationResult,
    ) -> ExecutorResult:
        """
        Mock-execute a validated shell command.

        Flow:
          1. If ``result.status != VALID`` → POLICY_MISMATCH
          2. Verify execution plan (9 dimensions)
          3. Verify resource path (if template requires it)
          4. Simulate execution with mock output
        """
        # ── 1. Status check ────────────────────────────────────────
        if result.status != ValidationStatus.VALID:
            return ExecutorResult(
                status=ExecutorStatus.POLICY_MISMATCH,
                exit_code=-1,
                error=(
                    f"invalid status: {result.status.value} "
                    f"(expected VALID)"
                ),
            )

        # ── 2. Execution plan verification ─────────────────────────
        plan_result: PlanVerificationResult = verify_execution_plan(
            result
        )
        if not plan_result.verified:
            return ExecutorResult(
                status=ExecutorStatus.PLAN_REJECTED,
                exit_code=-1,
                error=(
                    f"plan rejected: {plan_result.reason_code} — "
                    f"{plan_result.details}"
                ),
            )

        # ── 3. Resource path verification ──────────────────────────
        resolved_cwd: str = self.min_cwd
        needs_resource: bool = result.resource_name is not None
        if needs_resource:
            try:
                resolved_path = verify_runtime_path_evidence(
                    result.resource_name, mock_mode=True
                )
                resolved_cwd = str(resolved_path)
            except Exception as e:
                return ExecutorResult(
                    status=ExecutorStatus.EXECUTION_PATH_REJECTED,
                    exit_code=-1,
                    error=f"path rejected: {e}",
                )

        # ── 4. Select mock output ──────────────────────────────────
        tid = result.template_id
        argv = result.resolved_argv
        argv_hash = _sha256_hex(argv)

        # Determine mock key based on argv content
        mock_key = tid
        if tid == "git_rev_parse":
            if "--short" in argv:
                mock_key = "git_rev_parse_head"
            else:
                mock_key = "git_rev_parse_branch"
        elif tid == "systemctl_is_active":
            mock_key = "systemctl_is_active_active"

        mock_stdout, mock_stderr, mock_exit = MOCK_OUTPUTS.get(
            mock_key, ("", "", -1)
        )

        # ── 5. Apply limits (mock truncation) ──────────────────────
        timeout_s = result.timeout_seconds
        stdout_limit = result.stdout_limit_bytes
        stderr_limit = result.stderr_limit_bytes

        stdout_safe, stdout_trunc = _mock_truncate(
            mock_stdout, stdout_limit
        )
        stderr_safe, stderr_trunc = _mock_truncate(
            mock_stderr, stderr_limit
        )

        stdout_bytes = len(mock_stdout.encode("utf-8"))
        stderr_bytes = len(mock_stderr.encode("utf-8"))

        # Simulate redaction
        redacted_stdout = stdout_safe
        redacted_stderr = stderr_safe

        return ExecutorResult(
            status=ExecutorStatus.SUCCESS,
            exit_code=mock_exit,
            stdout_redacted=redacted_stdout,
            stderr_redacted=redacted_stderr,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            stdout_truncated=stdout_trunc,
            stderr_truncated=stderr_trunc,
            timed_out=False,
            redaction_hits=0,
            duration_ms=42,  # fixed mock duration
            error="",
            resolved_argv_hash=argv_hash,
        )
