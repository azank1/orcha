"""
Semantic reranker abstraction. Uses sentence-transformers when available.
Falls back to identity reranker if dependencies are missing.
"""
from __future__ import annotations

from typing import Any, List, Optional, Sequence

try:
    from sentence_transformers import SentenceTransformer, util as st_util  # type: ignore
    _HAS_ST = True
except Exception:
    SentenceTransformer = None  # type: ignore
    st_util = None  # type: ignore
    _HAS_ST = False


class SemanticReranker:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._enabled = _HAS_ST
        self._model_name = model_name
        self._model: Optional[Any] = None

    def _ensure_model(self) -> None:
        if not self._enabled:
            return
        if self._model is None and SentenceTransformer is not None:
            self._model = SentenceTransformer(self._model_name)

    def rerank(self, query: str, items: Sequence[Any], text_getter=lambda x: getattr(x, "item", str(x))) -> List[Any]:
        if not self._enabled:
            return list(items)
        if not items:
            return list(items)
        self._ensure_model()
        assert self._model is not None
        texts = [text_getter(x) for x in items]
        q_emb = self._model.encode([query], convert_to_tensor=True)
        d_emb = self._model.encode(texts, convert_to_tensor=True)
        scores = st_util.cos_sim(q_emb, d_emb)[0].cpu().tolist()
        ranked = sorted(zip(items, scores), key=lambda p: p[1], reverse=True)
        return [x for x, _ in ranked]

    @property
    def enabled(self) -> bool:
        return self._enabled


__all__ = ["SemanticReranker"]
