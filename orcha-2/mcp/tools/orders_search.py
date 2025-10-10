from typing import Optional

from mcp.adapters import get_pos_adapter, VendorType
from mcp.search.engine import SearchEngine
from mcp.search.rerank import SemanticReranker


def _convert_menu_dict_to_objects(menu_dict):
    """Convert a dict-based menu (as returned by mock adapter) into simple objects.

    Expected shape: { 'categories': [ { 'category': str, 'items': [ { 'item': str, ... } ] } ] }
    Returns a list of category-like objects with .items that each have .item.
    """
    class _Item:
        def __init__(self, d):
            self.item = d.get("item") or d.get("name") or ""
            self.category = d.get("category")

    class _Category:
        def __init__(self, d):
            self.category = d.get("category") or d.get("name") or "Uncategorised"
            self.items = [_Item(x) for x in (d.get("items") or [])]

    categories = [
        _Category(c) for c in (menu_dict.get("categories") or [])
    ]
    return categories


async def invoke(query: str, vendor: str = "foodtec", top_k: int = 5, use_semantic: bool = False, rerank_top_n: Optional[int] = None):
    adapter = get_pos_adapter(VendorType(vendor.lower()))
    menu = await adapter.fetch_menu("default")

    # Support both object-style and dict-style menus
    categories = getattr(menu, "categories", None)
    if categories is None and isinstance(menu, dict):
        categories = _convert_menu_dict_to_objects(menu)

    reranker = None
    if use_semantic:
        reranker = SemanticReranker().rerank

    engine = SearchEngine(categories, reranker=reranker)
    results = engine.search(query, top_k=top_k, rerank_top_n=rerank_top_n)

    # Support both object and dict outputs uniformly
    normalized = []
    for item in results:
        if hasattr(item, "model_dump"):
            normalized.append(item.model_dump())
        elif hasattr(item, "item"):
            normalized.append({"item": getattr(item, "item", "")})
        else:
            normalized.append(item)
    return normalized


# Backwards-compatible alias used by some tests
search_orders = invoke
