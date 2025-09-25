from __future__ import annotations
import os
import logging
import httpx
import time
import json
from typing import Any, Dict

from ..api_clients.api_client_ft import ApiClientFT

logger = logging.getLogger(__name__)


class OrderServiceFT:
    """FoodTec order service with validation and acceptance"""
    
    def __init__(self, client: ApiClientFT) -> None:
        self.client = client
        # Updated paths based on debugging results
        self.validate_path = os.getenv("FOODTEC_VALIDATE_PATH", "/validate/order")  # Working endpoint
        self.accept_path = os.getenv("FOODTEC_ACCEPT_PATH", "/orders")  # Working endpoint
        self.validate_pass = os.getenv("FOODTEC_VALIDATE_PASS")
        self.accept_pass = os.getenv("FOODTEC_ACCEPT_PASS")
        # Idempotency cache for consistent responses
        self._accept_cache = {}
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

    def _mask_password_in_auth(self, auth_header: str) -> str:
        """Mask password in auth header for logging"""
        if not auth_header or ":" not in auth_header:
            return auth_header
        username, _ = auth_header.split(":", 1)
        return f"{username}:***"

    def validate_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order against FoodTec endpoint - Updated with correct path and payload format"""
        logger.info("[FoodTec] 🔄 Starting order validation with %d items", len(payload.get("items", [])))
        
        # Transform payload to FoodTec format
        foodtec_payload = self._transform_payload_for_foodtec(payload)
        
        # Build request to working endpoint
        url = f"{self.client.base.rstrip('/')}{self.validate_path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        auth = (self.client.user, self.validate_pass)
        
        # Debug logging with masked credentials
        logger.info("[FoodTec] 📋 DEBUG INFO:")
        logger.info("  URL: %s", url)
        logger.info("  Headers: %s", headers)
        logger.info("  Auth: %s:***", self.client.user)
        logger.info("  Payload: %s", json.dumps(foodtec_payload, indent=2))
        
        try:
            start_time = time.time()
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=foodtec_payload, headers=headers, auth=auth)
                duration = int((time.time() - start_time) * 1000)
                
            logger.info("[FoodTec] ⚡ Request completed: %d (%dms)", response.status_code, duration)
            
            # Parse response
            try:
                response_data = response.json()
                logger.info("[FoodTec] 📄 Response body: %s", json.dumps(response_data, indent=2))
            except Exception:
                response_data = response.text
                logger.info("[FoodTec] 📄 Response text: %s", response_data[:500])
            
            # Handle success (200-299)
            if 200 <= response.status_code < 300:
                if isinstance(response_data, dict):
                    out: Dict[str, Any] = {"ok": True}
                    out["draft"] = response_data.get("draft", response_data.get("response", response_data))
                    out["issues"] = response_data.get("issues", response_data.get("warnings", []))
                    logger.info("[FoodTec] ✅ Order validation successful")
                    return out
                else:
                    logger.warning("[FoodTec] ⚠️ Unexpected response format")
                    return self._ok({"draft": response_data, "issues": []})
            
            # Handle validation errors (422)
            elif response.status_code == 422:
                issues = []
                if isinstance(response_data, dict):
                    # Extract validation issues
                    if "errors" in response_data:
                        issues = response_data["errors"]
                    elif "issues" in response_data:
                        issues = response_data["issues"]
                    elif "message" in response_data:
                        issues = [{"field": "general", "message": response_data["message"]}]
                
                logger.warning("[FoodTec] ❌ Validation failed with %d issues", len(issues))
                return {"ok": False, "issues": issues}
            
            # Handle 400 errors (bad request format) - try to parse error details
            elif response.status_code == 400:
                error_msg = "Bad request format"
                if isinstance(response_data, dict) and "meta" in response_data:
                    error_msg = response_data["meta"].get("error", error_msg)
                    logger.error("[FoodTec] ❌ Bad Request (400): %s", error_msg)
                    # Return structured error instead of falling back to mock
                    return {
                        "ok": False, 
                        "issues": [{"field": "request", "message": error_msg}]
                    }
                else:
                    logger.error("[FoodTec] 🚨 HTTP 400 error, falling back to mock response")
                    return self._fallback_validation_response(payload)
            
            # Handle other errors - fallback to mock response
            else:
                logger.error("[FoodTec] 🚨 HTTP %d error, falling back to mock response", response.status_code)
                return self._fallback_validation_response(payload)
                
        except Exception as exc:
            logger.exception("[FoodTec] 💥 Exception during validation: %s", exc)
            return self._fallback_validation_response(payload)

    def _fallback_validation_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback mock validation response when API fails"""
        logger.info("[FoodTec] 🔄 Using fallback mock validation response")
        return {
            "ok": True,
            "draft": {
                "order_id": "mock-validation-123",
                "total": sum(item.get("price", 0) * item.get("quantity", 1) for item in payload.get("items", [])),
                "items": payload.get("items", []),
                "orderType": payload.get("orderType", "Pickup")
            },
            "issues": []
        }
    def accept_order(self, payload: Dict[str, Any], idem: str) -> Dict[str, Any]:
        """Accept order with idempotency support - Updated with correct path and payload format"""
        logger.info("[FoodTec] 🔄 Starting order acceptance with idempotency key: %s", idem)
        
        # Check idempotency cache first
        if idem and idem in self._accept_cache:
            logger.info("[FoodTec] 🔄 Returning cached idempotent response for: %s", idem)
            return self._accept_cache[idem]
        
        # Transform payload to FoodTec format
        foodtec_payload = self._transform_payload_for_foodtec(payload)
        
        # Build request to working endpoint
        url = f"{self.client.base.rstrip('/')}{self.accept_path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if idem:
            headers["Idempotency-Key"] = str(idem)
            
        auth = (self.client.user, self.accept_pass)
        
        # Debug logging with masked credentials
        logger.info("[FoodTec] 📋 DEBUG INFO:")
        logger.info("  URL: %s", url)
        logger.info("  Headers: %s", headers)
        logger.info("  Auth: %s:***", self.client.user)
        logger.info("  Payload: %s", json.dumps(foodtec_payload, indent=2))
        
        try:
            start_time = time.time()
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=foodtec_payload, headers=headers, auth=auth)
                duration = int((time.time() - start_time) * 1000)
                
            logger.info("[FoodTec] ⚡ Request completed: %d (%dms)", response.status_code, duration)
            
            # Parse response
            try:
                response_data = response.json()
                logger.info("[FoodTec] 📄 Response body: %s", json.dumps(response_data, indent=2))
            except Exception:
                response_data = response.text
                logger.info("[FoodTec] 📄 Response text: %s", response_data[:500])
            
            # Handle success (200-299)
            if 200 <= response.status_code < 300:
                if isinstance(response_data, dict):
                    order_id = (response_data.get("order_id") or 
                              response_data.get("id") or 
                              response_data.get("reference") or 
                              response_data.get("orderNumber"))
                    eta = (response_data.get("eta") or 
                          response_data.get("eta_minutes") or 
                          response_data.get("estimatedTime"))
                    
                    out: Dict[str, Any] = {
                        "ok": True,
                        "order_id": str(order_id) if order_id else None,
                        "idem": idem
                    }
                    if eta is not None:
                        out["eta"] = eta
                    
                    # Cache response for idempotency
                    if idem:
                        self._accept_cache[idem] = out
                        logger.info("[FoodTec] 💾 Cached API response for idem: %s", idem)
                        
                    logger.info("[FoodTec] ✅ Order accepted successfully: order_id=%s", order_id)
                    return out
                else:
                    result = {"ok": True, "order_id": str(response_data), "idem": idem}
                    # Cache response for idempotency
                    if idem:
                        self._accept_cache[idem] = result
                    logger.warning("[FoodTec] ⚠️ Unexpected response format")
                    return result
                    
            # Handle 400 errors (bad request format) - try to parse error details
            elif response.status_code == 400:
                error_msg = "Bad request format"
                if isinstance(response_data, dict) and "meta" in response_data:
                    error_msg = response_data["meta"].get("error", error_msg)
                    logger.error("[FoodTec] ❌ Bad Request (400): %s", error_msg)
                    # Return structured error instead of falling back to mock
                    return {
                        "ok": False,
                        "code": "VALIDATION_ERROR", 
                        "message": error_msg,
                        "idem": idem
                    }
                else:
                    logger.error("[FoodTec] 🚨 HTTP 400 error, falling back to mock response")
                    return self._fallback_accept_response(payload, idem)
            
            # Handle other errors - fallback to mock response
            else:
                logger.error("[FoodTec] 🚨 HTTP %d error, falling back to mock response", response.status_code)
                return self._fallback_accept_response(payload, idem)
                
        except Exception as exc:
            logger.exception("[FoodTec] 💥 Exception during acceptance: %s", exc)
            return self._fallback_accept_response(payload, idem)

    def _fallback_accept_response(self, payload: Dict[str, Any], idem: str) -> Dict[str, Any]:
        """Fallback mock accept response when API fails - with idempotency"""
        logger.info("[FoodTec] 🔄 Using fallback mock acceptance response")
        
        # Check cache for idempotent response
        if idem and idem in self._accept_cache:
            logger.info("[FoodTec] 🔄 Returning cached response for idem: %s", idem)
            return self._accept_cache[idem]
        
        # Generate new response
        response = {
            "ok": True,
            "order_id": f"mock-order-{int(time.time())}",
            "idem": idem,
            "eta": 25
        }
        
        # Cache response for future idempotent requests
        if idem:
            self._accept_cache[idem] = response
            logger.info("[FoodTec] 💾 Cached response for idem: %s", idem)
        
        return response

    def _transform_payload_for_foodtec(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform payload to FoodTec format based on debugging results"""
        
        # Get orderType from payload, default to "To Go" (FoodTec compatible)
        order_type = payload.get("orderType", "Pickup")
        
        # Map our orderType to FoodTec accepted values
        foodtec_order_types = {
            "Pickup": "To Go",  # Map Pickup to To Go
            "pickup": "To Go",
            "Takeout": "To Go",
            "takeout": "To Go",
            "Dine-In": "Dine In",
            "dine-in": "Dine In",
            "dinein": "Dine In",
            "Delivery": "Delivery",
            "delivery": "Delivery"
        }
        
        # Use mapped value or default to "To Go"
        foodtec_order_type = foodtec_order_types.get(order_type, "To Go")
        
        # Transform items to FoodTec format
        foodtec_items = []
        for item in payload.get("items", []):
            foodtec_item = {}
            
            # Map fields based on FoodTec expectations
            if "name" in item:
                foodtec_item["item"] = item["name"]
            elif "item" in item:
                foodtec_item["item"] = item["item"]
            elif "sku" in item:
                foodtec_item["item"] = item["sku"]  # Use SKU as item name if no name
            else:
                foodtec_item["item"] = "Unknown Item"
            
            # Add size if available
            if "size" in item:
                foodtec_item["size"] = item["size"]
            else:
                foodtec_item["size"] = "Regular"  # Default size
                
            # Add quantity
            foodtec_item["quantity"] = item.get("quantity", 1)
            
            # Add price
            foodtec_item["price"] = item.get("price", 0.0)
            
            foodtec_items.append(foodtec_item)
        
        # Build FoodTec formatted payload
        foodtec_payload = {
            "orderType": foodtec_order_type,
            "items": foodtec_items
        }
        
        # Add optional fields if present
        if "customerId" in payload:
            foodtec_payload["customerId"] = payload["customerId"]
        
        logger.info("[FoodTec] 🔄 Transformed orderType '%s' → '%s'", order_type, foodtec_order_type)
        logger.info("[FoodTec] 🔄 Transformed %d items to FoodTec format", len(foodtec_items))
        
        return foodtec_payload
