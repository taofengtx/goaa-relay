"""
GOAA Authorization Kernel AK-2 — Classification Policy Unit Tests
===================================================================
Tests: ClassificationPolicy schema invariants, effect inheritance rules,
       group mapping coverage, parameter effect rules.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
"""

from __future__ import annotations

import unittest

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.classification_policy import (
    ClassificationPolicy,
    ClassificationRule,
    EffectGroupRule,
    EffectInheritanceRule,
    ParameterEffectRule,
    DEFAULT_GROUP_RULES,
    DEFAULT_INHERITANCE_RULES,
)


class TestParameterEffectRule(unittest.TestCase):

    def test_valid(self) -> None:
        rule = ParameterEffectRule("method", "deploy", ActionEffect.WRITE)
        self.assertEqual(rule.parameter_name, "method")
        self.assertEqual(rule.parameter_value, "deploy")
        self.assertEqual(rule.effect, ActionEffect.WRITE)

    def test_empty_name_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ParameterEffectRule("", "value", ActionEffect.READ)

    def test_empty_value_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ParameterEffectRule("name", "", ActionEffect.READ)

    def test_frozen(self) -> None:
        rule = ParameterEffectRule("a", "b", ActionEffect.READ)
        with self.assertRaises(AttributeError):
            rule.parameter_name = "c"  # type: ignore[misc]


class TestClassificationRule(unittest.TestCase):

    def _make_valid(self) -> ClassificationRule:
        return ClassificationRule(
            operation_id="git_push",
            primary_effect=ActionEffect.PUSH,
            base_secondary_effects=frozenset(),
        )

    def test_valid(self) -> None:
        rule = self._make_valid()
        self.assertEqual(rule.operation_id, "git_push")

    def test_empty_operation_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClassificationRule(
                operation_id="",
                primary_effect=ActionEffect.READ,
            )

    def test_primary_in_secondary_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClassificationRule(
                operation_id="test",
                primary_effect=ActionEffect.WRITE,
                base_secondary_effects=frozenset({ActionEffect.WRITE}),
            )

    def test_duplicate_parameter_rule_rejected(self) -> None:
        rule_a = ParameterEffectRule("method", "deploy", ActionEffect.WRITE)
        rule_b = ParameterEffectRule("method", "deploy", ActionEffect.EXECUTE)
        with self.assertRaises(ValueError):
            ClassificationRule(
                operation_id="test",
                primary_effect=ActionEffect.READ,
                parameter_effect_rules=(rule_a, rule_b),
            )

    def test_distinct_parameter_rules_allowed(self) -> None:
        rule_a = ParameterEffectRule("method", "deploy", ActionEffect.WRITE)
        rule_b = ParameterEffectRule("method", "restart", ActionEffect.SERVICE_RESTART)
        r = ClassificationRule(
            operation_id="test",
            primary_effect=ActionEffect.READ,
            parameter_effect_rules=(rule_a, rule_b),
        )
        self.assertEqual(len(r.parameter_effect_rules), 2)

    def test_frozen(self) -> None:
        rule = self._make_valid()
        with self.assertRaises(AttributeError):
            rule.operation_id = "x"  # type: ignore[misc]


class TestEffectInheritanceRule(unittest.TestCase):

    def test_secret_read_inherits_read(self) -> None:
        rule = EffectInheritanceRule(
            ActionEffect.SECRET_READ,
            frozenset({ActionEffect.READ}),
        )
        self.assertEqual(rule.effect, ActionEffect.SECRET_READ)
        self.assertIn(ActionEffect.READ, rule.inherited_effects)

    def test_move_out_of_discovery_inherits_rename(self) -> None:
        rule = EffectInheritanceRule(
            ActionEffect.MOVE_OUT_OF_DISCOVERY,
            frozenset({ActionEffect.RENAME}),
        )
        self.assertIn(ActionEffect.RENAME, rule.inherited_effects)

    def test_push_inherits_network_egress(self) -> None:
        rule = EffectInheritanceRule(
            ActionEffect.PUSH,
            frozenset({ActionEffect.NETWORK_EGRESS}),
        )
        self.assertIn(ActionEffect.NETWORK_EGRESS, rule.inherited_effects)

    def test_self_inheritance_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EffectInheritanceRule(
                ActionEffect.READ,
                frozenset({ActionEffect.READ}),
            )

    def test_frozen(self) -> None:
        rule = EffectInheritanceRule(ActionEffect.READ, frozenset())
        with self.assertRaises(AttributeError):
            rule.effect = ActionEffect.WRITE  # type: ignore[misc]


class TestEffectGroupRule(unittest.TestCase):

    def test_valid(self) -> None:
        rule = EffectGroupRule(ActionEffect.READ, "GROUP_READ")
        self.assertEqual(rule.group, "GROUP_READ")

    def test_empty_group_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EffectGroupRule(ActionEffect.READ, "")

    def test_frozen(self) -> None:
        rule = EffectGroupRule(ActionEffect.READ, "GROUP_READ")
        with self.assertRaises(AttributeError):
            rule.group = "GROUP_WRITE"  # type: ignore[misc]


class TestDefaultConstants(unittest.TestCase):

    def test_default_group_rules_count(self) -> None:
        # 14 ActionEffect → 14 rules
        self.assertEqual(len(DEFAULT_GROUP_RULES), 14)

    def test_default_groups_all_effects_covered(self) -> None:
        covered: set[ActionEffect] = set()
        for rule in DEFAULT_GROUP_RULES:
            covered.add(rule.effect)
        all_effects = set(ActionEffect)
        self.assertEqual(covered, all_effects)

    def test_default_groups_unique_group_count(self) -> None:
        group_names: set[str] = set()
        for rule in DEFAULT_GROUP_RULES:
            group_names.add(rule.group)
        # RENAME + MOVE_OUT_OF_DISCOVERY share GROUP_RENAME → 13 unique
        self.assertEqual(len(group_names), 13)

    def test_default_inheritance_rules_count(self) -> None:
        self.assertEqual(len(DEFAULT_INHERITANCE_RULES), 3)

    def test_no_false_inheritance(self) -> None:
        """Ensure DELETE↛SECRET_READ and PERMISSION_CHANGE↛SECRET_READ."""
        inherited_effects: set[ActionEffect] = set()
        for rule in DEFAULT_INHERITANCE_RULES:
            inherited_effects.update(rule.inherited_effects)
        self.assertNotIn(ActionEffect.SECRET_READ, inherited_effects
                         if ActionEffect.DELETE in {r.effect for r in DEFAULT_INHERITANCE_RULES}
                         else set())


class TestClassificationPolicy(unittest.TestCase):

    def _minimal_valid(self) -> ClassificationPolicy:
        return ClassificationPolicy(version="1.0")

    def test_valid_with_defaults(self) -> None:
        policy = self._minimal_valid()
        self.assertEqual(policy.version, "1.0")
        self.assertEqual(len(policy.group_rules), 14)

    def test_empty_version_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClassificationPolicy(version="")

    def test_incomplete_group_coverage_rejected(self) -> None:
        # Only 13 rules — missing one effect
        incomplete = tuple(DEFAULT_GROUP_RULES[:-1])
        with self.assertRaises(ValueError):
            ClassificationPolicy(
                version="1.0",
                group_rules=incomplete,
            )

    def test_less_than_13_unique_groups_rejected(self) -> None:
        """All rules mapping to same group → 1 unique, not 13."""
        bad_rules = tuple(
            EffectGroupRule(e, "GROUP_SAME") for e in ActionEffect
        )
        with self.assertRaises(ValueError):
            ClassificationPolicy(
                version="1.0",
                group_rules=bad_rules,
            )

    def test_duplicate_operation_id_rejected(self) -> None:
        rule_a = ClassificationRule(
            operation_id="git_push",
            primary_effect=ActionEffect.PUSH,
        )
        rule_b = ClassificationRule(
            operation_id="git_push",
            primary_effect=ActionEffect.PUSH,
        )
        with self.assertRaises(ValueError):
            ClassificationPolicy(
                version="1.0",
                rules=(rule_a, rule_b),
            )

    def test_duplicate_inheritance_effect_rejected(self) -> None:
        rule_a = EffectInheritanceRule(
            ActionEffect.SECRET_READ, frozenset({ActionEffect.READ})
        )
        rule_b = EffectInheritanceRule(
            ActionEffect.SECRET_READ, frozenset({ActionEffect.WRITE})
        )
        with self.assertRaises(ValueError):
            ClassificationPolicy(
                version="1.0",
                inheritance_rules=(rule_a, rule_b),
            )

    def test_circular_inheritance_rejected(self) -> None:
        """A→B→A cycle."""
        rules = (
            EffectInheritanceRule(
                ActionEffect.READ, frozenset({ActionEffect.WRITE})
            ),
            EffectInheritanceRule(
                ActionEffect.WRITE, frozenset({ActionEffect.READ})
            ),
        )
        with self.assertRaises(ValueError):
            ClassificationPolicy(
                version="1.0",
                inheritance_rules=rules,
            )

    def test_frozen(self) -> None:
        policy = self._minimal_valid()
        with self.assertRaises(AttributeError):
            policy.version = "2.0"  # type: ignore[misc]

    def test_more_than_13_unique_groups_rejected(self) -> None:
        """All rules mapping to unique groups → 14 unique, not 13."""
        rules = tuple(
            EffectGroupRule(e, f"GROUP_{e.value.upper()}")
            for e in ActionEffect
        )
        with self.assertRaises(ValueError):
            ClassificationPolicy(version="1.0", group_rules=rules)


if __name__ == "__main__":
    unittest.main()
