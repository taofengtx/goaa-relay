"""
GOAA Authorization Kernel AK-2 — Policy Merge
===============================================
Pure functions for merging multiple AuthorizationDecision values
using the strictest-policy precedence rule.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §11.3, §13
"""

from __future__ import annotations

from authorization_kernel.enums import AuthorizationDecision


# Precedence table: higher index = higher priority
_PRECEDENCE: tuple[AuthorizationDecision, ...] = (
    AuthorizationDecision.ALLOW,
    AuthorizationDecision.REQUIRES_APPROVAL,
    AuthorizationDecision.OUT_OF_SCOPE,
    AuthorizationDecision.DENY,
    AuthorizationDecision.POLICY_CONFLICT,
)


def merge_policy_decisions(
    decisions: tuple[AuthorizationDecision, ...],
) -> AuthorizationDecision:
    """Merge multiple AuthorizationDecision values using strictest precedence.

    Priority (highest to lowest):
      1. POLICY_CONFLICT
      2. DENY
      3. OUT_OF_SCOPE
      4. REQUIRES_APPROVAL
      5. ALLOW

    Rules:
      - Empty decisions tuple → OUT_OF_SCOPE (fail-closed)
      - Any POLICY_CONFLICT → POLICY_CONFLICT
      - Otherwise, any DENY → DENY
      - Otherwise, any OUT_OF_SCOPE → OUT_OF_SCOPE
      - Otherwise, any REQUIRES_APPROVAL → REQUIRES_APPROVAL
      - Only if ALL are ALLOW → ALLOW
      - Non-AuthorizationDecision values raise TypeError

    Order-independent and side-effect-free.
    """
    if not isinstance(decisions, tuple):
        raise TypeError("decisions must be a tuple")

    if not decisions:
        return AuthorizationDecision.OUT_OF_SCOPE

    # Build a presence mask (convert to set for O(1) lookup)
    present: set[AuthorizationDecision] = set()
    for d in decisions:
        if not isinstance(d, AuthorizationDecision):
            raise TypeError(
                f"all decisions must be AuthorizationDecision values; "
                f"got {type(d).__name__}: {d!r}"
            )
        present.add(d)

    # Check in precedence order (highest first)
    for decision in reversed(_PRECEDENCE):
        if decision in present:
            return decision

    # Should not reach here if decisions is non-empty
    return AuthorizationDecision.OUT_OF_SCOPE
