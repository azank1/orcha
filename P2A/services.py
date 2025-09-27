"""
Business logic services for FoodTec integration.
Handles payload construction and orchestration following documented working patterns.
"""
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from .client import FoodTecClient

class MenuService:
    """Menu processing and item selection service."""
    
    def __init__(self, client: FoodTecClient):
        self.client = client
    
    def export_menu(self, order_type: str = "Pickup") -> Dict[str, Any]:
        """Export menu with processed response."""
        status, data, raw = self.client.get_menu(order_type)
        
        return {
            "status": status,
            "data": data,
            "success": 200 <= status < 300 and data is not None,
            "raw": raw[:500] if raw else ""  # Truncate for readability
        }
    
    def pick_first_item(self, menu_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Pick first available item from menu data.
        Returns item with category, item name, size, and price.
        """
        if not isinstance(menu_data, list):
            return None
            
        for category in menu_data:
            items = category.get("items", [])
            for item in items:
                size_prices = item.get("sizePrices", [])
                if size_prices:
                    size_price = size_prices[0]
                    return {
                        "category": category.get("category", "Unknown"),
                        "item": item.get("item", "Unknown"),
                        "size": size_price.get("size", "Regular"),
                        "price": size_price.get("price", 0.0)
                    }
        return None


class OrderService:
    """Order processing service for validation and acceptance."""
    
    def __init__(self, client: FoodTecClient):
        self.client = client
    
    def _generate_external_ref(self) -> str:
        """Generate unique external reference."""
        return f"ext-{int(time.time())}-{random.randint(1000, 9999)}"
    
    def build_validation_payload(self, item_data: Dict[str, Any], customer: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build validation payload following FoodTec v1 schema.
        
        Key requirements from documentation:
        - type: "To Go" for pickup orders
        - source: "Voice" (only supported source)
        - customer: name + phone with area code
        - items: category + item + size + sellingPrice + externalRef
        """
        if customer is None:
            customer = {
                "name": "Test User",
                "phone": "410-848-1234"  # Format with area code required
            }
        
        external_ref = self._generate_external_ref()
        
        return {
            "type": "To Go",  # v1 validation expects "To Go" for pickup
            "source": "Voice",  # Only supported source per error 1004
            "externalRef": external_ref,
            "customer": customer,
            "items": [{
                "item": item_data["item"],
                "category": item_data["category"],  # Required per error 1101
                "size": item_data["size"],
                "quantity": 1,
                "externalRef": f"{external_ref}-i1",
                "sellingPrice": item_data["price"]
            }]
        }
    
    def build_acceptance_payload(self, validation_payload: Dict[str, Any], canonical_price: float) -> Dict[str, Any]:
        """
        Build acceptance payload from validation payload with canonical price.
        
        Key transformations:
        - type: "To Go" -> "Pickup" (v1 -> v2 format)  
        - price: Use canonical price from validation at order level
        - Preserve all other fields and structure
        """
        payload = validation_payload.copy()
        
        # Convert from v1 to v2 format
        payload["type"] = "Pickup"  # v2 acceptance expects "Pickup"
        payload["price"] = canonical_price  # Use canonical price from validation
        
        return payload
    
    def validate_order(self, item_data: Dict[str, Any], customer: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate order and return processed response."""
        payload = self.build_validation_payload(item_data, customer)
        status, data, raw = self.client.validate_order(payload)
        
        return {
            "status": status,
            "data": data,
            "payload": payload,
            "success": 200 <= status < 300 and data is not None,
            "canonical_price": data.get("price") if data else None,
            "raw": raw[:500] if raw else ""
        }
    
    def accept_order(self, validation_payload: Dict[str, Any], canonical_price: float) -> Dict[str, Any]:
        """Accept order using validation payload and canonical price."""
        payload = self.build_acceptance_payload(validation_payload, canonical_price)
        status, data, raw = self.client.accept_order(payload)
        
        return {
            "status": status,
            "data": data,
            "payload": payload,
            "success": 200 <= status < 300 and data is not None,
            "raw": raw[:500] if raw else ""
        }