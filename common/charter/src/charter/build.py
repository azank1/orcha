"""Build an AAC charter dict from an emerge.yaml manifest (RFC 0002).

Maps the manifest's flat ``authorized_scope`` block onto the charter shape
(FR-1). Absent optional blocks stay absent — "unspecified", not
"unrestricted".
"""

from __future__ import annotations

import uuid
from typing import Any

from .model import AACCharter


def build_charter(
    manifest: dict[str, Any],
    *,
    issuer: dict[str, Any],
    agent_identity: dict[str, Any],
    now: str | None = None,
) -> dict[str, Any]:
    """Construct an (unsigned) AAC charter dict from a manifest.

    - ``issuer`` — principal block: legal_name, identifier_type,
      identifier_value, optional regulator_license.
    - ``agent_identity`` — agent_id (DID), optional model_attestation /
      deployment_hash; agent_id defaults to the manifest's identity.id.
    - ``now`` — RFC 3339 timestamp used to fill a missing validity.not_before
      when the manifest declares a validity block.

    Field mapping from ``authorized_scope``: ``allowed_capabilities`` →
    ``permitted_actions``; ``spend_cap_usd`` → ``max_transaction_value``;
    ``rails`` → ``dpi_rails``; ``allowed_counterparties`` / ``jurisdictions`` /
    ``human_approval_required_above`` / ``delegation`` / ``validity`` pass
    through.
    """
    scope = manifest.get("authorized_scope") or {}
    identity = manifest.get("identity") or {}

    charter_scope: dict[str, Any] = {
        "dpi_rails": list(scope.get("rails") or []),
        "permitted_actions": list(scope.get("allowed_capabilities") or []),
        "prohibited_actions": list(scope.get("prohibited_actions") or []),
    }
    if scope.get("spend_cap_usd") is not None:
        charter_scope["max_transaction_value"] = scope["spend_cap_usd"]
    if scope.get("human_approval_required_above") is not None:
        charter_scope["human_approval_required_above"] = scope[
            "human_approval_required_above"
        ]
    if scope.get("allowed_counterparties"):
        charter_scope["allowed_counterparties"] = list(scope["allowed_counterparties"])
    if scope.get("jurisdictions"):
        charter_scope["jurisdictions"] = list(scope["jurisdictions"])

    charter: dict[str, Any] = {
        "charter_id": f"charter:{uuid.uuid4()}",
        "version": "1.0",
        "issued_by": dict(issuer),
        "agent_identity": {
            "agent_id": identity.get("id"),
            **agent_identity,
        },
        "authorized_scope": charter_scope,
    }

    if scope.get("delegation"):
        charter["delegation"] = dict(scope["delegation"])

    validity = scope.get("validity")
    if validity:
        validity = dict(validity)
        if validity.get("not_before") is None and now is not None:
            validity["not_before"] = now
        charter["validity"] = validity

    # Validate the shape before returning; raises on a malformed manifest block.
    return AACCharter(**charter).model_dump(exclude_none=True, exclude_unset=True)
