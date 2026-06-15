"""Configure the common.llm namespace mock for unit tests in this package.

Unit tests here test IOResolver and DependencyRefiner in isolation.
The common.llm.src.LLMProvider abstract class is mocked so that the
modules can be imported without the full workspace on sys.path.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from types import ModuleType
from unittest.mock import MagicMock


def _install_common_llm_mock() -> None:
    """Inject a minimal common.llm.src stub into sys.modules if not present."""
    if "common" in sys.modules and not isinstance(sys.modules["common"], MagicMock):
        # Real package present — nothing to do
        return

    class _LLMProvider(ABC):
        @abstractmethod
        async def complete(self, model: str, messages: list, **kwargs) -> str: ...
        @abstractmethod
        async def embed(self, text: str, model: str) -> list[float]: ...

    llm_src_mod = ModuleType("common.llm.src")
    llm_src_mod.LLMProvider = _LLMProvider  # type: ignore[attr-defined]

    llm_mod = ModuleType("common.llm")
    llm_mod.src = llm_src_mod  # type: ignore[attr-defined]

    common_mod = ModuleType("common")
    common_mod.llm = llm_mod  # type: ignore[attr-defined]

    sys.modules.setdefault("common", common_mod)
    sys.modules.setdefault("common.llm", llm_mod)
    sys.modules.setdefault("common.llm.src", llm_src_mod)


_install_common_llm_mock()
