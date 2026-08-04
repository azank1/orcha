"""Validate all fleet agent emerge.yaml files against JSON Schema and ValidationService."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from services.registry.src.models.emerge_config import EmergeConfig
from services.registry.src.services.validation import ValidationService

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "docs/spec/emerge-yaml.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
FLEET_MANIFESTS = sorted((ROOT / "agents").glob("*/emerge.yaml"))


@pytest.mark.parametrize("manifest_path", FLEET_MANIFESTS, ids=lambda p: p.parent.name)
def test_fleet_manifest_valid(manifest_path: Path) -> None:
    data = yaml.safe_load(manifest_path.read_text())
    schema_errors = sorted(VALIDATOR.iter_errors(data), key=lambda e: list(e.path))
    assert not schema_errors, [f"{list(e.path)}: {e.message}" for e in schema_errors]

    config = EmergeConfig(**data)
    ok, msg = ValidationService.validate_emerge_config(config)
    assert ok, msg
