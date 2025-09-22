from __future__ import annotations
from typing import Any, Dict, List, Optional

from core.services.menu.menu_service_mock import MenuServiceMock


class MenuServiceExportMock:
    def __init__(self) -> None:
        self._mock = MenuServiceMock()

    def _filter_search(self, categories: List[Dict[str, Any]], q: Optional[str]) -> List[Dict[str, Any]]:
        if not q:
            return categories
        ql = q.lower()
        out: List[Dict[str, Any]] = []
        for c in categories:
            items = [it for it in c.get("items", []) if ql in str(it.get("name", "")).lower() or ql in str(it.get("sku", "")).lower()]
            if items:
                out.append({"id": c.get("id"), "name": c.get("name"), "items": items})
        return out

    def _paginate(self, categories: List[Dict[str, Any]], page: Optional[int], page_size: Optional[int]):
        total = len(categories)
        if not page or not page_size:
            # Default to first page with page_size 50
            ps = 50
            return categories[:ps], 1, ps, total
        p = max(1, int(page))
        ps = max(1, int(page_size))
        start = (p - 1) * ps
        end = start + ps
        return categories[start:end], p, ps, total

    async def export_menu(self, store_id: str, page: Optional[int] = None, page_size: Optional[int] = None, q: Optional[str] = None) -> Dict[str, Any]:
        # Build a simple catalog from the mock menu service for a default orderType
        orderType = "Pickup"

        cats = await self._mock.get_categories(orderType)
        out: List[Dict[str, Any]] = []
        for cname in cats:
            items = await self._mock.get_category_items(cname, orderType)
            mapped = []
            for iname in items:
                sku = f"{cname}:{iname}".upper().replace(" ", "_")
                mapped.append({"sku": sku, "name": iname, "price": 10.0})
            out.append({"id": cname.lower(), "name": cname, "items": mapped})

        categories = self._filter_search(out, q)
        paged, p, ps, total = self._paginate(categories, page, page_size)
        return {"menu": {"categories": paged}, "page": p, "page_size": ps, "total": total}
