import os
import sys
import time
import random
import re
import logging
from typing import Any, Dict
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Add parent directory to Python path to import P2A
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ Import working P2A services
from P2A.core.menu_service import MenuService
from P2A.core.order_service import OrderService

# ---- Service singletons ----
def _build_services():
    # P2A services read from environment variables directly
    # so we just need to instantiate them
    menu_service = MenuService()
    order_service = OrderService()
    
    return menu_service, order_service

_MENU_SVC, _ORDER_SVC = _build_services()

# ---- JSON-RPC dispatcher ----
async def handle_rpc(request: Dict[str, Any]) -> Dict[str, Any]:
    method: str = request.get("method", "")
    params: Dict[str, Any] = request.get("params") or {}

    try:
        if method == "foodtec.export_menu":
            order_type = params.get("orderType", "Pickup")
            result = await run_in_threadpool(_MENU_SVC.export_menu, order_type)
            
            # Check if P2A service call was successful
            if not result.get("success"):
                return {
                    "error": {
                        "code": -32000,
                        "message": "Menu export failed",
                        "data": {
                            "status": result.get("status"),
                            "raw": result.get("raw", "")[:300]
                        }
                    }
                }
            return result

        elif method == "foodtec.validate_order":
            # P2A validate_order expects item_data dict
            item_data = {
                "category": params.get("category"),
                "item": params.get("item"), 
                "size": params.get("size"),
                "price": params.get("price")
            }
            customer = params.get("customer")
            result = await run_in_threadpool(_ORDER_SVC.validate_order, item_data, customer)
            
            # Check if P2A service call was successful
            if not result.get("success"):
                return {
                    "error": {
                        "code": -32001,
                        "message": "Order validation failed",
                        "data": {
                            "status": result.get("status"),
                            "raw": result.get("raw", "")[:300]
                        }
                    }
                }
            return result

        elif method == "foodtec.accept_order":
            # TODO: Refactor to vendor-agnostic orders.submit() once multi-vendor support is added
            # For acceptance, UI should send BOTH menuPrice and canonicalPrice
            # menuPrice: original price without tax (goes in item sellingPrice)
            # canonicalPrice: price WITH tax from validation (goes to accept_order method)
            menu_price = params.get("menuPrice") or params.get("price")  # Fallback for backwards compat
            canonical_price = params.get("canonicalPrice") or params.get("price")
            
            # Runtime invariant checks to prevent tax-on-tax regression
            if not menu_price or not canonical_price:
                return {
                    "error": {
                        "code": -32002,
                        "message": "Both menuPrice and canonicalPrice are required for acceptance"
                    }
                }
            
            # Validate prices
            try:
                mp = float(menu_price)
                cp = float(canonical_price)
                assert mp >= 0 and cp >= 0, "Prices must be >= 0"
                assert cp >= mp, f"canonicalPrice ({cp}) must be >= menuPrice ({mp})"
            except (ValueError, AssertionError) as e:
                return {
                    "error": {
                        "code": -32003,
                        "message": f"Price validation failed: {str(e)}"
                    }
                }
            
            customer = params.get("customer", {})
            
            # Validate phone format (XXX-XXX-XXXX)
            import re
            phone = customer.get("phone", "")
            if not re.match(r"^\d{3}-\d{3}-\d{4}$", phone):
                return {
                    "error": {
                        "code": -32004,
                        "message": f"Invalid phone format: {phone}. Expected XXX-XXX-XXXX"
                    }
                }
            
            # Build the validation-style payload (what accept_order expects)
            external_ref = params.get("externalRef") or f"ext-{int(time.time())}-{random.randint(1000, 9999)}"
            validation_payload = {
                "type": "To Go",  # Will be converted to "Pickup" in accept_order
                "source": "Voice",
                "externalRef": external_ref,
                "customer": customer,
                "items": [{
                    "item": params.get("item"),
                    "category": params.get("category"),
                    "size": params.get("size"),
                    "quantity": 1,
                    "externalRef": f"{external_ref}-i1",
                    "sellingPrice": menu_price  # Use MENU price (without tax) in item
                }]
            }
            
            # Log acceptance attempt (no PII except phone pattern validation already done)
            logger.info({
                "evt": "accept.submit",
                "itemPrice": menu_price,
                "orderPrice": canonical_price,
                "externalRef": external_ref,
                "idem": params.get("idem", "")
            })
            
            # Accept using the payload and canonical price (WITH tax at order level)
            # CRITICAL: Do NOT re-validate here to avoid tax-on-tax
            result = await run_in_threadpool(_ORDER_SVC.accept_order, validation_payload, canonical_price)
            
            # Check if P2A service call was successful
            if not result.get("success"):
                acceptance_payload = result.get("payload", {})
                
                return {
                    "error": {
                        "code": -32003,
                        "message": "Order acceptance failed",
                        "data": {
                            "status": result.get("status"),
                            "raw": result.get("raw", "")[:300],
                            "debug": {
                                "canonical_price_used": canonical_price,
                                "validation_payload_type": validation_payload.get("type"),
                                "acceptance_payload_type": acceptance_payload.get("type"),
                                "acceptance_payload_price": acceptance_payload.get("price"),
                                "validation_external_ref": validation_payload.get("externalRef"),
                                "acceptance_external_ref": acceptance_payload.get("externalRef"),
                                "item_selling_price": acceptance_payload.get("items", [{}])[0].get("sellingPrice") if acceptance_payload.get("items") else None
                            }
                        }
                    }
                }
            return result

        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        return {
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }
