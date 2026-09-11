"""
GOAA Shell Capability V0 — Policy (刀 1)
=========================================
Immutable policy definitions: allowed resources, templates, blocklists.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md
Policy version: shell-v0.1-knife1
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional, Tuple

from shell_schema import ApprovedUnit, GitRevParseMode

# ── Policy metadata ────────────────────────────────────────────────

POLICY_VERSION: str = "shell-v0.1-knife1"

# ── Named resource mappings ────────────────────────────────────────
# Only two symbolic resources are allowed in V0 knife 1.
# Real paths are never accepted from user input.

RESOURCE_MAP: Dict[str, str] = {
    "repo_main": "/home/aika/Projects/goaa-ai-main",
    "runtime_local": "/opt/goaa/repo",
}

ALLOWED_RESOURCE_NAMES: FrozenSet[str] = frozenset(RESOURCE_MAP.keys())

# ── Template definitions ───────────────────────────────────────────
# Each template defines a fixed argv (no user-supplied arguments).
# <resolved_resource> is substituted by the Validator at resolve time.

# -- Git options used by git templates --
GIT_REV_PARSE_MODES: FrozenSet[str] = frozenset(
    m.value for m in GitRevParseMode
)

# -- Approved systemd unit names for systemctl --
# Derived from the ApprovedUnit enum so they stay in sync.
APPROVED_UNITS: FrozenSet[str] = frozenset(
    m.value for m in ApprovedUnit
)


def _template_argv(template_id: str, option: Optional[str] = None) -> List[str]:
    """Return the fixed argv for *template_id*.

    Raises KeyError for unknown template IDs.
    *option* is used only by templates that require a sub-choice
    (e.g. git_rev_parse).
    """
    if template_id == "pwd":
        return ["pwd"]
    elif template_id == "whoami":
        return ["whoami"]
    elif template_id == "hostname":
        return ["hostname"]
    elif template_id == "date_iso":
        return ["date", "--iso-8601=seconds"]
    elif template_id == "uptime_pretty":
        return ["uptime", "-p"]
    elif template_id == "df_summary":
        return ["df", "-h", "--output=source,size,used,avail,pcent,target"]
    elif template_id == "free_human":
        return ["free", "-h"]
    elif template_id == "git_status_short":
        return ["git", "-C", "<resolved_resource>", "status", "--short"]
    elif template_id == "git_rev_parse":
        if option == "HEAD_SHORT":
            return ["git", "-C", "<resolved_resource>", "rev-parse", "--short", "HEAD"]
        elif option == "BRANCH_NAME":
            return ["git", "-C", "<resolved_resource>", "rev-parse", "--abbrev-ref", "HEAD"]
        else:
            raise ValueError(f"Invalid git_rev_parse mode: {option!r}")
    elif template_id == "systemctl_is_active":
        if option is None or option not in APPROVED_UNITS:
            raise ValueError(f"Unapproved systemd unit: {option!r}")
        return ["systemctl", "is-active", option]
    else:
        raise KeyError(f"Unknown template_id: {template_id!r}")


# ── Per-template policy metadata ───────────────────────────────────

TemplatePolicy = Tuple[int, int, int, str, bool, bool]  # timeout, stdout_limit, stderr_limit, risk, needs_resource, needs_approval

TEMPLATE_POLICY: Dict[str, TemplatePolicy] = {
    "pwd":                (5, 32768, 16384, "low",    False, False),
    "whoami":             (5, 32768, 16384, "low",    False, False),
    "hostname":           (5, 32768, 16384, "low",    False, False),
    "date_iso":           (5, 32768, 16384, "low",    False, False),
    "uptime_pretty":      (5, 32768, 16384, "low",    False, False),
    "df_summary":         (5, 32768, 16384, "low",    False, False),
    "free_human":         (5, 32768, 16384, "low",    False, False),
    "git_status_short":   (10, 32768, 16384, "medium", True,  True),
    "git_rev_parse":      (10, 32768, 16384, "medium", True,  True),
    "systemctl_is_active":(10, 32768, 16384, "medium", True,  True),
}

ALLOWED_TEMPLATE_IDS: FrozenSet[str] = frozenset(TEMPLATE_POLICY.keys())

# ── Hard block tokens (defense-in-depth) ──────────────────────────
# These are used by the Validator to reject any request whose fields
# contain banned shell tokens / commands.

BLOCKED_COMMANDS: FrozenSet[str] = frozenset({
    "bash", "sh", "eval", "exec", "source",
    "sudo", "su", "doas",
    "env", "printenv",
    "curl", "wget", "ping", "nc", "netcat",
    "ssh", "scp", "rsync",
    "python", "python3", "perl", "ruby", "node",
})

BLOCKED_SHELL_CHARS: FrozenSet[str] = frozenset({
    "|", ">", ">>", "<", "$(", "$", "`",
    "&&", "||", ";",
})

BLOCKED_PATH_PREFIXES: Tuple[str, ...] = (
    "/etc/goaa",
    "/root/.ssh",
)

BLOCKED_PATH_GLOBS: Tuple[str, ...] = (
    "/home/*/.ssh",
    "/proc/*/environ",
    "/proc/*/cmdline",
    "/dev",
    "/sys",
    "/run/secrets",
)

BLOCKED_PATH_SUFFIXES: Tuple[str, ...] = (
    ".env",
    ".pem",
    ".key",
)

BLOCKED_PATH_NAMES: FrozenSet[str] = frozenset({
    "secrets",
    "id_rsa",
    "id_ed25519",
})
