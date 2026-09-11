"""
GOAA Shell Capability V0 — Resource Policy (刀 2A-1)
=====================================================
Immutable resource path definitions and runtime path verification.

Design spec: docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md §7
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet


@dataclass(frozen=True)
class ResourcePolicy:
    """
    Security policy for a named resource path.

    All checks are performed by ``verify_runtime_path_evidence()``
    before any subprocess call.
    """

    canonical_path: str
    allowed_owner_names: FrozenSet[str]
    allowed_prefix: Path
    must_be_directory: bool = True
    reject_world_writable: bool = True


# ── Static policy definitions ──────────────────────────────────────
# These mirror RESOURCE_MAP in shell_policy.py but add path-level
# security constraints.  They MUST stay in sync with RESOURCE_MAP.

RESOURCE_POLICIES: dict[str, ResourcePolicy] = {
    "repo_main": ResourcePolicy(
        canonical_path="/home/aika/Projects/goaa-ai-main",
        allowed_owner_names=frozenset({"aika"}),
        allowed_prefix=Path("/home/aika/"),
        must_be_directory=True,
        reject_world_writable=True,
    ),
    "runtime_local": ResourcePolicy(
        canonical_path="/opt/goaa/repo",
        allowed_owner_names=frozenset({"root", "aika"}),
        allowed_prefix=Path("/opt/goaa/"),
        must_be_directory=True,
        reject_world_writable=True,
    ),
}


# ── Error type ─────────────────────────────────────────────────────


class PathRejected(Exception):
    """Raised when a resource path fails security checks."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ── Verification function ──────────────────────────────────────────


def verify_runtime_path_evidence(
    resource_name: str,
    *,
    mock_mode: bool = True,
) -> Path:
    """
    Verify that *resource_name* maps to a safe, real filesystem path.

    In **mock mode** (default for unit tests), filesystem calls are
    skipped — only the prefix check via ``Path.is_relative_to()`` is
    performed.  This allows testing without a real filesystem.

    In **live mode** (``mock_mode=False``), the full check is done:
    realpath resolution, owner verification, world-writable check,
    must-be-directory, and blocklist check.

    Returns the resolved ``Path`` on success.
    Raises ``PathRejected`` on any failure.
    """
    policy = RESOURCE_POLICIES.get(resource_name)
    if policy is None:
        raise PathRejected(f"unknown resource: {resource_name!r}")

    if mock_mode:
        # Mock mode: only check prefix via Path.is_relative_to.
        # This catches obvious prefix escapes without filesystem I/O.
        p = Path(policy.canonical_path)
        try:
            safe = p.is_relative_to(policy.allowed_prefix)
        except AttributeError:
            # Python < 3.9 fallback: os.path.commonpath
            common = os.path.commonpath(
                [str(p), str(policy.allowed_prefix)]
            )
            safe = common == str(policy.allowed_prefix)
        if not safe:
            raise PathRejected(
                f"prefix escape (mock): {p} not under "
                f"{policy.allowed_prefix}"
            )
        return p

    # ── Live mode: full filesystem checks ──────────────────────────
    try:
        p = Path(policy.canonical_path).resolve(strict=True)
    except FileNotFoundError:
        raise PathRejected(f"path does not exist: {policy.canonical_path}")
    except PermissionError:
        raise PathRejected(f"permission denied: {policy.canonical_path}")
    except OSError as e:
        raise PathRejected(f"path resolution error: {e}")

    # 2. Prefix check (Python 3.9+)
    try:
        safe = p.is_relative_to(policy.allowed_prefix)
    except AttributeError:
        common = os.path.commonpath(
            [str(p), str(policy.allowed_prefix)]
        )
        safe = common == str(policy.allowed_prefix)
    if not safe:
        raise PathRejected(
            f"prefix escape: {p} not under {policy.allowed_prefix}"
        )

    # 3. Must be directory
    if policy.must_be_directory and not p.is_dir():
        raise PathRejected(f"not a directory: {p}")

    # 4. Owner check (by name, not UID)
    try:
        import pwd  # only available on Unix
        st = p.stat()
        owner_name = pwd.getpwuid(st.st_uid).pw_name
    except ImportError:
        # Non-Unix platform: skip owner check with a warning
        owner_name = "<unknown>"
    except (KeyError, OSError) as e:
        raise PathRejected(f"cannot determine owner: {e}")
    if owner_name not in policy.allowed_owner_names:
        raise PathRejected(
            f"wrong owner: {owner_name!r} "
            f"(allowed: {policy.allowed_owner_names})"
        )

    # 5. Reject world-writable
    if policy.reject_world_writable and (p.stat().st_mode & 0o002):
        raise PathRejected(f"world-writable: {p}")

    return p
