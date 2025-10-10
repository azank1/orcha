import os
from dotenv import load_dotenv
from models.foodtec.menu_models_ft import CategoryFT, MenuItemFT, OrderTypeFT
from typing import List
from core.api_clients.http_client import AsyncHTTPClient

# Load environment variables
load_dotenv()

# Centralize FoodTec configuration
FOODTEC_BASE = os.getenv("FOODTEC_BASE")
FOODTEC_STORE_ID = os.getenv("FOODTEC_STORE_ID")
FOODTEC_TIMEOUT = float(os.getenv("FOODTEC_TIMEOUT", 5))


class ApiClientFT:
    """FoodTec API client with environment-based configuration."""

    def __init__(self, auth_header: str) -> None:
        if not FOODTEC_BASE:
            raise ValueError("FOODTEC_BASE environment variable is required")
        if not FOODTEC_STORE_ID:
            raise ValueError("FOODTEC_STORE_ID environment variable is required")
        
        self._http_client = AsyncHTTPClient(
            base_url=FOODTEC_BASE,
            auth_header=auth_header,
            timeout=FOODTEC_TIMEOUT
        )
        self.store_id = FOODTEC_STORE_ID

    async def get_order_types(self) -> List[OrderTypeFT]:
        res = await self._http_client.get(f'store/{self.store_id}/menu/ordertypes')
        return [OrderTypeFT(**ot) for ot in res]

    async def get_categories(self, orderType: str) -> List[CategoryFT]:
        res = await self._http_client.get(f'store/{self.store_id}/menu/categories', params={'orderType': orderType})
        return [CategoryFT(**cat) for cat in res]
    
    async def get_category_items(self, category: str, orderType: str) -> List[MenuItemFT]:
        res = await self._http_client.get(f'store/{self.store_id}/menu/categories/{category}', params={'orderType': orderType})
        return [MenuItemFT(**item) for item in res['items']]
    
    async def get_item_details(self, item: str, category: str, orderType: str) -> MenuItemFT:
        res = await self._http_client.get(f'store/{self.store_id}/menu/categories/{category}/items/{item}', params={'orderType': orderType})
        return MenuItemFT(**res)
    
    async def get_specials(self, orderType: str) -> List[MenuItemFT]:
        res = await self._http_client.get(f'store/{self.store_id}/menu/specials', params={'orderType': orderType})
        return [MenuItemFT(**item) for item in res['items']]
        
