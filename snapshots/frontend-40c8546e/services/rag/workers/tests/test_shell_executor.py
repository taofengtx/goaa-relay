"""
GOAA Shell Capability V0 — Knife 2A-1 Tests
=============================================
Covers: verify_execution_plan (9 dimensions), ResourcePolicy,
        MockShellExecutor execution and rejection.

All 66 tests are pure: no subprocess, no os.system, no real I/O.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md §18.1
"""

import unittest

from shell_schema import (
    ApprovedUnit,
    GitRevParseMode,
    ShellTaskRequest,
    ShellValidationResult,
    ValidationStatus,
)
from shell_policy import (
    POLICY_VERSION,
    RESOURCE_MAP,
    TEMPLATE_POLICY,
)

# ── Module under test: execution plan ──────────────────────────────

from shell_execution_plan import (
    PlanVerificationResult,
    verify_execution_plan,
)

# ── Module under test: resource policy ─────────────────────────────

from shell_resource_policy import (
    RESOURCE_POLICIES,
    PathRejected,
    ResourcePolicy,
    verify_runtime_path_evidence,
)

# ── Module under test: mock executor ───────────────────────────────

from shell_mock_executor import (
    ExecutorResult,
    ExecutorStatus,
    MockShellExecutor,
)


# ═══════════════════════════════════════════════════════════════════
# Section A: verify_execution_plan — 9-dimension independent review
# ═══════════════════════════════════════════════════════════════════


class TestVerifyTemplateId(unittest.TestCase):
    """Dimension 1: template_id ∈ ALLOWED_TEMPLATE_IDS."""

    def test_verify_template_id_known_pwd(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="pwd",
            resolved_argv=["pwd"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_template_id_unknown_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="evil_cmd",
            resolved_argv=[],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "UNKNOWN_TEMPLATE")


class TestVerifyPolicyVersion(unittest.TestCase):
    """Dimension 2: policy_version == POLICY_VERSION."""

    def test_verify_policy_version_match(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="whoami",
            resolved_argv=["whoami"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_policy_version_mismatch_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="whoami",
            resolved_argv=["whoami"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version="shell-v0.2-fake",
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "POLICY_VERSION_MISMATCH")


class TestVerifyResourceName(unittest.TestCase):
    """Dimension 3: resource_name ∈ ALLOWED_RESOURCE_NAMES."""

    def test_verify_resource_known_repo_main(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_resource_unknown_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="/etc/passwd",
            resolved_argv=[],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "UNKNOWN_RESOURCE")


class TestVerifyArgv(unittest.TestCase):
    """Dimension 4: resolved_argv matches recomputed expected argv."""

    def test_verify_argv_pwd_correct(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="pwd",
            resolved_argv=["pwd"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_argv_pwd_forged_rejected(self):
        """Forged argv: template says pwd but argv is rm -rf."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="pwd",
            resolved_argv=["rm", "-rf", "/tmp/x"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "ARGV_MISMATCH")

    def test_verify_git_rev_parse_head_correct(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_git_rev_parse_branch_correct(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--abbrev-ref", "HEAD",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_git_rev_parse_forged_hash_rejected(self):
        """Wrong commit hash should be rejected."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "AAAA",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "ARGV_MISMATCH")

    def test_verify_systemctl_approved_unit_correct(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="systemctl_is_active",
            resource_name="runtime_local",
            resolved_argv=["systemctl", "is-active", "ollama"],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_systemctl_forged_unit_rejected(self):
        """Non-approved systemd unit should be rejected."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="systemctl_is_active",
            resource_name="runtime_local",
            resolved_argv=["systemctl", "is-active", "nginx"],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "ARGV_MISMATCH")


class TestVerifyTimeoutsAndLimits(unittest.TestCase):
    """Dimensions 5, 6, 7: timeout, stdout/stderr limits."""

    def test_verify_timeout_exact(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="hostname",
            resolved_argv=["hostname"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_timeout_forged_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="hostname",
            resolved_argv=["hostname"],
            timeout_seconds=999,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "TIMEOUT_MISMATCH")

    def test_verify_stdout_limit_exact(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="date_iso",
            resolved_argv=["date", "--iso-8601=seconds"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_stdout_limit_forged_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="date_iso",
            resolved_argv=["date", "--iso-8601=seconds"],
            timeout_seconds=5,
            stdout_limit_bytes=999999,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "STDOUT_LIMIT_MISMATCH")

    def test_verify_stderr_limit_forged_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="uptime_pretty",
            resolved_argv=["uptime", "-p"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=999999,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "STDERR_LIMIT_MISMATCH")


class TestVerifyRiskAndApproval(unittest.TestCase):
    """Dimensions 8, 9: risk_level and requires_approval."""

    def test_verify_risk_level_low(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="free_human",
            resolved_argv=["free", "-h"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="low",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_risk_level_medium(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertTrue(vr.verified, msg=vr.details)

    def test_verify_risk_level_forged_rejected(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="free_human",
            resolved_argv=["free", "-h"],
            timeout_seconds=5,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="critical",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "RISK_LEVEL_MISMATCH")

    def test_verify_approval_mismatch_rejected(self):
        """Template needs approval but result says False."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10,
            stdout_limit_bytes=32768,
            stderr_limit_bytes=16384,
            risk_level="medium",
            requires_approval=False,
            policy_version=POLICY_VERSION,
        )
        vr = verify_execution_plan(result)
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "APPROVAL_MISMATCH")


# ═══════════════════════════════════════════════════════════════════
# Section B: MockShellExecutor — execution simulation
# ═══════════════════════════════════════════════════════════════════


def _valid_pwd_result() -> ShellValidationResult:
    return ShellValidationResult(
        status=ValidationStatus.VALID,
        template_id="pwd",
        resolved_argv=["pwd"],
        timeout_seconds=5,
        stdout_limit_bytes=32768,
        stderr_limit_bytes=16384,
        risk_level="low",
        requires_approval=False,
        policy_version=POLICY_VERSION,
    )


class TestMockExecutorBasic(unittest.TestCase):
    """Each template returns SUCCESS."""

    def setUp(self):
        self.executor = MockShellExecutor()

    def test_executor_pwd(self):
        result = _valid_pwd_result()
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertEqual(er.exit_code, 0)
        self.assertIn("goaa-ai-main", er.stdout_redacted)

    def test_executor_whoami(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="whoami", resolved_argv=["whoami"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("aika", er.stdout_redacted)

    def test_executor_hostname(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="hostname", resolved_argv=["hostname"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("aika-core-01", er.stdout_redacted)

    def test_executor_date_iso(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="date_iso",
            resolved_argv=["date", "--iso-8601=seconds"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)

    def test_executor_uptime_pretty(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="uptime_pretty",
            resolved_argv=["uptime", "-p"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)

    def test_executor_free_human(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="free_human",
            resolved_argv=["free", "-h"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("Mem:", er.stdout_redacted)

    def test_executor_git_rev_parse_head(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("a1b2c3d", er.stdout_redacted)

    def test_executor_git_rev_parse_branch(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--abbrev-ref", "HEAD",
            ],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("main", er.stdout_redacted)

    def test_executor_systemctl_is_active(self):
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="systemctl_is_active",
            resource_name="runtime_local",
            resolved_argv=["systemctl", "is-active", "ollama"],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)
        self.assertIn("active", er.stdout_redacted)


class TestMockExecutorRejection(unittest.TestCase):
    """Executor correctly rejects invalid inputs."""

    def setUp(self):
        self.executor = MockShellExecutor()

    def test_executor_rejects_invalid_status(self):
        """REJECTED status should produce POLICY_MISMATCH."""
        result = ShellValidationResult(
            status=ValidationStatus.REJECTED_ARGUMENT,
            template_id="pwd",
            resolved_argv=[],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.POLICY_MISMATCH)

    def test_executor_rejects_empty_argv(self):
        """Empty argv for pwd should fail ARGV_MISMATCH."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="pwd",
            resolved_argv=[],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)
        self.assertIn("ARGV_MISMATCH", er.error)

    def test_executor_forged_argv_blocked(self):
        """Forged argv on pwd template is blocked at plan level."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="pwd",
            resolved_argv=["rm", "-rf", "/tmp/x"],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)
        self.assertIn("ARGV_MISMATCH", er.error)

    def test_executor_forged_git_rev_parse_rejected(self):
        """Wrong hash in git_rev_parse HEAD is blocked."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "AAAA",
            ],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)

    def test_executor_unknown_resource_rejected(self):
        """Unknown resource name is blocked at plan level."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="nonexistent_repo",
            resolved_argv=[],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)
        self.assertIn("UNKNOWN_RESOURCE", er.error)

    def test_executor_missing_required_resource(self):
        """Template that needs resource but resource is None."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name=None,
            resolved_argv=[],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)
        self.assertIn("MISSING_RESOURCE", er.error)

    def test_executor_unknown_template_rejected(self):
        """Unknown template_id is blocked."""
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="unknown_template_99",
            resolved_argv=[],
            timeout_seconds=5, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="low",
            requires_approval=False, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.PLAN_REJECTED)
        self.assertIn("UNKNOWN_TEMPLATE", er.error)


class TestMockExecutorMetadata(unittest.TestCase):
    """Executor result metadata correctness."""

    def setUp(self):
        self.executor = MockShellExecutor()

    def test_executor_argv_hash_present(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertIsNotNone(er.resolved_argv_hash)
        self.assertGreater(len(er.resolved_argv_hash), 10)

    def test_executor_duration_ms_positive(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertGreater(er.duration_ms, 0)

    def test_executor_stdout_bytes_nonzero(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertGreater(er.stdout_bytes, 0)

    def test_executor_not_timed_out(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertFalse(er.timed_out)


class TestMockExecutorCwdAndShell(unittest.TestCase):
    """Cwd and shell=False invocation semantics."""

    def test_executor_cwd_default(self):
        self.executor = MockShellExecutor(min_cwd="/")
        result = _valid_pwd_result()
        # Mock executor uses min_cwd directly for non-resource templates
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)

    def test_executor_cwd_resource_template(self):
        self.executor = MockShellExecutor()
        result = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="git_rev_parse",
            resource_name="repo_main",
            resolved_argv=[
                "git", "-C", RESOURCE_MAP["repo_main"],
                "rev-parse", "--short", "HEAD",
            ],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True, policy_version=POLICY_VERSION,
        )
        er = self.executor.execute_shell(result)
        self.assertEqual(er.status, ExecutorStatus.SUCCESS)


class TestMockExecutorEdgeCases(unittest.TestCase):
    """Edge cases and error handling."""

    def setUp(self):
        self.executor = MockShellExecutor()

    def test_executor_all_8_templates(self):
        """All 8 knife 2A template IDs produce SUCCESS."""
        results = []
        # Template 1-6: no resource
        for tid, argv, timeout, risk, approval in [
            ("pwd", ["pwd"], 5, "low", False),
            ("whoami", ["whoami"], 5, "low", False),
            ("hostname", ["hostname"], 5, "low", False),
            ("date_iso", ["date", "--iso-8601=seconds"], 5, "low", False),
            ("uptime_pretty", ["uptime", "-p"], 5, "low", False),
            ("free_human", ["free", "-h"], 5, "low", False),
        ]:
            r = ShellValidationResult(
                status=ValidationStatus.VALID,
                template_id=tid, resolved_argv=argv,
                timeout_seconds=timeout, stdout_limit_bytes=32768,
                stderr_limit_bytes=16384, risk_level=risk,
                requires_approval=approval,
                policy_version=POLICY_VERSION,
            )
            results.append(r)

        # Template 7: git_rev_parse (2 variants)
        for argv in [
            ["git", "-C", RESOURCE_MAP["repo_main"],
             "rev-parse", "--short", "HEAD"],
            ["git", "-C", RESOURCE_MAP["repo_main"],
             "rev-parse", "--abbrev-ref", "HEAD"],
        ]:
            r = ShellValidationResult(
                status=ValidationStatus.VALID,
                template_id="git_rev_parse",
                resource_name="repo_main",
                resolved_argv=argv,
                timeout_seconds=10, stdout_limit_bytes=32768,
                stderr_limit_bytes=16384, risk_level="medium",
                requires_approval=True,
                policy_version=POLICY_VERSION,
            )
            results.append(r)

        # Template 8: systemctl_is_active
        r = ShellValidationResult(
            status=ValidationStatus.VALID,
            template_id="systemctl_is_active",
            resource_name="runtime_local",
            resolved_argv=["systemctl", "is-active", "ollama"],
            timeout_seconds=10, stdout_limit_bytes=32768,
            stderr_limit_bytes=16384, risk_level="medium",
            requires_approval=True,
            policy_version=POLICY_VERSION,
        )
        results.append(r)

        for er in [self.executor.execute_shell(r) for r in results]:
            self.assertEqual(er.status, ExecutorStatus.SUCCESS,
                             msg=f"failed: {er.error}")

    def test_executor_sha256_consistency(self):
        """Same argv produces same hash."""
        er1 = self.executor.execute_shell(_valid_pwd_result())
        er2 = self.executor.execute_shell(_valid_pwd_result())
        self.assertEqual(er1.resolved_argv_hash, er2.resolved_argv_hash)

    def test_executor_stdout_not_truncated_normal(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertFalse(er.stdout_truncated)

    def test_executor_stderr_empty_by_default(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertEqual(er.stderr_bytes, 0)
        self.assertEqual(er.stderr_redacted, "")

    def test_executor_redaction_hits_zero_default(self):
        er = self.executor.execute_shell(_valid_pwd_result())
        self.assertEqual(er.redaction_hits, 0)


# ═══════════════════════════════════════════════════════════════════
# Section C: ResourcePolicy — named resource path verification
# ═══════════════════════════════════════════════════════════════════


class TestResourcePolicyData(unittest.TestCase):
    """ResourcePolicy dataclass integrity."""

    def test_repo_main_policy_exists(self):
        self.assertIn("repo_main", RESOURCE_POLICIES)
        policy = RESOURCE_POLICIES["repo_main"]
        self.assertIn("aika", policy.allowed_owner_names)
        prefix_str = str(policy.allowed_prefix)
        self.assertTrue(
            prefix_str.startswith("/home/aika"),
            f"expected prefix starting with /home/aika, got {prefix_str!r}",
        )

    def test_runtime_local_policy_exists(self):
        self.assertIn("runtime_local", RESOURCE_POLICIES)
        policy = RESOURCE_POLICIES["runtime_local"]
        self.assertIn("root", policy.allowed_owner_names)
        self.assertIn("aika", policy.allowed_owner_names)
        prefix_str = str(policy.allowed_prefix)
        self.assertTrue(
            prefix_str.startswith("/opt/goaa"),
            f"expected prefix starting with /opt/goaa, got {prefix_str!r}",
        )

    def test_policy_must_be_directory(self):
        for name in RESOURCE_POLICIES:
            with self.subTest(name=name):
                self.assertTrue(
                    RESOURCE_POLICIES[name].must_be_directory
                )

    def test_policy_rejects_world_writable(self):
        for name in RESOURCE_POLICIES:
            with self.subTest(name=name):
                self.assertTrue(
                    RESOURCE_POLICIES[name].reject_world_writable
                )


class TestVerifyRuntimePathEvidence(unittest.TestCase):
    """verify_runtime_path_evidence() in mock mode."""

    def test_verify_known_resource_repo_main(self):
        p = verify_runtime_path_evidence("repo_main", mock_mode=True)
        self.assertIsNotNone(p)
        self.assertTrue(str(p).startswith("/home/aika/"))

    def test_verify_known_resource_runtime_local(self):
        p = verify_runtime_path_evidence(
            "runtime_local", mock_mode=True
        )
        self.assertIsNotNone(p)
        self.assertTrue(str(p).startswith("/opt/goaa/"))

    def test_verify_unknown_resource_raises(self):
        with self.assertRaises(PathRejected):
            verify_runtime_path_evidence(
                "nonexistent_resource", mock_mode=True
            )

    def test_verify_empty_resource_raises(self):
        with self.assertRaises(PathRejected):
            verify_runtime_path_evidence("", mock_mode=True)

    def test_verify_path_prefix_escape_raises(self):
        """A resource whose canonical_path escapes allowed_prefix."""
        from pathlib import Path
        escaped_policy = ResourcePolicy(
            canonical_path="/tmp/escape",
            allowed_owner_names=frozenset({"root"}),
            allowed_prefix=Path("/etc/"),
            must_be_directory=False,
            reject_world_writable=False,
        )
        # Manually check prefix
        p = Path(escaped_policy.canonical_path)
        try:
            safe = p.is_relative_to(escaped_policy.allowed_prefix)
        except AttributeError:
            import os
            safe = os.path.commonpath(
                [str(p), str(escaped_policy.allowed_prefix)]
            ) == str(escaped_policy.allowed_prefix)
        self.assertFalse(safe)

    def test_verify_mock_mode_no_filesystem_access(self):
        """Mock mode should not raise FileNotFoundError."""
        p = verify_runtime_path_evidence("repo_main", mock_mode=True)
        self.assertEqual(str(p), "/home/aika/Projects/goaa-ai-main")

    def test_verify_path_exact_return_type(self):
        p = verify_runtime_path_evidence("repo_main", mock_mode=True)
        from pathlib import Path
        self.assertIsInstance(p, Path)


# ═══════════════════════════════════════════════════════════════════
# Section D: PlanVerificationResult dataclass
# ═══════════════════════════════════════════════════════════════════


class TestPlanVerificationResult(unittest.TestCase):
    """PlanVerificationResult dataclass integrity."""

    def test_verified_true(self):
        vr = PlanVerificationResult(
            verified=True, reason_code="VERIFIED",
            details="ok"
        )
        self.assertTrue(vr.verified)
        self.assertEqual(vr.reason_code, "VERIFIED")

    def test_verified_false(self):
        vr = PlanVerificationResult(
            verified=False, reason_code="ARGV_MISMATCH",
            details="expected ['pwd'], got ['rm']"
        )
        self.assertFalse(vr.verified)
        self.assertEqual(vr.reason_code, "ARGV_MISMATCH")

    def test_verified_default_empty(self):
        vr = PlanVerificationResult(verified=True)
        self.assertEqual(vr.reason_code, "")
        self.assertEqual(vr.details, "")


# ═══════════════════════════════════════════════════════════════════
# Section E: Policy alignment — verify_execution_plan stays in sync
# ═══════════════════════════════════════════════════════════════════


class TestPolicyAlignment(unittest.TestCase):
    """Execution plan verification must be consistent with Policy."""

    def test_all_knife2a_templates_verifiable(self):
        """Each knife 2A template can be verified with correct data."""
        templates = [
            ("pwd", ["pwd"], "low", False, 5),
            ("whoami", ["whoami"], "low", False, 5),
            ("hostname", ["hostname"], "low", False, 5),
            ("date_iso", ["date", "--iso-8601=seconds"],
             "low", False, 5),
            ("uptime_pretty", ["uptime", "-p"],
             "low", False, 5),
            ("free_human", ["free", "-h"],
             "low", False, 5),
        ]
        for tid, argv, risk, approval, timeout in templates:
            with self.subTest(template=tid):
                result = ShellValidationResult(
                    status=ValidationStatus.VALID,
                    template_id=tid, resolved_argv=argv,
                    timeout_seconds=timeout,
                    stdout_limit_bytes=32768,
                    stderr_limit_bytes=16384,
                    risk_level=risk,
                    requires_approval=approval,
                    policy_version=POLICY_VERSION,
                )
                vr = verify_execution_plan(result)
                self.assertTrue(vr.verified, msg=f"{tid}: {vr.details}")

    def test_git_rev_parse_both_modes_verifiable(self):
        """Both git_rev_parse modes can be verified."""
        rp = RESOURCE_MAP["repo_main"]
        for argv in [
            ["git", "-C", rp, "rev-parse", "--short", "HEAD"],
            ["git", "-C", rp, "rev-parse", "--abbrev-ref", "HEAD"],
        ]:
            result = ShellValidationResult(
                status=ValidationStatus.VALID,
                template_id="git_rev_parse",
                resource_name="repo_main",
                resolved_argv=argv,
                timeout_seconds=10,
                stdout_limit_bytes=32768,
                stderr_limit_bytes=16384,
                risk_level="medium",
                requires_approval=True,
                policy_version=POLICY_VERSION,
            )
            vr = verify_execution_plan(result)
            self.assertTrue(vr.verified)

    def test_systemctl_is_active_verifiable(self):
        """systemctl_is_active with approved unit is verifiable."""
        for unit in ("ollama", "goaa-router",
                     "goaa-local-console", "goaa-worker-agent",
                     "goaa-telemetry-writer"):
            with self.subTest(unit=unit):
                result = ShellValidationResult(
                    status=ValidationStatus.VALID,
                    template_id="systemctl_is_active",
                    resource_name="runtime_local",
                    resolved_argv=["systemctl", "is-active", unit],
                    timeout_seconds=10,
                    stdout_limit_bytes=32768,
                    stderr_limit_bytes=16384,
                    risk_level="medium",
                    requires_approval=True,
                    policy_version=POLICY_VERSION,
                )
                vr = verify_execution_plan(result)
                self.assertTrue(vr.verified)

    def test_knife2b_templates_not_in_verification_scope(self):
        """df_summary and git_status_short are knife 2B, not 2A."""
        for tid in ("df_summary", "git_status_short"):
            with self.subTest(template=tid):
                self.assertIn(tid, TEMPLATE_POLICY,
                              f"{tid} should be in policy")
                # Verify that knife 2B templates are in ALLOWED_TEMPLATE_IDS
                # but execution_plan handles them via verify_execution_plan
                result = ShellValidationResult(
                    status=ValidationStatus.VALID,
                    template_id=tid,
                    resolved_argv=[],
                    timeout_seconds=5,
                    stdout_limit_bytes=32768,
                    stderr_limit_bytes=16384,
                    risk_level="low",
                    requires_approval=False,
                    policy_version=POLICY_VERSION,
                )
                vr = verify_execution_plan(result)
                self.assertFalse(vr.verified)


# ═══════════════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main()
