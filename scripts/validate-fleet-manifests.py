#!/usr/bin/env python3
"""Validate fleet agent emerge.yaml files against JSON Schema and Pydantic rules."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env.setdefault(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/metaorcha",
    )
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "services/registry/tests/test_fleet_manifests.py",
            "-v",
        ],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
