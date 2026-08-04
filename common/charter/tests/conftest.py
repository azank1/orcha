"""Make ``charter`` and ``emerge_node`` importable regardless of pytest rootdir.

The package pyproject sets ``pythonpath`` for standalone runs
(``uv run pytest common/charter/tests``); this conftest covers combined runs
from the repo root where the root-level rootdir wins and ini pythonpath is
not applied.
"""

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _PACKAGE_ROOT.parents[1]

for path in (_PACKAGE_ROOT / "src", _REPO_ROOT / "node" / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
