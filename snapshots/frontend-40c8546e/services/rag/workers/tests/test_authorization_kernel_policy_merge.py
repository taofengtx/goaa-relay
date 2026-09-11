"""
GOAA Authorization Kernel AK-2 — Policy Merge Unit Tests
===========================================================
Tests: merge_policy_decisions() with full precedence hierarchy,
       empty input handling, type safety, order independence.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
"""

from __future__ import annotations

import unittest

from authorization_kernel.enums import AuthorizationDecision
from authorization_kernel.policy_merge import merge_policy_decisions


class TestMergePolicyDecisions(unittest.TestCase):

    # --- ALLOW ---

    def test_single_allow(self) -> None:
        result = merge_policy_decisions((AuthorizationDecision.ALLOW,))
        self.assertEqual(result, AuthorizationDecision.ALLOW)

    def test_all_allow(self) -> None:
        result = merge_policy_decisions(
            (AuthorizationDecision.ALLOW, AuthorizationDecision.ALLOW)
        )
        self.assertEqual(result, AuthorizationDecision.ALLOW)

    def test_all_allow_multiple(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.ALLOW,
            )
        )
        self.assertEqual(result, AuthorizationDecision.ALLOW)

    # --- REQUIRES_APPROVAL ---

    def test_requires_approval_wins_over_allow(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.REQUIRES_APPROVAL,
                AuthorizationDecision.ALLOW,
            )
        )
        self.assertEqual(result, AuthorizationDecision.REQUIRES_APPROVAL)

    def test_requires_approval_single(self) -> None:
        result = merge_policy_decisions(
            (AuthorizationDecision.REQUIRES_APPROVAL,)
        )
        self.assertEqual(result, AuthorizationDecision.REQUIRES_APPROVAL)

    # --- OUT_OF_SCOPE ---

    def test_out_of_scope_wins_over_requires_approval(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.OUT_OF_SCOPE,
                AuthorizationDecision.REQUIRES_APPROVAL,
            )
        )
        self.assertEqual(result, AuthorizationDecision.OUT_OF_SCOPE)

    def test_out_of_scope_wins_over_allow(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.OUT_OF_SCOPE,
                AuthorizationDecision.ALLOW,
            )
        )
        self.assertEqual(result, AuthorizationDecision.OUT_OF_SCOPE)

    # --- DENY ---

    def test_deny_wins_over_out_of_scope(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.DENY,
                AuthorizationDecision.OUT_OF_SCOPE,
            )
        )
        self.assertEqual(result, AuthorizationDecision.DENY)

    def test_deny_wins_over_requires_approval(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.DENY,
                AuthorizationDecision.REQUIRES_APPROVAL,
            )
        )
        self.assertEqual(result, AuthorizationDecision.DENY)

    def test_deny_wins_over_allow(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.DENY,
                AuthorizationDecision.ALLOW,
            )
        )
        self.assertEqual(result, AuthorizationDecision.DENY)

    def test_deny_single(self) -> None:
        result = merge_policy_decisions((AuthorizationDecision.DENY,))
        self.assertEqual(result, AuthorizationDecision.DENY)

    # --- POLICY_CONFLICT ---

    def test_policy_conflict_wins_over_deny(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.POLICY_CONFLICT,
                AuthorizationDecision.DENY,
            )
        )
        self.assertEqual(result, AuthorizationDecision.POLICY_CONFLICT)

    def test_policy_conflict_wins_over_all(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.POLICY_CONFLICT,
                AuthorizationDecision.DENY,
                AuthorizationDecision.OUT_OF_SCOPE,
                AuthorizationDecision.REQUIRES_APPROVAL,
                AuthorizationDecision.ALLOW,
            )
        )
        self.assertEqual(result, AuthorizationDecision.POLICY_CONFLICT)

    def test_policy_conflict_single(self) -> None:
        result = merge_policy_decisions(
            (AuthorizationDecision.POLICY_CONFLICT,)
        )
        self.assertEqual(result, AuthorizationDecision.POLICY_CONFLICT)

    # --- Empty input ---

    def test_empty_decisions_fail_closed(self) -> None:
        """Empty decisions must NOT return ALLOW."""
        result = merge_policy_decisions(())
        self.assertEqual(result, AuthorizationDecision.OUT_OF_SCOPE)

    # --- Order independence ---

    def test_order_independence_reversed(self) -> None:
        a = (
            AuthorizationDecision.ALLOW,
            AuthorizationDecision.DENY,
            AuthorizationDecision.ALLOW,
        )
        b = (
            AuthorizationDecision.DENY,
            AuthorizationDecision.ALLOW,
            AuthorizationDecision.ALLOW,
        )
        self.assertEqual(
            merge_policy_decisions(a),
            merge_policy_decisions(b),
        )

    def test_order_independence_policy_conflict_first(self) -> None:
        a = (
            AuthorizationDecision.POLICY_CONFLICT,
            AuthorizationDecision.ALLOW,
        )
        b = (
            AuthorizationDecision.ALLOW,
            AuthorizationDecision.POLICY_CONFLICT,
        )
        self.assertEqual(
            merge_policy_decisions(a),
            merge_policy_decisions(b),
        )

    # --- Type safety ---

    def test_non_tuple_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            merge_policy_decisions([AuthorizationDecision.ALLOW])  # type: ignore[arg-type]

    def test_non_authorization_decision_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            merge_policy_decisions(
                (AuthorizationDecision.ALLOW, "DENY")  # type: ignore[arg-type]
            )

    def test_none_in_decisions_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            merge_policy_decisions(
                (AuthorizationDecision.ALLOW, None)  # type: ignore[arg-type]
            )

    # --- Pure function / no side effects ---

    def test_no_side_effects(self) -> None:
        decisions = (
            AuthorizationDecision.ALLOW,
            AuthorizationDecision.DENY,
        )
        _ = merge_policy_decisions(decisions)
        # Original tuple unchanged
        self.assertEqual(len(decisions), 2)
        self.assertEqual(decisions[0], AuthorizationDecision.ALLOW)

    # --- Full hierarchy smoke tests ---

    def test_all_five_present_returns_policy_conflict(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.REQUIRES_APPROVAL,
                AuthorizationDecision.OUT_OF_SCOPE,
                AuthorizationDecision.DENY,
                AuthorizationDecision.POLICY_CONFLICT,
            )
        )
        self.assertEqual(result, AuthorizationDecision.POLICY_CONFLICT)

    def test_all_except_policy_conflict_returns_deny(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.REQUIRES_APPROVAL,
                AuthorizationDecision.OUT_OF_SCOPE,
                AuthorizationDecision.DENY,
            )
        )
        self.assertEqual(result, AuthorizationDecision.DENY)

    def test_allow_requires_approval_only_returns_requires_approval(self) -> None:
        result = merge_policy_decisions(
            (
                AuthorizationDecision.ALLOW,
                AuthorizationDecision.REQUIRES_APPROVAL,
            )
        )
        self.assertEqual(result, AuthorizationDecision.REQUIRES_APPROVAL)


if __name__ == "__main__":
    unittest.main()
