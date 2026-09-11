"""
GOAA Authorization Kernel AK-2 — Classification Policy
=========================================================
Defines pure data models for effect classification rules,
effect inheritance, and group mapping.

AK-2 defines only the data model. Policy loading and runtime
evaluation are implemented alongside classifier functions.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §10, §14
"""

from __future__ import annotations

from dataclasses import dataclass, field

from authorization_kernel.enums import ActionEffect, ResourceScopeType


@dataclass(frozen=True)
class ParameterEffectRule:
    """A parameter-based effect override rule.

    When the canonical parameter matches parameter_name == parameter_value,
    the corresponding effect is added to the action's secondary effects.
    """

    parameter_name: str
    parameter_value: str
    effect: ActionEffect

    def __post_init__(self) -> None:
        if not self.parameter_name:
            raise ValueError("parameter_name must not be empty")
        if not self.parameter_value:
            raise ValueError("parameter_value must not be empty")


@dataclass(frozen=True)
class ClassificationRule:
    """A classification rule mapping an operation to its effects and requirements.

    operation_id: unique identifier for the tool/operation being classified
    primary_effect: the primary factual effect of this operation
    base_secondary_effects: secondary effects common to all invocations
    required_resource_types: resource scope types that must be present
    parameter_effect_rules: optional parameter-specific effect overrides
    """

    operation_id: str
    primary_effect: ActionEffect
    base_secondary_effects: frozenset[ActionEffect] = field(default_factory=frozenset)
    required_resource_types: frozenset[ResourceScopeType] = field(
        default_factory=frozenset
    )
    parameter_effect_rules: tuple[ParameterEffectRule, ...] = ()

    def __post_init__(self) -> None:
        if not self.operation_id:
            raise ValueError("operation_id must not be empty")
        if self.primary_effect in self.base_secondary_effects:
            raise ValueError(
                f"primary_effect {self.primary_effect} must not appear "
                f"in base_secondary_effects"
            )
        # Check for duplicate parameter rules
        seen: set[tuple[str, str]] = set()
        for rule in self.parameter_effect_rules:
            key = (rule.parameter_name, rule.parameter_value)
            if key in seen:
                raise ValueError(
                    f"duplicate parameter effect rule: "
                    f"{rule.parameter_name}={rule.parameter_value}"
                )
            seen.add(key)


@dataclass(frozen=True)
class EffectInheritanceRule:
    """A factual inheritance rule: effect implies inherited_effects.

    For example:
      SECRET_READ → {READ}
      MOVE_OUT_OF_DISCOVERY → {RENAME}
      PUSH → {NETWORK_EGRESS}
    """

    effect: ActionEffect
    inherited_effects: frozenset[ActionEffect] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.effect in self.inherited_effects:
            raise ValueError(
                f"effect {self.effect} must not inherit itself"
            )


@dataclass(frozen=True)
class EffectGroupRule:
    """Maps a single ActionEffect to its equivalent action group name."""

    effect: ActionEffect
    group: str

    def __post_init__(self) -> None:
        if not self.group:
            raise ValueError("group must not be empty")


_ALL_EFFECTS: frozenset[ActionEffect] = frozenset(ActionEffect)

# Required: 14 base mapping rules → 13 unique groups
DEFAULT_GROUP_RULES: tuple[EffectGroupRule, ...] = (
    EffectGroupRule(ActionEffect.READ, "GROUP_READ"),
    EffectGroupRule(ActionEffect.WRITE, "GROUP_WRITE"),
    EffectGroupRule(ActionEffect.CREATE, "GROUP_CREATE"),
    EffectGroupRule(ActionEffect.DELETE, "GROUP_DELETE"),
    EffectGroupRule(ActionEffect.RENAME, "GROUP_RENAME"),
    EffectGroupRule(ActionEffect.MOVE_OUT_OF_DISCOVERY, "GROUP_RENAME"),
    EffectGroupRule(ActionEffect.EXECUTE, "GROUP_EXECUTE"),
    EffectGroupRule(ActionEffect.COMMIT, "GROUP_COMMIT"),
    EffectGroupRule(ActionEffect.PUSH, "GROUP_PUSH"),
    EffectGroupRule(ActionEffect.DEPLOY, "GROUP_DEPLOY"),
    EffectGroupRule(ActionEffect.SERVICE_RESTART, "GROUP_SERVICE_RESTART"),
    EffectGroupRule(ActionEffect.SECRET_READ, "GROUP_SECRET_READ"),
    EffectGroupRule(ActionEffect.NETWORK_EGRESS, "GROUP_NETWORK_EGRESS"),
    EffectGroupRule(ActionEffect.PERMISSION_CHANGE, "GROUP_PERMISSION_CHANGE"),
)

# Required: three factual inheritance rules
DEFAULT_INHERITANCE_RULES: tuple[EffectInheritanceRule, ...] = (
    EffectInheritanceRule(
        ActionEffect.SECRET_READ,
        frozenset({ActionEffect.READ}),
    ),
    EffectInheritanceRule(
        ActionEffect.MOVE_OUT_OF_DISCOVERY,
        frozenset({ActionEffect.RENAME}),
    ),
    EffectInheritanceRule(
        ActionEffect.PUSH,
        frozenset({ActionEffect.NETWORK_EGRESS}),
    ),
)


@dataclass(frozen=True)
class ClassificationPolicy:
    """A complete classification policy definition.

    version: unique version identifier for this policy
    rules: classification rules for specific operations
    inheritance_rules: factual effect inheritance definitions
    group_rules: effect-to-group mappings

    At construction, validates:
      - All 14 ActionEffect are covered by group_rules
      - Unique groups count = 13 (RENAME shared by RENAME + MOVE_OUT_OF_DISCOVERY)
      - No self-referencing or cyclic inheritance
      - No duplicate operation_id
    """

    version: str
    rules: tuple[ClassificationRule, ...] = ()
    inheritance_rules: tuple[EffectInheritanceRule, ...] = ()
    group_rules: tuple[EffectGroupRule, ...] = DEFAULT_GROUP_RULES

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("version must not be empty")

        # Validate group coverage: all 14 ActionEffect covered
        covered_effects: set[ActionEffect] = set()
        group_names: set[str] = set()
        for rule in self.group_rules:
            covered_effects.add(rule.effect)
            group_names.add(rule.group)
        uncovered = _ALL_EFFECTS - covered_effects
        if uncovered:
            raise ValueError(
                f"group_rules do not cover all effects; missing: "
                f"{[e.value for e in sorted(uncovered, key=lambda x: x.value)]}"
            )
        # unique groups must be exactly 13
        if len(group_names) != 13:
            raise ValueError(
                f"expected 13 unique group names, got {len(group_names)}"
            )

        # Validate no duplicate inheritance effect
        if self.inheritance_rules:
            seen_inherit: set[ActionEffect] = set()
            for rule in self.inheritance_rules:
                if rule.effect in seen_inherit:
                    raise ValueError(
                        f"duplicate inheritance rule for effect {rule.effect}"
                    )
                seen_inherit.add(rule.effect)

            # Validate no cycles in inheritance
            _validate_no_inheritance_cycles(self.inheritance_rules)

        # Validate no duplicate operation_id
        if self.rules:
            seen_op: set[str] = set()
            for rule in self.rules:
                if rule.operation_id in seen_op:
                    raise ValueError(
                        f"duplicate operation_id in rules: {rule.operation_id}"
                    )
                seen_op.add(rule.operation_id)


def _validate_no_inheritance_cycles(
    rules: tuple[EffectInheritanceRule, ...],
) -> None:
    """Detect cycles in inheritance rules.

    Raises ValueError if a cycle is detected.
    """
    # Build adjacency: effect -> set of inherited effects
    adj: dict[ActionEffect, set[ActionEffect]] = {}
    for rule in rules:
        adj.setdefault(rule.effect, set()).update(rule.inherited_effects)

    visited: set[ActionEffect] = set()
    rec_stack: set[ActionEffect] = set()

    def _dfs(node: ActionEffect) -> None:
        if node in rec_stack:
            raise ValueError(
                f"circular inheritance detected involving effect {node}"
            )
        if node in visited:
            return
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj.get(node, set()):
            _dfs(neighbor)
        rec_stack.remove(node)

    for effect in adj:
        _dfs(effect)
