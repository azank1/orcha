from __future__ import annotations
import os
from typing import Any, Dict

from api_client_ft import ApiClientFT


class OrderServiceFT:
    def __init__(self, client: ApiClientFT) -> None:
        self.client = client
        self.validate_path = os.getenv("FOODTEC_VALIDATE_PATH", "/order/validate")
        self.accept_path = os.getenv("FOODTEC_ACCEPT_PATH", "/order/accept")

    def _ok(self, d: Dict[str, Any]) -> Dict[str, Any]:
        d.setdefault("ok", True)
        return d

    def _err(self, code: str, message: str, upstream_status: int, details: Any = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": False, "code": code, "message": message, "upstream_status": upstream_status}
        if details is not None:
            out["details"] = details
        return out

    def validate_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        status, data = self.client.post(self.validate_path, json=payload)
        if 200 <= status < 300 and isinstance(data, dict):
            # Normalize: { ok, draft?, issues? }
            out: Dict[str, Any] = {"ok": True}
            if "draft" in data:
                out["draft"] = data["draft"]
            if "warnings" in data or "issues" in data:
                out["issues"] = data.get("issues") or data.get("warnings")
            return out
        # Error mapping
        msg = data.get("message") if isinstance(data, dict) else str(data)
        code = data.get("code") if isinstance(data, dict) else "UPSTREAM_ERROR"
        return self._err(str(code), msg or "Validation failed", status, details=data)

    def accept_order(self, payload: Dict[str, Any], idem: str) -> Dict[str, Any]:
        # Pass idempotency key via header in client; we embed it in payload here and let caller set header if needed.
        headers = {"Idempotency-Key": str(idem)} if idem else None
        status, data = self.client.post(self.accept_path, json=payload, headers=headers)
        if 200 <= status < 300 and isinstance(data, dict):
            order_id = data.get("order_id") or data.get("id") or data.get("reference")
            eta = data.get("eta") or data.get("eta_minutes")
            out: Dict[str, Any] = {"ok": True, "order_id": order_id, "idem": idem}
            if eta is not None:
                out["eta"] = eta
            return out
        msg = data.get("message") if isinstance(data, dict) else str(data)
        code = data.get("code") if isinstance(data, dict) else "UPSTREAM_ERROR"
        return self._err(str(code), msg or "Accept failed", status, details=data)
