"""Monotonic delegation attenuation (aac-srs.md FR-3).

A child charter is valid only if its scope is a strict attenuation of its
parent's: every dimension narrows or holds. A missing scope dimension on
either side is a violation ("unspecified") — never an implicit pass.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def _dim(scope: dict[str, Any], *names: str) -> Any:
    """First present value among alternative key names, else None."""
    for name in names:
        if scope.get(name) is not None:
            return scope[name]
    return None


def _parse_datetime(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _subset_violations(
    dim: str, child: Any, parent: Any, *, direction: str
) -> list[str]:
    """Subset check in either direction ('child_in_parent' or 'parent_in_child')."""
    if child is None or parent is None:
        return [f"{dim}: unspecified"]
    child_set, parent_set = set(child), set(parent)
    if direction == "child_in_parent":
        extra = child_set - parent_set
        if extra:
            return [f"{dim}: child exceeds parent ({sorted(extra)})"]
    else:
        missing = parent_set - child_set
        if missing:
            return [f"{dim}: child drops parent prohibitions ({sorted(missing)})"]
    return []


def _decimal_violations(
    dim: str, child: Any, parent: Any, *, direction: str
) -> list[str]:
    """Decimal comparison: 'lte' means child <= parent, 'gte' child >= parent."""
    if child is None or parent is None:
        return [f"{dim}: unspecified"]
    try:
        child_value, parent_value = Decimal(str(child)), Decimal(str(parent))
    except InvalidOperation:
        return [f"{dim}: unparseable decimal"]
    if direction == "lte" and child_value > parent_value:
        return [f"{dim}: child {child_value} exceeds parent {parent_value}"]
    if direction == "gte" and child_value < parent_value:
        return [f"{dim}: child {child_value} below parent {parent_value}"]
    return []


def _validity_violations(child: Any, parent: Any) -> list[str]:
    if not child or not parent:
        return ["validity: unspecified"]
    child_before = _parse_datetime(child.get("not_before"))
    child_after = _parse_datetime(child.get("not_after"))
    parent_before = _parse_datetime(parent.get("not_before"))
    parent_after = _parse_datetime(parent.get("not_after"))
    if None in (child_before, child_after, parent_before, parent_after):
        return ["validity: unspecified"]
    if child_before < parent_before or child_after > parent_after:
        return ["validity: child window not within parent window"]
    return []


def _delegation_violations(child: Any, parent: Any) -> list[str]:
    if not parent:
        return ["delegation: unspecified"]
    if not parent.get("allowed", False):
        return ["delegation: not allowed by parent charter"]
    if not child:
        return ["delegation: unspecified"]
    child_depth = child.get("max_depth")
    parent_depth = parent.get("max_depth")
    if child_depth is None or parent_depth is None:
        return ["delegation: unspecified"]
    if child_depth > parent_depth - 1:
        return [
            (
                f"delegation: child max_depth {child_depth} "
                f"not below parent max_depth {parent_depth}"
            )
        ]
    return []


def scope_violations(
    child_scope: dict[str, Any], parent_scope: dict[str, Any]
) -> list[str]:
    """Attenuation check: every way ``child_scope`` widens ``parent_scope``.

    Scope dicts use the charter shape: ``rails`` (or ``dpi_rails``),
    ``permitted_actions``, ``prohibited_actions``, ``max_transaction_value``,
    ``human_approval_required_above``, ``validity``, ``delegation``.
    """
    violations: list[str] = []
    violations += _subset_violations(
        "rails",
        _dim(child_scope, "rails", "dpi_rails"),
        _dim(parent_scope, "rails", "dpi_rails"),
        direction="child_in_parent",
    )
    violations += _subset_violations(
        "permitted_actions",
        child_scope.get("permitted_actions"),
        parent_scope.get("permitted_actions"),
        direction="child_in_parent",
    )
    violations += _subset_violations(
        "prohibited_actions",
        child_scope.get("prohibited_actions"),
        parent_scope.get("prohibited_actions"),
        direction="parent_in_child",
    )
    violations += _decimal_violations(
        "max_transaction_value",
        child_scope.get("max_transaction_value"),
        parent_scope.get("max_transaction_value"),
        direction="lte",
    )
    violations += _decimal_violations(
        "human_approval_required_above",
        child_scope.get("human_approval_required_above"),
        parent_scope.get("human_approval_required_above"),
        direction="gte",
    )
    violations += _validity_violations(
        child_scope.get("validity"), parent_scope.get("validity")
    )
    violations += _delegation_violations(
        child_scope.get("delegation"), parent_scope.get("delegation")
    )
    return violations


def _charter_scope(charter: dict[str, Any]) -> dict[str, Any]:
    """Flatten a charter dict into the scope shape scope_violations expects."""
    scope = dict(charter.get("authorized_scope") or {})
    scope["validity"] = charter.get("validity")
    scope["delegation"] = charter.get("delegation")
    return scope


def verify_delegation_chain(chain: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Verify a charter delegation chain, root first.

    Per hop: scope attenuation (``scope_violations``) plus signature-chain
    linkage — the child's ``parent_charter_hash`` must equal the parent's
    ``charter_hash``.
    """
    violations: list[str] = []
    for hop, (parent, child) in enumerate(zip(chain, chain[1:], strict=False), start=1):
        for violation in scope_violations(
            _charter_scope(child), _charter_scope(parent)
        ):
            violations.append(f"hop {hop}: {violation}")
        parent_hash = parent.get("charter_hash")
        child_link = child.get("parent_charter_hash")
        if not parent_hash or not child_link:
            violations.append(f"hop {hop}: chain linkage: unspecified")
        elif child_link != parent_hash:
            violations.append(
                f"hop {hop}: chain linkage: parent_charter_hash does not match "
                "parent charter_hash"
            )
    return (not violations, violations)
