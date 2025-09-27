import os
import sys
from typing import Any, Dict
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv

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
            # For acceptance, we need to validate first to get the canonical price
            # then use that for acceptance
            # IMPORTANT: Use original menu price (6.99) for validation, not canonical price (7.41)
            item_data = {
                "category": params.get("category"),
                "item": params.get("item"),
                "size": params.get("size"), 
                "price": 6.99  # Use original menu price for validation
            }
            customer = params.get("customer")
            
            # First validate to get the proper payload structure and canonical price
            validation_result = await run_in_threadpool(_ORDER_SVC.validate_order, item_data, customer)
            
            if not validation_result.get("success"):
                return {
                    "error": {
                        "code": -32002,
                        "message": "Validation failed before acceptance",
                        "data": {
                            "status": validation_result.get("status"),
                            "raw": validation_result.get("raw", "")[:300]
                        }
                    }
                }
            
            # Use canonical price from validation response
            canonical_price = validation_result.get("canonical_price")
            validation_data = validation_result.get("data")
            validation_payload = validation_result.get("payload")
            
            if not canonical_price and validation_data:
                canonical_price = validation_data.get("price")
            
            # Accept using the validation payload and canonical price
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
                                "validation_canonical_price": canonical_price,
                                "validation_data_price": validation_data.get("price") if validation_data else None,
                                "final_price_used": canonical_price,
                                "validation_success": validation_result.get("success"),
                                "validation_status": validation_result.get("status"),
                                "validation_payload_type": validation_payload.get("type") if validation_payload else None,
                                "acceptance_payload_type": acceptance_payload.get("type"),
                                "acceptance_payload_price": acceptance_payload.get("price"),
                                "validation_external_ref": validation_payload.get("externalRef") if validation_payload else None,
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
