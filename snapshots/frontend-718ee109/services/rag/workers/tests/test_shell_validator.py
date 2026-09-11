"""
GOAA Shell Capability V0 — Validator unit tests (刀 1)
=======================================================
Covers: schema validation, template resolution, resource validation,
option validation via explicit typed fields, block-token scanning,
success cases.

All tests are pure: no subprocess, no I/O, no filesystem access.
"""

import unittest

from shell_schema import (
    ApprovedUnit,
    GitRevParseMode,
    ShellTaskRequest,
    ShellValidationResult,
    ValidationStatus,
)
from shell_validator import validate_request


class TestSchemaRejection(unittest.TestCase):
    """ShellTaskRequest schema-level validation."""

    def test_empty_task_id_rejected(self):
        req = ShellTaskRequest(task_id="", template_id="pwd")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "EMPTY_TASK_ID")

    def test_blank_task_id_rejected(self):
        req = ShellTaskRequest(task_id="   ", template_id="pwd")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "EMPTY_TASK_ID")

    def test_empty_template_id_rejected(self):
        req = ShellTaskRequest(task_id="t1", template_id="")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "EMPTY_TEMPLATE_ID")

    def test_blank_template_id_rejected(self):
        req = ShellTaskRequest(task_id="t1", template_id="   ")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)

    def test_raw_command_in_metadata_rejected(self):
        """Simulate future misuse: raw_command passed via metadata."""
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"raw_command": "rm -rf /"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_argv_in_metadata_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"argv": "date --iso"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_cwd_in_metadata_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"cwd": "/tmp"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_env_in_metadata_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"env": "PATH=/evil"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_option_in_metadata_rejected(self):
        """metadata['option'] must NOT control git_rev_parse argv."""
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=GitRevParseMode.HEAD_SHORT,
            metadata={"option": "HEAD_SHORT"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_unit_in_metadata_rejected(self):
        """metadata['unit'] must NOT control systemctl argv."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=ApprovedUnit.GOAA_ROUTER,
            metadata={"unit": "goaa-router"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_git_mode_in_metadata_rejected(self):
        """metadata['git_mode'] is reserved."""
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"git_mode": "HEAD_SHORT"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_command_in_metadata_rejected(self):
        """metadata['command'] is reserved."""
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"command": "whoami"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")


class TestTemplateRejection(unittest.TestCase):
    """Template validation."""

    def test_unknown_template_id_rejected(self):
        req = ShellTaskRequest(task_id="t1", template_id="rm_rf")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_TEMPLATE)
        self.assertEqual(result.reason_code, "UNKNOWN_TEMPLATE")

    def test_case_disguise_rejected(self):
        req = ShellTaskRequest(task_id="t1", template_id="PWD")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_TEMPLATE)

    def test_mixed_case_disguise_rejected(self):
        req = ShellTaskRequest(task_id="t1", template_id="PwD")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_TEMPLATE)

    def test_trailing_whitespace_normalized(self):
        """Leading/trailing whitespace on template_id is stripped."""
        req = ShellTaskRequest(task_id="t1", template_id="  pwd  ")
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_unknown_resource_disguised_as_template(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            resource_name="repo_main",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)


class TestResourceRejection(unittest.TestCase):
    """Resource validation."""

    def test_missing_resource_for_git_status_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_status_short",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_RESOURCE)
        self.assertEqual(result.reason_code, "MISSING_RESOURCE")

    def test_unknown_resource_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_status_short",
            resource_name="production",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_RESOURCE)
        self.assertEqual(result.reason_code, "UNKNOWN_RESOURCE")

    def test_absolute_path_as_resource_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_status_short",
            resource_name="/home/aika/secret",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_RESOURCE)

    def test_path_traversal_as_resource_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_status_short",
            resource_name="../etc",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_RESOURCE)

    def test_tilde_path_as_resource_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_status_short",
            resource_name="~/Projects",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_RESOURCE)
        self.assertEqual(result.reason_code, "UNKNOWN_RESOURCE")


class TestGitOptionRejection(unittest.TestCase):
    """Git rev-parse mode validation via explicit git_mode field."""

    def test_missing_git_mode_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "MISSING_GIT_MODE")

    def test_git_mode_with_unit_name_rejected(self):
        """Mutual exclusion: git_rev_parse must not have unit_name."""
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=GitRevParseMode.HEAD_SHORT,
            unit_name=ApprovedUnit.OLLAMA,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "UNEXPECTED_UNIT_NAME")


class TestSystemctlUnitRejection(unittest.TestCase):
    """systemctl unit validation via explicit unit_name field."""

    def test_missing_unit_name_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "MISSING_UNIT_NAME")

    def test_unit_name_with_git_mode_rejected(self):
        """Mutual exclusion: systemctl must not have git_mode."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=ApprovedUnit.OLLAMA,
            git_mode=GitRevParseMode.HEAD_SHORT,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "UNEXPECTED_GIT_MODE")

    def test_unknown_unit_rejected(self):
        """String unit_name must be rejected (not silently converted)."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name="unknown-unit",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "INVALID_UNIT_NAME_TYPE")

    def test_unit_start_rejected(self):
        """String 'start' as unit_name must be rejected."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name="start",
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "INVALID_UNIT_NAME_TYPE")


class TestSimpleTemplateFieldRejection(unittest.TestCase):
    """Simple templates must not carry git_mode or unit_name."""

    def test_pwd_with_git_mode_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            git_mode=GitRevParseMode.HEAD_SHORT,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "UNEXPECTED_GIT_MODE")

    def test_pwd_with_unit_name_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            unit_name=ApprovedUnit.OLLAMA,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "UNEXPECTED_UNIT_NAME")

    def test_whoami_with_git_mode_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="whoami",
            git_mode=GitRevParseMode.HEAD_SHORT,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)

    def test_date_iso_with_unit_name_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="date_iso",
            unit_name=ApprovedUnit.OLLAMA,
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)

    def test_all_simple_templates_reject_git_mode(self):
        for tid in ("pwd", "whoami", "hostname", "date_iso",
                     "uptime_pretty", "df_summary", "free_human"):
            req = ShellTaskRequest(
                task_id="t1", template_id=tid,
                git_mode=GitRevParseMode.HEAD_SHORT,
            )
            result = validate_request(req)
            self.assertEqual(
                result.status, ValidationStatus.REJECTED_ARGUMENT,
                f"{tid} should reject git_mode",
            )

    def test_all_simple_templates_reject_unit_name(self):
        for tid in ("pwd", "whoami", "hostname", "date_iso",
                     "uptime_pretty", "df_summary", "free_human"):
            req = ShellTaskRequest(
                task_id="t1", template_id=tid,
                unit_name=ApprovedUnit.OLLAMA,
            )
            result = validate_request(req)
            self.assertEqual(
                result.status, ValidationStatus.REJECTED_ARGUMENT,
                f"{tid} should reject unit_name",
            )


class TestShellInjectionRejection(unittest.TestCase):
    """Block-token scanning in request fields."""

    def _assert_rejected_policy(self, req: ShellTaskRequest):
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_POLICY,
                         f"Expected REJECTED_POLICY, got {result.status} "
                         f"({result.reason_code}: {result.reason})")

    def test_command_semicolon_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd;whoami"))

    def test_command_pipe_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="hostname|id"))

    def test_double_ampersand_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="date && id"))

    def test_dollar_substitution_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="$(whoami)"))

    def test_backtick_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="`whoami`"))

    def test_newline_double_command_injection(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1\necho 'evil'", template_id="pwd"))

    def test_env_var_expansion_in_task_id(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1 $HOME", template_id="pwd"))

    def test_env_var_expansion_in_template_id(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd $PATH"))


class TestBlockedCommandsInRequest(unittest.TestCase):
    """Blocked command detection in string fields."""

    def _assert_rejected_policy(self, req: ShellTaskRequest):
        result = validate_request(req)
        self.assertEqual(
            result.status, ValidationStatus.REJECTED_POLICY,
            f"Expected REJECTED_POLICY, got {result.status} "
            f"(code={result.reason_code}, reason={result.reason})",
        )

    def test_bash_c_in_requested_by(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             requested_by="bash -c 'evil'"))

    def test_sh_c_in_requested_by(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             requested_by="sh -c 'evil'"))

    def test_sudo_in_approval_id(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             approval_id="sudo rm -rf"))

    def test_curl_in_approval_id(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             approval_id="curl http://evil.com"))

    def test_wget_in_resource_name(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="git_status_short",
                             resource_name="wget"))

    def test_ssh_in_approval_id(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             approval_id="ssh root@evil"))

    def test_python_c_in_requested_by(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             requested_by="python -c 'import os'"))

    def test_node_e_in_requested_by(self):
        self._assert_rejected_policy(
            ShellTaskRequest(task_id="t1", template_id="pwd",
                             requested_by="node -e 'console.log(1)'"))


class TestSuccessCases(unittest.TestCase):
    """All 10 templates must produce VALID results."""

    def _assert_valid(self, req: ShellTaskRequest) -> ShellValidationResult:
        result = validate_request(req)
        self.assertEqual(
            result.status, ValidationStatus.VALID,
            f"Expected VALID for {req.template_id!r}, got "
            f"{result.status} ({result.reason_code}: {result.reason})",
        )
        return result

    def test_pwd_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="pwd"))
        self.assertEqual(r.resolved_argv, ["pwd"])
        self.assertEqual(r.risk_level, "low")
        self.assertFalse(r.requires_approval)
        self.assertEqual(r.policy_version, "shell-v0.1-knife1")

    def test_whoami_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="whoami"))
        self.assertEqual(r.resolved_argv, ["whoami"])

    def test_hostname_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="hostname"))
        self.assertEqual(r.resolved_argv, ["hostname"])

    def test_date_iso_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="date_iso"))
        self.assertEqual(r.resolved_argv,
                         ["date", "--iso-8601=seconds"])

    def test_uptime_pretty_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="uptime_pretty"))
        self.assertEqual(r.resolved_argv, ["uptime", "-p"])

    def test_df_summary_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="df_summary"))
        self.assertEqual(r.resolved_argv,
                         ["df", "-h",
                          "--output=source,size,used,avail,pcent,target"])

    def test_free_human_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(task_id="t1", template_id="free_human"))
        self.assertEqual(r.resolved_argv, ["free", "-h"])

    def test_git_status_short_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(
                task_id="t1", template_id="git_status_short",
                resource_name="repo_main"))
        self.assertEqual(
            r.resolved_argv,
            ["git", "-C", "/home/aika/Projects/goaa-ai-main",
             "status", "--short"],
        )
        self.assertEqual(r.risk_level, "medium")
        self.assertTrue(r.requires_approval)

    def test_git_rev_parse_head_short_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode=GitRevParseMode.HEAD_SHORT))
        self.assertEqual(
            r.resolved_argv,
            ["git", "-C", "/home/aika/Projects/goaa-ai-main",
             "rev-parse", "--short", "HEAD"],
        )

    def test_git_rev_parse_branch_name_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="runtime_local",
                git_mode=GitRevParseMode.BRANCH_NAME))
        self.assertEqual(
            r.resolved_argv,
            ["git", "-C", "/opt/goaa/repo",
             "rev-parse", "--abbrev-ref", "HEAD"],
        )

    def test_systemctl_is_active_valid(self):
        r = self._assert_valid(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name=ApprovedUnit.OLLAMA))
        self.assertEqual(r.resolved_argv,
                         ["systemctl", "is-active", "ollama"])

    def test_systemctl_is_active_all_approved_units(self):
        for unit in ApprovedUnit:
            r = self._assert_valid(
                ShellTaskRequest(
                    task_id="t1", template_id="systemctl_is_active",
                    resource_name="runtime_local",
                    unit_name=unit))
            self.assertEqual(
                r.resolved_argv,
                ["systemctl", "is-active", unit.value],
            )

    def test_all_templates_fully_populated_metadata(self):
        """Every valid result must carry all policy metadata fields."""
        cases = [
            ("pwd", {}),
            ("whoami", {}),
            ("hostname", {}),
            ("date_iso", {}),
            ("uptime_pretty", {}),
            ("df_summary", {}),
            ("free_human", {}),
            ("git_status_short", {"resource_name": "repo_main"}),
            ("git_rev_parse", {"resource_name": "repo_main",
                               "git_mode": GitRevParseMode.HEAD_SHORT}),
            ("systemctl_is_active", {"resource_name": "runtime_local",
                                      "unit_name": ApprovedUnit.OLLAMA}),
        ]
        for tid, extra in cases:
            req = ShellTaskRequest(task_id="t1", template_id=tid, **extra)
            r = self._assert_valid(req)
            self.assertIsNotNone(r.resolved_argv)
            self.assertGreater(len(r.resolved_argv), 0)
            self.assertGreater(r.timeout_seconds, 0)
            self.assertGreater(r.stdout_limit_bytes, 0)
            self.assertGreater(r.stderr_limit_bytes, 0)
            self.assertIn(r.risk_level, ("low", "medium"))
            self.assertEqual(r.policy_version, "shell-v0.1-knife1")


class TestMetadataAuditOnly(unittest.TestCase):
    """metadata must not control argv; it must only carry audit labels."""

    def test_innocent_metadata_allowed(self):
        """Audit labels in metadata must not be rejected."""
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"request_reason": "debug_session",
                      "ticket": "TICKET-123"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_metadata_with_reserved_option_key_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"option": "something"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_metadata_with_reserved_mode_key_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"mode": "admin"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)

    def test_metadata_with_reserved_argv_key_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"argv": "-rf /"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_metadata_with_reserved_command_key_rejected(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="pwd",
            metadata={"command": "whoami"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)

    def test_git_rev_parse_option_in_metadata_not_controlling_argv(self):
        """Even if metadata['option'] is set, git_mode controls argv."""
        # This request will fail because option is a reserved key,
        # not because of the git_mode.
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=GitRevParseMode.HEAD_SHORT,
            metadata={"option": "HEAD_SHORT"},
        )
        result = validate_request(req)
        # Reserved key check happens before template-specific check
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")

    def test_systemctl_unit_in_metadata_not_controlling_argv(self):
        """Even if metadata['unit'] is set, unit_name controls argv."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=ApprovedUnit.OLLAMA,
            metadata={"unit": "goaa-router"},
        )
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "RESERVED_METADATA_KEY")


class TestGitModeTypeGuard(unittest.TestCase):
    """Runtime type checks: git_mode must be GitRevParseMode."""

    def _assert_type_rejected(self, req: ShellTaskRequest):
        result = validate_request(req)
        self.assertEqual(
            result.status, ValidationStatus.REJECTED_ARGUMENT,
            f"Expected REJECTED_ARGUMENT, got {result.status} "
            f"(code={result.reason_code}, reason={result.reason})",
        )
        self.assertEqual(result.reason_code, "INVALID_GIT_MODE_TYPE")

    def test_string_head_short_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode="HEAD_SHORT"))

    def test_string_branch_name_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode="BRANCH_NAME"))

    def test_integer_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode=123))

    def test_list_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode=["HEAD_SHORT"]))

    def test_dict_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode={"value": "HEAD_SHORT"}))

    def test_enum_head_short_valid(self):
        """Explicit enum values must still pass type guard."""
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=GitRevParseMode.HEAD_SHORT)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_enum_branch_name_valid(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=GitRevParseMode.BRANCH_NAME)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_none_not_rejected(self):
        """None is accepted (but subsequent checks may reject)."""
        req = ShellTaskRequest(
            task_id="t1", template_id="git_rev_parse",
            resource_name="repo_main",
            git_mode=None)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "MISSING_GIT_MODE")


class TestUnitNameTypeGuard(unittest.TestCase):
    """Runtime type checks: unit_name must be ApprovedUnit."""

    def _assert_type_rejected(self, req: ShellTaskRequest):
        result = validate_request(req)
        self.assertEqual(
            result.status, ValidationStatus.REJECTED_ARGUMENT,
            f"Expected REJECTED_ARGUMENT, got {result.status} "
            f"(code={result.reason_code}, reason={result.reason})",
        )
        self.assertEqual(result.reason_code, "INVALID_UNIT_NAME_TYPE")

    def test_string_goaa_router_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name="goaa-router"))

    def test_string_ollama_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name="ollama"))

    def test_integer_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name=123))

    def test_list_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name=["goaa-router"]))

    def test_dict_rejected(self):
        self._assert_type_rejected(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name={"value": "goaa-router"}))

    def test_enum_ollama_valid(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=ApprovedUnit.OLLAMA)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_enum_goaa_router_valid(self):
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=ApprovedUnit.GOAA_ROUTER)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_none_not_rejected_by_type_guard(self):
        """None is accepted (but subsequent checks may reject)."""
        req = ShellTaskRequest(
            task_id="t1", template_id="systemctl_is_active",
            resource_name="runtime_local",
            unit_name=None)
        result = validate_request(req)
        self.assertEqual(result.status, ValidationStatus.REJECTED_ARGUMENT)
        self.assertEqual(result.reason_code, "MISSING_UNIT_NAME")


class TestExceptionSafety(unittest.TestCase):
    """Validator must never raise AttributeError on invalid types."""

    def _assert_clean_rejection(self, req: ShellTaskRequest):
        """Whether result is VALID or REJECTED, no exception allowed."""
        try:
            result = validate_request(req)
            self.assertIn(result.status, (
                ValidationStatus.VALID,
                ValidationStatus.REJECTED_ARGUMENT,
                ValidationStatus.REJECTED_TEMPLATE,
                ValidationStatus.REJECTED_RESOURCE,
                ValidationStatus.REJECTED_POLICY,
            ))
        except Exception as exc:
            self.fail(f"validate_request raised {type(exc).__name__}: {exc}")

    def test_git_mode_string_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode="HEAD_SHORT"))

    def test_git_mode_integer_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode=123))

    def test_git_mode_list_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="git_rev_parse",
                resource_name="repo_main",
                git_mode=["HEAD_SHORT"]))

    def test_unit_name_string_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name="goaa-router"))

    def test_unit_name_integer_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name=123))

    def test_unit_name_list_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="systemctl_is_active",
                resource_name="runtime_local",
                unit_name=["ollama"]))

    def test_both_wrong_no_crash(self):
        self._assert_clean_rejection(
            ShellTaskRequest(
                task_id="t1", template_id="pwd",
                git_mode="HEAD_SHORT",
                unit_name="ollama"))


if __name__ == "__main__":
    unittest.main()
