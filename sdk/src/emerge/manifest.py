"""Generate an ``emerge.yaml`` manifest from an :class:`AgentSpec`."""

from __future__ import annotations

from typing import Any

from .sdk import AgentSpec

SCHEMA_VERSION = "1.0"


def build_manifest(spec: AgentSpec, *, host: str = "localhost") -> dict[str, Any]:
    """Build the manifest dict the registry validates against emerge.yaml schema."""
    endpoint = f"http://{host}:{spec.port}"
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "identity": {
            "id": spec.did,
            "name": spec.name,
            "version": spec.version,
            "description": spec.description,
            "tags": spec.tags,
        },
        "protocol": {
            "type": "a2a",
            "version": "1.0",
            "transport": {"type": "http", "endpoint": endpoint},
        },
        "health_endpoint": f"{endpoint}/health",
        "security": {
            "transport_layer": {"type": "none"},
            "auth_strategies": [],
        },
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "tags": s.tags,
                "examples": s.examples,
            }
            for s in spec.skills
        ],
    }
    if spec.base_fee is not None:
        manifest["payment"] = {"enabled": True, "base_fee": spec.base_fee}
    return manifest


def manifest_yaml(spec: AgentSpec, *, host: str = "localhost") -> str:
    """Serialize the manifest to YAML text."""
    import yaml

    return yaml.safe_dump(
        build_manifest(spec, host=host), sort_keys=False, default_flow_style=False
    )
