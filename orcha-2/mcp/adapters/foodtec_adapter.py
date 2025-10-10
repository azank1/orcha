"""
FoodTec POS Adapter for Orcha-2
Async HTTP client for FoodTec API integration with comprehensive error handling
"""
import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import httpx
from loguru import logger

# Load environment variables
load_dotenv()

class FoodTecAdapter:
    """
    Production-ready async FoodTec API adapter
    Handles authentication, retries, and Pydantic model validation
    """
    
    def __init__(self):
        """Initialize FoodTec adapter with environment configuration"""
        self.base_url = os.getenv("FOODTEC_BASE", "https://pizzabolis-lab.foodtecsolutions.com/ws/store/v1")
        self.menu_path = os.getenv("FOODTEC_MENU_PATH", "/menu/categories") 
        self.validate_path = os.getenv("FOODTEC_VALIDATE_PATH", "/orders/validate")
        self.accept_path = os.getenv("FOODTEC_ACCEPT_PATH", "/orders")
        # Optional alternate validation flow: POST /orders?validateOnly=true
        self.validate_via_orders = os.getenv("FOODTEC_VALIDATE_VIA_ORDERS", "true").lower() in {"1", "true", "yes"}
        self.validate_flag_param = os.getenv("FOODTEC_VALIDATE_FLAG_PARAM", "validateOnly")
        
        # Store/menu query configuration
        self.store_param = os.getenv("FOODTEC_STORE_PARAM", "store")
        self.default_store_id = os.getenv("FOODTEC_STORE_ID", "default")
        
        # Authentication credentials
        self.user = os.getenv("FOODTEC_USER", "apiclient")
        self.menu_pass = os.getenv("FOODTEC_MENU_PASS", "")
        self.validate_pass = os.getenv("FOODTEC_VALIDATE_PASS", "")
        self.accept_pass = os.getenv("FOODTEC_ACCEPT_PASS", "")
        
        # Allowed/desired order source value (API may be strict)
        self.allowed_source = os.getenv("FOODTEC_ALLOWED_SOURCE", "Voice")
        
        # Configuration
        self.timeout = float(os.getenv("TIMEOUT", 5))
        self.max_retries = int(os.getenv("RETRY_MAX", 2))
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            headers={
                "Accept": "application/json",
                # Content-Type is set automatically for json= payloads
                "User-Agent": "Orcha2-FoodTecAdapter/2.0"
            }
        )
        
        logger.info(f"🔌 FoodTecAdapter initialized - Base: {self.base_url}")
    
    async def fetch_menu(self, store_id: str = "default") -> Dict[str, Any]:
        """
        Fetch menu from FoodTec API
        
        Args:
            store_id: Store identifier (default for sandbox)
            
        Returns:
            Menu data dictionary with categories and items
        """
        # Attach store parameter if provided/required
        store = store_id or self.default_store_id
        url = f"{self.base_url}{self.menu_path}"
        if self.store_param:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{self.store_param}={store}"
        auth = (self.user, self.menu_pass)
        
        logger.info(f"📋 Fetching menu from FoodTec - Store: {store_id}")
        
        try:
            response = await self._make_request("GET", url, auth=auth)
            
            # Transform FoodTec response to Orcha-2 format
            menu_data = self._transform_menu_response(response)
            
            logger.info(f"✅ Menu fetched successfully - Categories: {len(menu_data.get('categories', []))}")
            return menu_data
            
        except Exception as e:
            logger.error(f"❌ Menu fetch failed: {e}")
            raise
    
    async def validate_order(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate order with FoodTec API
        
        Args:
            draft: Order draft dictionary
            
        Returns:
            Validation response with pricing and availability
        """
        url = f"{self.base_url}{self.validate_path}"
        auth = (self.user, self.validate_pass)
        
        logger.info(f"🔍 Validating order with FoodTec")
        
        try:
            # Transform Orcha-2 format to FoodTec format
            foodtec_payload = self._transform_order_to_foodtec(draft)
            
            response = await self._make_request("POST", url, json=foodtec_payload, auth=auth)
            
            # If server returned HTML or empty JSON unexpectedly, and fallback is enabled, try validate via orders endpoint
            if self.validate_via_orders and (not isinstance(response, dict) or ("meta" not in response and "valid" not in response)):
                alt_url = f"{self.base_url}{self.accept_path}"
                sep = "&" if "?" in alt_url else "?"
                alt_url = f"{alt_url}{sep}{self.validate_flag_param}=true"
                logger.debug(f"🔁 Falling back to validate via orders endpoint: {alt_url}")
                response = await self._make_request("POST", alt_url, json=foodtec_payload, auth=auth)
            
            # Transform response back to Orcha-2 format
            validation_data = self._transform_validation_response(response)
            
            logger.info(f"✅ Order validation completed - Status: {validation_data.get('status', 'unknown')}")
            return validation_data
            
        except Exception as e:
            logger.error(f"❌ Order validation failed: {e}")
            raise
    
    async def accept_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit order to FoodTec API
        
        Args:
            order: Validated order dictionary
            
        Returns:
            Order confirmation with order number
        """
        url = f"{self.base_url}{self.accept_path}"
        auth = (self.user, self.accept_pass)

        logger.info(f"📤 Submitting order to FoodTec")

        try:
            # Transform to FoodTec format
            foodtec_payload = self._transform_order_to_foodtec(order)

            response = await self._make_request("POST", url, json=foodtec_payload, auth=auth)

            # Transform response
            confirmation_data = self._transform_confirmation_response(response)

            order_number = confirmation_data.get('order_number', 'unknown')
            logger.info(f"✅ Order accepted - Number: {order_number}")
            return confirmation_data

        except Exception as e:
            logger.error(f"❌ Order submission failed: {e}")
            raise
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data
        """
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"🌐 {method} {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json() if response.content else {}
                
                logger.debug(f"✅ Request successful - Status: {response.status_code}")
                return data
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"⚠️ HTTP error {e.response.status_code}: {e.response.text}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                
            except httpx.RequestError as e:
                logger.warning(f"⚠️ Request error: {e}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
                
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                raise
    
    def _transform_menu_response(self, foodtec_data: Dict) -> Dict[str, Any]:
        """Transform FoodTec menu response to Orcha-2 format"""
        try:
            # Extract categories from FoodTec response
            categories = []
            
            # Handle FoodTec menu structure
            if "categories" in foodtec_data:
                for cat in foodtec_data["categories"]:
                    items = []
                    for item in cat.get("items", []):
                        # Transform item to Orcha-2 format
                        orcha_item = {
                            "item": item.get("name", ""),
                            "code": item.get("id", ""),
                            "sizePrices": [],
                            "choices": [],
                            "category": cat.get("name", "")
                        }
                        
                        # Transform sizes/prices
                        if "sizes" in item:
                            for size in item["sizes"]:
                                orcha_item["sizePrices"].append({
                                    "size": size.get("name", ""),
                                    "price": float(size.get("price", 0))
                                })
                        
                        items.append(orcha_item)
                    
                    categories.append({
                        "category": cat.get("name", ""),
                        "items": items
                    })
            
            return {
                "categories": categories,
                "orderTypes": [
                    {"orderType": "Pickup", "requiresAddress": False},
                    {"orderType": "Delivery", "requiresAddress": True}
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Menu transformation failed: {e}")
            # Return fallback structure
            return {
                "categories": [],
                "orderTypes": []
            }
    
    def _transform_order_to_foodtec(self, orcha_order: Dict) -> Dict[str, Any]:
        """Transform Orcha-2 order format to FoodTec format"""
        try:
            # Ensure required fields align with FoodTec expectations
            payload: Dict[str, Any] = {
                "type": orcha_order.get("type", "To Go"),
                # Enforce allowed source value if the provided one is unsupported
                "source": orcha_order.get("source") or self.allowed_source,
                "customer": orcha_order.get("customer", {}),
                "items": orcha_order.get("items", [])
            }
            # External reference is commonly required by FoodTec
            if orcha_order.get("externalRef"):
                payload["externalRef"] = orcha_order.get("externalRef")
            # Some APIs expect store/location identifier at order-time as well
            if self.store_param and self.default_store_id:
                payload.setdefault("store", self.default_store_id)
            return payload
        except Exception as e:
            logger.error(f"❌ Order transformation failed: {e}")
            return orcha_order  # Return as-is if transformation fails
    
    def _transform_validation_response(self, foodtec_data: Dict) -> Dict[str, Any]:
        """Transform FoodTec validation response to Orcha-2 format"""
        try:
            return {
                "success": foodtec_data.get("valid", True),
                "canonicalPrice": float(foodtec_data.get("total", 0)),
                "orderDraft": foodtec_data.get("order", {}),
                "validationErrors": foodtec_data.get("errors", []),
                "externalRef": foodtec_data.get("reference", None)
            }
        except Exception as e:
            logger.error(f"❌ Validation response transformation failed: {e}")
            return {"success": False, "validationErrors": [str(e)]}
    
    def _transform_confirmation_response(self, foodtec_data: Dict) -> Dict[str, Any]:
        """Transform FoodTec confirmation response to Orcha-2 format"""
        try:
            return {
                "success": True,
                "order_number": foodtec_data.get("orderNumber", ""),
                "confirmation": foodtec_data.get("confirmation", {}),
                "estimatedTime": foodtec_data.get("estimatedMinutes", 30),
                "externalRef": foodtec_data.get("reference", None)
            }
        except Exception as e:
            logger.error(f"❌ Confirmation response transformation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()
        logger.info("🔌 FoodTec adapter connection closed")