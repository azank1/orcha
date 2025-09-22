from __future__ import annotations
from typing import Any, Dict


class OrderServiceMock:
    def validate_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        items = (payload or {}).get("items") or (payload or {}).get("draft", {}).get("items")
        if not isinstance(items, list) or not items:
            return {"ok": False, "code": "VALIDATION_ERROR", "message": "No items provided", "upstream_status": 422}
        return {"ok": True, "draft": payload, "issues": []}

    def accept_order(self, payload: Dict[str, Any], idem: str) -> Dict[str, Any]:
        return {"ok": True, "order_id": f"MOCK-{idem}", "idem": idem}
