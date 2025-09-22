from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

from api_client_ft import ApiClientFT


class MenuServiceFT:
    """FoodTec menu service mapping to Engine schema shape.

    Output shape:
      {
        menu: {
          categories: [
            { id, name, items: [ { sku, name, price } ] }
          ]
        },
        page, page_size, total
      }
    """

    def __init__(self, client: ApiClientFT) -> None:
        self.client = client
        self.menu_path = os.getenv("FOODTEC_MENU_PATH", "/menu/export")

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

    def _paginate(self, categories: List[Dict[str, Any]], page: Optional[int], page_size: Optional[int]) -> (List[Dict[str, Any]], int, int, int):
        # flatten items while preserving category grouping in output
        # For simplicity, paginate over categories list, not per-category items
        total = len(categories)
        if not page or not page_size:
            return categories, 1, total or 0, total
        p = max(1, int(page))
        ps = max(1, int(page_size))
        start = (p - 1) * ps
        end = start + ps
        return categories[start:end], p, ps, total

    def _map_vendor_menu(self, vendor_json: Any) -> List[Dict[str, Any]]:
        # Attempt to map common FT-ish shape to target categories/items
        # Expecting something like categories array with nested items; otherwise perform best-effort mapping
        categories_out: List[Dict[str, Any]] = []
        if isinstance(vendor_json, dict):
            cats = vendor_json.get("categories") or vendor_json.get("menu", {}).get("categories")
            if isinstance(cats, list):
                for c in cats:
                    cid = c.get("id") or c.get("code") or c.get("name")
                    cname = c.get("name") or str(cid)
                    items_out: List[Dict[str, Any]] = []
                    vitems = c.get("items") or []
                    if isinstance(vitems, list):
                        for it in vitems:
                            sku = it.get("sku") or it.get("code") or it.get("id") or it.get("name")
                            name = it.get("name") or str(sku)
                            price = None
                            pr = it.get("price")
                            if isinstance(pr, (int, float)):
                                price = float(pr)
                            elif isinstance(pr, dict) and "amount" in pr:
                                price = float(pr.get("amount", 0)) / (100 if pr.get("currency") in ("USD", "CAD", "EUR") else 1)
                            items_out.append({"sku": sku, "name": name, "price": price})
                    categories_out.append({"id": cid, "name": cname, "items": items_out})
        return categories_out

    def export_menu(
        self,
        store_id: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        q: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Build query
        params = {"store_id": store_id} if store_id else {}
        status, data = self.client.get(self.menu_path, params=params)
        # Map vendor to target shape
        categories = self._map_vendor_menu(data)
        categories = self._filter_search(categories, q)
        paged, p, ps, total = self._paginate(categories, page, page_size)
        return {
            "menu": {"categories": paged},
            "page": p,
            "page_size": ps,
            "total": total,
            "_upstream_status": status,
        }
