from __future__ import annotations
from typing import Any, Callable, List, Optional, Union

from mcp.search.indexer import MenuIndexer


class SearchEngine:
    def __init__(self, categories_or_indexer: Union[List[Any], MenuIndexer], reranker: Optional[Callable[[List[Any]], List[Any]]] = None):
        if isinstance(categories_or_indexer, MenuIndexer):
            self.indexer = categories_or_indexer
        else:
            self.indexer = MenuIndexer(categories_or_indexer)
        self.reranker = reranker

    def search(self, query: str, top_k: int = 5, rerank_top_n: Optional[int] = None, use_reranker: bool = False):
        try:
            results = self.indexer.search(query, k=top_k)
            if self.reranker and use_reranker and results:
                n = rerank_top_n or len(results)
                head = results[:n]
                tail = results[n:]
                # Call rerank method if it's a SemanticReranker, otherwise assume it's a callable
                if hasattr(self.reranker, 'rerank'):
                    head = self.reranker.rerank(query, head)
                else:
                    head = self.reranker(head, query)
                return head + tail
            return results
        except Exception as e:
            return [{"error": str(e)}]
