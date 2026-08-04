"""Make ``common.llm.src`` importable regardless of pytest rootdir.

Mirrors the pattern in ``common/charter/tests/conftest.py``: covers runs
from the repo root (``uv run pytest common/llm/tests/``) where the
root-level rootdir wins and no ini ``pythonpath`` is applied.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
