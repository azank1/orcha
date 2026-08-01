"""
Seed the registry with all fixture agents from tests/fixtures/.

Usage:
    # From repo root:
    uv run python services/registry/scripts/seed_agents.py [--registry-url URL]

What it does:
    1. Starts the test manifest server (port 9000) as a subprocess — fixtures
       point to http://localhost:9000 for both health checks and capability
       harvesting.
    2. POSTs each non-invalid *.yaml fixture to POST /api/agents/register.
    3. Stops the manifest server.

Prerequisites:
    - Registry service is running (default: http://localhost:8000)
    - DISABLE_AUTH=true in the registry .env (the script sends no token)
    - Kafka + PnD running if you want end-to-end indexing:
          make kafka-up && make kafka-topics && make pnd-dev
    - KAFKA_ENABLED=true in services/registry/.env for the registry to publish
      the Kafka event that triggers PnD indexing.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
MANIFEST_SERVER_SCRIPT = (
    Path(__file__).resolve().parents[1] / "tests" / "manifest_server.py"
)
MANIFEST_SERVER_PORT = 9000
MANIFEST_SERVER_URL = f"http://localhost:{MANIFEST_SERVER_PORT}"


def _wait_for_url(url: str, timeout: int = 10) -> bool:
    """Poll url until it returns 2xx or timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=2)
            if resp.is_success:
                return True
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass
        time.sleep(0.5)
    return False


def _start_manifest_server() -> subprocess.Popen:
    """Start the test manifest server in the background."""
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "services.registry.tests.manifest_server:app",
            "--host",
            "0.0.0.0",  # noqa: S104
            "--port",
            str(MANIFEST_SERVER_PORT),
            "--log-level",
            "warning",
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  started manifest server (pid {proc.pid}), waiting for readiness…")
    if not _wait_for_url(f"{MANIFEST_SERVER_URL}/health"):
        proc.terminate()
        raise RuntimeError(
            f"Manifest server did not become ready within 10s. "
            f"Check that port {MANIFEST_SERVER_PORT} is free."
        )
    print(f"  manifest server ready at {MANIFEST_SERVER_URL}")
    return proc


def _register_fixture(client: httpx.Client, registry_url: str, yaml_path: Path) -> str:
    """POST a single fixture YAML to the registry. Returns 'ok', 'conflict', or 'error'."""
    with yaml_path.open("rb") as fh:
        resp = client.post(
            f"{registry_url}/api/v1/agents/register",
            files={"emerge_yaml": (yaml_path.name, fh, "application/x-yaml")},
            timeout=30,
        )

    if resp.status_code == 201:
        data = resp.json().get("data", {})
        caps = data.get("capabilities_harvested", {})
        print(
            f"  ✓  {yaml_path.name:<35} → {data.get('name')} v{data.get('version')} "
            f"({caps.get('tools', 0)} tools, {caps.get('resources', 0)} resources)"
        )
        return "ok"
    if resp.status_code == 409:
        print(f"  ⚠  {yaml_path.name:<35} → already registered (skipped)")
        return "conflict"
    detail = resp.json().get("detail", {})
    print(
        f"  ✗  {yaml_path.name:<35} → {resp.status_code} {detail.get('message', resp.text)}"
    )
    return "error"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the registry with fixture agents."
    )
    parser.add_argument(
        "--registry-url",
        default="http://localhost:8000",
        help="Base URL of the registry service (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    registry_url = args.registry_url.rstrip("/")

    # ── Check registry is up ──────────────────────────────────────────────────
    print(f"\nChecking registry at {registry_url} …")
    if not _wait_for_url(f"{registry_url}/api/v1/health", timeout=5):
        print(f"  ✗  Registry not reachable at {registry_url}")
        print("     Start it with:  make dev s=registry   (or  uv run uvicorn ...)")
        sys.exit(1)
    print("  ✓  Registry is up")

    # ── Collect fixtures (skip invalid_* files) ───────────────────────────────
    fixtures = sorted(
        f for f in FIXTURES_DIR.glob("*.yaml") if not f.name.startswith("invalid_")
    )
    if not fixtures:
        print(f"\nNo fixtures found in {FIXTURES_DIR}")
        sys.exit(0)

    print(f"\nFound {len(fixtures)} fixture(s) to seed:")
    for f in fixtures:
        print(f"  • {f.name}")

    # ── Start manifest server ─────────────────────────────────────────────────
    print(f"\nStarting manifest server on port {MANIFEST_SERVER_PORT} …")
    manifest_proc = _start_manifest_server()

    # ── Register each fixture ─────────────────────────────────────────────────
    print(f"\nRegistering agents at {registry_url} …\n")
    counts = {"ok": 0, "conflict": 0, "error": 0}
    try:
        with httpx.Client() as client:
            for fixture_path in fixtures:
                result = _register_fixture(client, registry_url, fixture_path)
                counts[result] += 1
    finally:
        manifest_proc.terminate()
        manifest_proc.wait()
        print("\n  stopped manifest server")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(
        f"\n{'─' * 50}\n"
        f"  Registered:     {counts['ok']}\n"
        f"  Already exists: {counts['conflict']}\n"
        f"  Errors:         {counts['error']}\n"
        f"{'─' * 50}"
    )
    if counts["error"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
