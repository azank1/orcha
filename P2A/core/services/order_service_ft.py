from __future__ import annotations
import os
import logging
from typing import Any, Dict

from ..api_clients.api_client_ft import ApiClientFT

logger = logging.getLogger(__name__)


class OrderServiceFT:
    """FoodTec order service with validation and acceptance"""
    
    def __init__(self, client: ApiClientFT) -> None:
        self.client = client
        self.validate_path = os.getenv("FOODTEC_VALIDATE_PATH", "/validateOrder")
        self.accept_path = os.getenv("FOODTEC_ACCEPT_PATH", "/acceptOrder")
        self.validate_pass = os.getenv("FOODTEC_VALIDATE_PASS")
        self.accept_pass = os.getenv("FOODTEC_ACCEPT_PASS")
        logger.info("[FoodTec] OrderService initialized with paths: validate=%s, accept=%s", 
                   self.validate_path, self.accept_path)

    def _ok(self, d: Dict[str, Any]) -> Dict[str, Any]:
        d.setdefault("ok", True)
        return d

    def _err(self, code: str, message: str, upstream_status: int, details: Any = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": False, "code": code, "message": message, "upstream_status": upstream_status}
        if details is not None:
            out["details"] = details
        return out

    def validate_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order against FoodTec endpoint"""
        logger.info("[FoodTec] Validating order with %d items", len(payload.get("items", [])))
        
        try:
            status, data = self.client.post(self.validate_path, json=payload, password=self.validate_pass)
        except Exception as exc:
            logger.exception("[FoodTec] Failed to validate order: %s", exc)
            return self._err("UPSTREAM_ERROR", "Failed to connect to FoodTec", 0, details=str(exc))
            
        if 200 <= status < 300 and isinstance(data, dict):
            # Normalize successful response
            out: Dict[str, Any] = {"ok": True}
            if "draft" in data:
                out["draft"] = data["draft"]
            if "warnings" in data or "issues" in data:
                out["issues"] = data.get("issues") or data.get("warnings")
            logger.info("[FoodTec] Order validation successful")
            return out
            
        # Error mapping
        msg = data.get("message") if isinstance(data, dict) else str(data)
        code = data.get("code") if isinstance(data, dict) else "UPSTREAM_ERROR"
        logger.warning("[FoodTec] Order validation failed: %s (status %d)", msg, status)
        return self._err(str(code), msg or "Validation failed", status, details=data)

    def accept_order(self, payload: Dict[str, Any], idem: str) -> Dict[str, Any]:
        """Accept order with idempotency support"""
        logger.info("[FoodTec] Accepting order with idempotency key: %s", idem)
        
        try:
            headers = {"Idempotency-Key": str(idem)} if idem else None
            status, data = self.client.post(self.accept_path, json=payload, headers=headers, password=self.accept_pass)
        except Exception as exc:
            logger.exception("[FoodTec] Failed to accept order: %s", exc)
            return self._err("UPSTREAM_ERROR", "Failed to connect to FoodTec", 0, details=str(exc))
            
        if 200 <= status < 300 and isinstance(data, dict):
            order_id = data.get("order_id") or data.get("id") or data.get("reference")
            eta = data.get("eta") or data.get("eta_minutes")
            out: Dict[str, Any] = {"ok": True, "order_id": order_id, "idem": idem}
            if eta is not None:
                out["eta"] = eta
            logger.info("[FoodTec] Order accepted successfully: order_id=%s", order_id)
            return out
            
        msg = data.get("message") if isinstance(data, dict) else str(data)
        code = data.get("code") if isinstance(data, dict) else "UPSTREAM_ERROR"
        logger.warning("[FoodTec] Order acceptance failed: %s (status %d)", msg, status)
        return self._err(str(code), msg or "Accept failed", status, details=data)
        return self._err(str(code), msg or "Accept failed", status, details=data)
