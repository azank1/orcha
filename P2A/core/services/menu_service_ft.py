import os
import logging
from typing import Any, Dict, List
from ..api_clients.api_client_ft import ApiClientFT

logger = logging.getLogger(__name__)


class MenuServiceFT:
    """FoodTec menu service with Engine schema mapping and pagination"""
    
    def __init__(self, client: ApiClientFT | None = None):
        self.client = client or ApiClientFT()
        self.menu_path = os.getenv("FOODTEC_MENU_PATH", "/menu")
        self.menu_pass = os.getenv("FOODTEC_MENU_PASS")

    def _map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Map FoodTec item format to Engine schema"""
        # Extract the base price from the first size price if available
        base_price = 0
        size_prices = item.get("sizePrices", [])
        if size_prices and isinstance(size_prices, list) and len(size_prices) > 0:
            first_size_price = size_prices[0]
            if isinstance(first_size_price, dict):
                base_price = first_size_price.get("price", 0)
        
        return {
            "sku": str(item.get("code", "")),
            "name": item.get("item", ""),
            "price": base_price,
            "metadata": {
                "sizePrices": item.get("sizePrices", []),
                "choices": item.get("choices", []),
                "code": item.get("code")
            },
        }

    def _map_category(self, category: Dict[str, Any]) -> Dict[str, Any]:
        """Map FoodTec category format to Engine schema"""
        items = [self._map_item(item) for item in category.get("items", [])]
        return {
            "id": category.get("category", ""),
            "name": category.get("category", ""),
            "items": items
        }

    def export_menu(self, store_id: str = "default", page: int = 1, page_size: int = 50, q: str | None = None) -> Dict[str, Any]:
        """Export menu with pagination according to FoodTec API v1 specification"""
        
        # Validate required parameters
        if not store_id:
            logger.error("[FoodTec] store_id is required for menu export")
            return {"ok": False, "message": "INVALID_PARAMS", "details": "store_id is required"}
            
        logger.info("[FoodTec] Exporting menu for store: %s (page %d, size %d)", 
                   store_id, page, page_size)
        
        try:
            # 🎯 EXACT POSTMAN CONFIGURATION REPLICATION
            # Method: GET  
            # URL: {FOODTEC_BASE}/menu/categories
            # Required Query: orderType=Pickup
            # Headers: Content-Type: application/json, Accept: application/json
            # Auth: Basic apiclient:FOODTEC_MENU_PASS
            
            # Build exact URL as per Postman
            url = f"{self.client.base}/menu/categories"
            
            # Required query params (orderType is mandatory)
            params = {
                "orderType": "Pickup"  # Required per FoodTec API spec
            }
            
            # Add pagination parameters  
            if page != 1:
                params["page"] = str(page)
            if page_size != 50:
                params["pageSize"] = str(page_size)
            
            # Add search filter if provided
            if q:
                params["q"] = q
                
            # Exact headers as used in Postman
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            
            # Basic auth as per Postman config
            auth = (self.client.user, self.client.menu_pass)  # apiclient:FOODTEC_MENU_PASS
            
            # 📝 Debug logging before request
            from urllib.parse import urlencode
            query_string = urlencode(params)
            full_url_with_params = f"{url}?{query_string}"
            
            logger.info("[FoodTec] GET %s", full_url_with_params)
            logger.info("[FoodTec] Headers: %s", {k: v for k, v in headers.items()})
            logger.info("[FoodTec] Auth User: %s (password masked)", self.client.user)
            logger.info("[FoodTec] Query Params: %s", params)
            
            # Make HTTP request with exact Postman configuration
            import httpx
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    url=url,
                    params=params,
                    headers=headers,
                    auth=auth
                )
                
                status = response.status_code
                try:
                    body = response.json()
                except Exception:
                    body = response.text
                    
            logger.info("[FoodTec] Menu API response: status=%d", status)
            
            # Log response details for debugging
            if isinstance(body, dict):
                logger.debug("[FoodTec] Response keys: %s", list(body.keys()))
            elif isinstance(body, list):
                logger.debug("[FoodTec] Response: list with %d items", len(body))
            else:
                logger.debug("[FoodTec] Response type: %s, length: %d", type(body), len(str(body)))
                
        except Exception as exc:
            logger.exception("[FoodTec] Failed to fetch menu: %s", exc)
            # Fallback to mock if exception occurs
            logger.info("[FoodTec] Exception occurred, falling back to sample data")
            return self._fallback_to_sample(store_id, page, page_size, q)

        # 🎯 FALLBACK HANDLING as per instruction
        if status == 200:
            # ✅ SUCCESS: Parse categories → Engine schema
            logger.info("[FoodTec] ✅ SUCCESS: Got 200 response from FoodTec API")
            
            # Normalize response structure
            # FoodTec API returns an array of categories directly, not wrapped in an object
            if isinstance(body, list):
                raw_categories = body
            elif isinstance(body, dict) and "categories" in body:
                raw_categories = body.get("categories", [])
            else:
                logger.error("[FoodTec] Invalid response format, expected list or dict with categories, got %s", type(body))
                logger.info("[FoodTec] Invalid response format, falling back to sample data")
                return self._fallback_to_sample(store_id, page, page_size, q)
                
        else:
            # ❌ NOT 200: Log status + response body and fallback to sample
            logger.error("[FoodTec] Menu export failed with status %d", status)
            logger.error("[FoodTec] Response body: %s", str(body)[:500])  # Log first 500 chars
            logger.info("[FoodTec] Non-200 status, falling back to sample_categories_res.json")
            return self._fallback_to_sample(store_id, page, page_size, q)

        if not isinstance(raw_categories, list):
            logger.warning("[FoodTec] No categories found in response, using empty list")
            raw_categories = []

        logger.info("[FoodTec] Found %d categories in response", len(raw_categories))

        # Map to Engine schema
        categories = [self._map_category(cat) for cat in raw_categories]

        # Apply search filter if provided
        if q:
            q_lower = q.lower()
            for category in categories:
                filtered_items = []
                for item in category["items"]:
                    if (q_lower in (item.get("name", "") or "").lower() or 
                        q_lower in (item.get("sku", "") or "").lower()):
                        filtered_items.append(item)
                category["items"] = filtered_items

        # Flatten items for pagination across all categories
        all_items = []
        for category in categories:
            for item in category["items"]:
                all_items.append({"category": category["name"], **item})

        total_items = len(all_items)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_items[start_idx:end_idx]

        # Regroup paginated items back into categories
        category_map: Dict[str, List[Dict[str, Any]]] = {}
        for item in paginated_items:
            cat_name = item.pop("category")
            category_map.setdefault(cat_name, []).append(item)

        # Build final category structure
        result_categories = [
            {"name": cat_name, "items": items}
            for cat_name, items in category_map.items()
        ]

        logger.info("[FoodTec] Menu export successful: %d total items, %d returned", 
                   total_items, len(paginated_items))

        return {
            "ok": True,
            "store_id": store_id,
            "categories": result_categories,
            "total": total_items,
            "page": page,
            "page_size": page_size
        }

    def _fallback_to_sample(self, store_id: str, page: int, page_size: int, q: str | None = None) -> Dict[str, Any]:
        """Fallback to sample data when FoodTec API fails"""
        import json
        
        try:
            sample_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "menu", "sample_categories_res.json")
            if os.path.exists(sample_file):
                with open(sample_file, 'r') as f:
                    body = json.load(f)
                logger.info("[FoodTec] Using sample data as fallback")
                
                # Process the sample data through the same logic as real API response
                raw_categories = body.get("categories", [])
                if not isinstance(raw_categories, list):
                    raw_categories = []

                # Map to Engine schema
                categories = [self._map_category(cat) for cat in raw_categories]

                # Apply search filter if provided
                if q:
                    q_lower = q.lower()
                    for category in categories:
                        filtered_items = []
                        for item in category["items"]:
                            if (q_lower in (item.get("name", "") or "").lower() or 
                                q_lower in (item.get("sku", "") or "").lower()):
                                filtered_items.append(item)
                        category["items"] = filtered_items

                # Flatten items for pagination across all categories
                all_items = []
                for category in categories:
                    for item in category["items"]:
                        all_items.append({"category": category["name"], **item})

                total_items = len(all_items)
                
                # Apply pagination
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_items = all_items[start_idx:end_idx]

                # Regroup paginated items back into categories
                category_map: Dict[str, List[Dict[str, Any]]] = {}
                for item in paginated_items:
                    cat_name = item.pop("category")
                    category_map.setdefault(cat_name, []).append(item)

                # Build final category structure
                result_categories = [
                    {"name": cat_name, "items": items}
                    for cat_name, items in category_map.items()
                ]

                logger.info("[FoodTec] Sample data fallback successful: %d total items, %d returned", 
                           total_items, len(paginated_items))

                return {
                    "ok": True,
                    "store_id": store_id,
                    "categories": result_categories,
                    "total": total_items,
                    "page": page,
                    "page_size": page_size,
                    "fallback": True  # Indicate this is fallback data
                }
                
        except Exception as exc:
            logger.exception("[FoodTec] Failed to load sample data: %s", exc)
            
        # Ultimate fallback if sample data fails
        return {
            "ok": False, 
            "message": "fallback_failed", 
            "details": "Both FoodTec API and sample data failed"
        }
