import json
import random
from typing import Dict, Any, List, Optional, Tuple
from .api_client import FoodTecAPIClient


class MenuService:
    """Service for menu-related operations with FoodTec API"""
    
    def __init__(self, api_client: Optional[FoodTecAPIClient] = None):
        self.api_client = api_client or FoodTecAPIClient()
    
    def export_menu(self, order_type: str = "Pickup") -> Dict[str, Any]:
        """Export menu with processed response - exact copy of working services.py"""
        status, data, raw = self.api_client.get_menu(order_type)
        
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