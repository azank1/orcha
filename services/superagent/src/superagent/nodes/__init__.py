"""SuperAgent graph nodes.

_registry is used to inject module-level singletons (pnd_client) without
circular imports.  main.py calls _registry["pnd_client"] = instance at boot.
"""

from typing import Any

_registry: dict[str, Any] = {}
