from __future__ import annotations

from typing import Protocol, Any, List, Dict
from mcp.search.indexer import MenuIndexer
from mcp.search.engine import SearchEngine
from mcp.models.base import Category, MenuItem, SizePrice


class MenuProvider(Protocol):
    async def get_categories(self, order_type: str = "pickup") -> List[Any]: ...
    async def search(self, query: str, k: int = 8, order_type: str = "pickup") -> List[Dict]: ...


class DemoMenuProvider:
    def __init__(self) -> None:
        self._categories = [
            Category(category="Pizza", items=[
                MenuItem(item="Margherita Pizza", sizePrices=[SizePrice(size="Regular", price=12.99)], category="Pizza"),
                MenuItem(item="Pepperoni Pizza", sizePrices=[SizePrice(size="Regular", price=14.99)], category="Pizza"),
                MenuItem(item="Hawaiian Pizza", sizePrices=[SizePrice(size="Regular", price=15.99)], category="Pizza"),
            ])
        ]
        # Build persistent engine/indexer for provider lifetime
        indexer = MenuIndexer(self._categories)
        self._engine = SearchEngine(indexer)

    async def get_categories(self, order_type: str = "pickup") -> List[Any]:
        return self._categories

    async def search(self, query: str, k: int = 8, order_type: str = "pickup") -> List[Dict]:
        results = self._engine.search(query, top_k=k)
        # If engine surfaced an error as a dict, raise a clear exception
        if results and isinstance(results[0], dict) and "error" in results[0]:
            raise RuntimeError(f"search_engine_error: {results[0]['error']}")
        out: List[Dict] = []
        for item in results:
            # Skip unexpected payloads defensively
            if not hasattr(item, "item"):
                continue
            price = item.sizePrices[0].price if getattr(item, "sizePrices", None) else None
            out.append({
                "name": item.item,
                "category": getattr(item, "category", "") or "",
                "price": price,
                "sku": getattr(item, "code", None),
            })
        return out
