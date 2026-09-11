"""
GOAA Shell Capability V0 — Policy unit tests (刀 1)
====================================================
Covers: template count, resource map, blocklist contents, path
patterns, approved units.  No execution, no subprocess.
"""

import unittest

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


class TestPolicyConstants(unittest.TestCase):
    """Policy-level invariants."""

    def test_policy_version(self):
        self.assertEqual(POLICY_VERSION, "shell-v0.1-knife1")

    def test_allowlist_exactly_10(self):
        """Design spec: exactly 10 templates in V0 knife 1."""
        expected = frozenset({
            "pwd", "whoami", "hostname", "date_iso", "uptime_pretty",
            "df_summary", "free_human", "git_status_short",
            "git_rev_parse", "systemctl_is_active",
        })
        self.assertEqual(ALLOWED_TEMPLATE_IDS, expected)

    def test_resource_map_two_entries(self):
        self.assertEqual(len(RESOURCE_MAP), 2)
        self.assertIn("repo_main", RESOURCE_MAP)
        self.assertIn("runtime_local", RESOURCE_MAP)
        self.assertEqual(RESOURCE_MAP["repo_main"],
                         "/home/aika/Projects/goaa-ai-main")
        self.assertEqual(RESOURCE_MAP["runtime_local"],
                         "/opt/goaa/repo")

    def test_resource_names_correct(self):
        self.assertEqual(ALLOWED_RESOURCE_NAMES,
                         frozenset({"repo_main", "runtime_local"}))

    def test_approved_units(self):
        expected = frozenset({
            "goaa-local-console",
            "goaa-worker-agent",
            "goaa-telemetry-writer",
            "ollama",
            "goaa-router",
        })
        self.assertEqual(APPROVED_UNITS, expected)

    def test_git_rev_parse_modes(self):
        self.assertEqual(GIT_REV_PARSE_MODES,
                         frozenset({"HEAD_SHORT", "BRANCH_NAME"}))


class TestTemplateArgv(unittest.TestCase):
    """Fixed argv generation from templates."""

    def test_pwd(self):
        self.assertEqual(_template_argv("pwd"), ["pwd"])

    def test_whoami(self):
        self.assertEqual(_template_argv("whoami"), ["whoami"])

    def test_hostname(self):
        self.assertEqual(_template_argv("hostname"), ["hostname"])

    def test_date_iso(self):
        self.assertEqual(_template_argv("date_iso"),
                         ["date", "--iso-8601=seconds"])

    def test_uptime_pretty(self):
        self.assertEqual(_template_argv("uptime_pretty"),
                         ["uptime", "-p"])

    def test_df_summary(self):
        self.assertEqual(_template_argv("df_summary"),
                         ["df", "-h",
                          "--output=source,size,used,avail,pcent,target"])

    def test_free_human(self):
        self.assertEqual(_template_argv("free_human"), ["free", "-h"])

    def test_git_status_short(self):
        self.assertEqual(_template_argv("git_status_short"),
                         ["git", "-C", "<resolved_resource>",
                          "status", "--short"])

    def test_git_rev_parse_head_short(self):
        self.assertEqual(
            _template_argv("git_rev_parse", "HEAD_SHORT"),
            ["git", "-C", "<resolved_resource>",
             "rev-parse", "--short", "HEAD"],
        )

    def test_git_rev_parse_branch_name(self):
        self.assertEqual(
            _template_argv("git_rev_parse", "BRANCH_NAME"),
            ["git", "-C", "<resolved_resource>",
             "rev-parse", "--abbrev-ref", "HEAD"],
        )

    def test_git_rev_parse_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            _template_argv("git_rev_parse", "INVALID_MODE")

    def test_systemctl_is_active_valid_unit(self):
        self.assertEqual(
            _template_argv("systemctl_is_active", "ollama"),
            ["systemctl", "is-active", "ollama"],
        )

    def test_systemctl_is_active_invalid_unit_raises(self):
        with self.assertRaises(ValueError):
            _template_argv("systemctl_is_active", "nginx")

    def test_unknown_template_raises(self):
        with self.assertRaises(KeyError):
            _template_argv("does_not_exist")


class TestBlocklistIntegrity(unittest.TestCase):
    """Blocklist coverage."""

    def test_blocked_commands_nonempty(self):
        self.assertGreater(len(BLOCKED_COMMANDS), 0)
        # Key dangerous commands must be present
        for cmd in ("bash", "sh", "sudo", "curl", "ssh",
                    "python", "python3", "node"):
            self.assertIn(cmd, BLOCKED_COMMANDS)

    def test_blocked_shell_chars_nonempty(self):
        self.assertGreater(len(BLOCKED_SHELL_CHARS), 0)
        for ch in ("|", ">", "$(", "`", "&&", ";"):
            self.assertIn(ch, BLOCKED_SHELL_CHARS)

    def test_blocked_path_prefixes(self):
        self.assertIn("/etc/goaa", BLOCKED_PATH_PREFIXES)
        self.assertIn("/root/.ssh", BLOCKED_PATH_PREFIXES)

    def test_blocked_path_suffixes(self):
        for s in (".env", ".pem", ".key"):
            self.assertIn(s, BLOCKED_PATH_SUFFIXES)

    def test_blocked_path_names(self):
        for n in ("secrets", "id_rsa", "id_ed25519"):
            self.assertIn(n, BLOCKED_PATH_NAMES)

    def test_blocked_path_globs(self):
        expected = {
            "/home/*/.ssh",
            "/proc/*/environ",
            "/proc/*/cmdline",
            "/dev",
            "/sys",
            "/run/secrets",
        }
        for g in expected:
            self.assertIn(g, BLOCKED_PATH_GLOBS)


class TestTemplatePolicyMetadata(unittest.TestCase):
    """Per-template metadata constraints."""

    def test_timeout_max_10(self):
        for tid, pol in TEMPLATE_POLICY.items():
            timeout = pol[0]
            self.assertLessEqual(
                timeout, 10,
                f"{tid}: timeout {timeout}s exceeds max 10s",
            )

    def test_stdout_limit_max_32k(self):
        for tid, pol in TEMPLATE_POLICY.items():
            limit = pol[1]
            self.assertLessEqual(
                limit, 32768,
                f"{tid}: stdout limit {limit} exceeds 32KB",
            )

    def test_stderr_limit_max_16k(self):
        for tid, pol in TEMPLATE_POLICY.items():
            limit = pol[2]
            self.assertLessEqual(
                limit, 16384,
                f"{tid}: stderr limit {limit} exceeds 16KB",
            )

    def test_git_templates_need_resource_and_approval(self):
        for tid in ("git_status_short", "git_rev_parse", "systemctl_is_active"):
            pol = TEMPLATE_POLICY[tid]
            self.assertTrue(pol[4], f"{tid} should require resource")
            self.assertTrue(pol[5], f"{tid} should require approval")

    def test_simple_templates_no_resource(self):
        for tid in ("pwd", "whoami", "hostname", "date_iso",
                     "uptime_pretty", "df_summary", "free_human"):
            pol = TEMPLATE_POLICY[tid]
            self.assertFalse(pol[4], f"{tid} should not require resource")


if __name__ == "__main__":
    unittest.main()
