"""
GOAA Authorization Kernel AK-2 — Effect Classifier
====================================================
Pure functions for classifying actions into effects, recomputing
equivalent groups, and building/verifying classification attestations.

No I/O, no subprocess, no network. All functions are deterministic.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §7, §10, §14
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from authorization_kernel.enums import ActionEffect, AuthorizationDecision
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.action_request import CanonicalParameter, ActionRequest
from authorization_kernel.classification_attestation import (
    ClassificationAttestation,
    compute_attestation_hash,
    verify_attestation_hash,
    classification_matches,
)
from authorization_kernel.classification_policy import (
    ClassificationPolicy,
    EffectInheritanceRule,
    EffectGroupRule,
)


class ClassificationPolicyError(Exception):
    """Raised when a ClassificationPolicy is structurally invalid.

    This is an internal error indicating the policy itself is broken.
    It is not an authorization decision — it signals a configuration fault.
    """


@dataclass(frozen=True)
class RecomputedClassification:
    """The result of recomputing an action's effects and groups."""

    primary_effect: ActionEffect
    secondary_effects: frozenset[ActionEffect] = field(default_factory=frozenset)
    equivalent_action_groups: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ClassificationResult:
    """The outcome of a classification attempt.

    decision: ALLOW if classification succeeded, POLICY_CONFLICT or
              OUT_OF_SCOPE otherwise.
    classification: the recomputed classification, or None on failure.
    reason_code: a brief string explaining the outcome.
    """

    decision: AuthorizationDecision
    classification: RecomputedClassification | None = None
    reason_code: str = ""


# ---------------------------------------------------------------------------
# Inheritance helpers
# ---------------------------------------------------------------------------


def _compute_inherited_effects(
    effects: frozenset[ActionEffect],
    inheritance_rules: tuple[EffectInheritanceRule, ...],
) -> set[ActionEffect]:
    """Recursively compute the closure of inherited effects.

    Builds a mapping from each effect to its direct inherited effects,
    then performs a BFS/DFS closure to discover all transitive inheritance.
    """
    # Build lookup
    inherit_map: dict[ActionEffect, frozenset[ActionEffect]] = {}
    for rule in inheritance_rules:
        inherit_map[rule.effect] = rule.inherited_effects

    result: set[ActionEffect] = set(effects)

    def _collect(e: ActionEffect) -> None:
        inherited = inherit_map.get(e, frozenset())
        for ie in inherited:
            if ie not in result:
                result.add(ie)
                # Inherited effects may themselves inherit further
                _collect(ie)

    for e in effects:
        _collect(e)

    return result


# ---------------------------------------------------------------------------
# Group computation
# ---------------------------------------------------------------------------


def _build_group_map(
    group_rules: tuple[EffectGroupRule, ...],
) -> dict[ActionEffect, str]:
    """Build a lookup from ActionEffect to its group name.

    Raises ClassificationPolicyError if any effect lacks a mapping.
    """
    group_map: dict[ActionEffect, str] = {}
    for rule in group_rules:
        group_map[rule.effect] = rule.group
    return group_map


def recompute_equivalent_groups(
    primary_effect: ActionEffect,
    secondary_effects: frozenset[ActionEffect],
    policy: ClassificationPolicy,
) -> frozenset[str]:
    """Recompute the set of equivalent action groups from effects.

    All effects (primary + secondary + inherited) are mapped to their
    group names via the policy's group_rules.

    Raises ClassificationPolicyError if the policy is incomplete
    (any effect lacks a group mapping).
    """
    group_map = _build_group_map(policy.group_rules)

    # Gather all effects: primary + secondary + inherited
    all_effects: set[ActionEffect] = {primary_effect}
    all_effects.update(secondary_effects)

    # Include inherited effects
    all_effects.update(
        _compute_inherited_effects(
            frozenset(all_effects), policy.inheritance_rules
        )
    )

    groups: set[str] = set()
    for effect in all_effects:
        g = group_map.get(effect)
        if g is None:
            raise ClassificationPolicyError(
                f"no group mapping for effect {effect}"
            )
        groups.add(g)

    return frozenset(groups)


# ---------------------------------------------------------------------------
# Resource type checking
# ---------------------------------------------------------------------------


def _check_resource_types(
    resource_scopes: tuple[TypedResourceScope, ...],
    required: frozenset,
) -> bool:
    """Check that all required resource scope types are present."""
    present = {s.scope_type for s in resource_scopes}
    return required.issubset(present)


# ---------------------------------------------------------------------------
# classify_action
# ---------------------------------------------------------------------------


def classify_action(
    requested_tool: str,
    canonical_parameters: tuple[CanonicalParameter, ...],
    resource_scopes: tuple[TypedResourceScope, ...],
    policy: ClassificationPolicy,
    expected_policy_version: str,
) -> ClassificationResult:
    """Classify a requested action against a ClassificationPolicy.

    Returns a ClassificationResult with:
      - ALLOW + RecomputedClassification on successful match
      - OUT_OF_SCOPE if no matching operation found or resource types missing
      - POLICY_CONFLICT if policy version mismatch or structural error
    """
    # Policy version check
    if policy.version != expected_policy_version:
        return ClassificationResult(
            decision=AuthorizationDecision.POLICY_CONFLICT,
            reason_code=f"policy version mismatch: expected "
            f"{expected_policy_version}, got {policy.version}",
        )

    # Find matching rule
    matching_rule = None
    for rule in policy.rules:
        if rule.operation_id == requested_tool:
            matching_rule = rule
            break

    if matching_rule is None:
        return ClassificationResult(
            decision=AuthorizationDecision.OUT_OF_SCOPE,
            reason_code=f"unknown operation_id: {requested_tool}",
        )

    # Check required resource types
    if matching_rule.required_resource_types:
        if not _check_resource_types(
            resource_scopes, matching_rule.required_resource_types
        ):
            return ClassificationResult(
                decision=AuthorizationDecision.OUT_OF_SCOPE,
                reason_code=f"missing required resource types for "
                f"{requested_tool}",
            )

    # Build effect set: primary + base secondary
    primary = matching_rule.primary_effect
    secondary: set[ActionEffect] = set(matching_rule.base_secondary_effects)

    # Add parameter-based effects
    if matching_rule.parameter_effect_rules:
        param_map: dict[str, str] = {}
        for p in canonical_parameters:
            param_map[p.name] = p.value
        for pe_rule in matching_rule.parameter_effect_rules:
            actual_value = param_map.get(pe_rule.parameter_name)
            if actual_value == pe_rule.parameter_value:
                secondary.add(pe_rule.effect)

    # Compute inheritance closure
    all_with_inheritance = _compute_inherited_effects(
        frozenset({primary}) | frozenset(secondary),
        policy.inheritance_rules,
    )

    # Remove primary from secondary set (primary must not be in secondary)
    secondary_final = frozenset(
        e for e in all_with_inheritance if e != primary
    )

    # Compute groups
    try:
        groups = recompute_equivalent_groups(primary, secondary_final, policy)
    except ClassificationPolicyError as exc:
        return ClassificationResult(
            decision=AuthorizationDecision.POLICY_CONFLICT,
            reason_code=f"policy error during group recomputation: {exc}",
        )

    return ClassificationResult(
        decision=AuthorizationDecision.ALLOW,
        classification=RecomputedClassification(
            primary_effect=primary,
            secondary_effects=secondary_final,
            equivalent_action_groups=groups,
        ),
        reason_code="classified",
    )


# ---------------------------------------------------------------------------
# build_classification_attestation
# ---------------------------------------------------------------------------


def build_classification_attestation(
    request: ActionRequest,
    recomputed: RecomputedClassification,
    policy_version: str,
) -> ClassificationAttestation:
    """Build a ClassificationAttestation from an ActionRequest and
    recomputed classification.

    Steps:
      1. Create attestation with declared fields from request,
         recomputed fields from recomputed, and a placeholder hash.
      2. Compute the real hash via AK-1 compute_attestation_hash().
      3. Replace placeholder with real hash via dataclasses.replace().
    """
    placeholder = ClassificationAttestation(
        classification_policy_version=policy_version,
        declared_primary_effect=request.primary_effect,
        declared_secondary_effects=request.secondary_effects,
        recomputed_primary_effect=recomputed.primary_effect,
        recomputed_secondary_effects=recomputed.secondary_effects,
        declared_equivalent_groups=request.equivalent_action_groups,
        recomputed_equivalent_groups=recomputed.equivalent_action_groups,
        classification_attestation_hash="",
    )
    real_hash = compute_attestation_hash(placeholder)
    return dataclasses.replace(placeholder, classification_attestation_hash=real_hash)


# ---------------------------------------------------------------------------
# verify_classification_attestation
# ---------------------------------------------------------------------------


def verify_classification_attestation(
    attestation: ClassificationAttestation,
) -> bool:
    """Verify that a classification attestation is authentic and consistent.

    Both conditions must hold:
      1. attestation_hash is valid (hash covers all other fields)
      2. Declared and recomputed fields match
    """
    return verify_attestation_hash(attestation) and classification_matches(
        attestation
    )
