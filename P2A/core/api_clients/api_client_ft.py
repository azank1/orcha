from models.foodtec.menu_models_ft import CategoryFT, MenuItemFT, OrderTypeFT
from typing import  List
from core.api_clients.http_client import AsyncHTTPClient


class ApiClientFT:
    """FoodTec API client (basic)."""

    def __init__(self, auth_header: str) -> None:
        self._http_client = AsyncHTTPClient(base_url="https://pizzabolis-lab.foodtecsolutions.com/ws/store/v1", 
        auth_header=auth_header)

    async def get_order_types(self) -> List[OrderTypeFT]:
        res = await self._http_client.get('menu/ordertypes')
        return [OrderTypeFT(**ot) for ot in res]

    async def get_categories(self, orderType: str) -> List[CategoryFT]:
        res = await self._http_client.get('menu/categories', params={'orderType': orderType})
        return [CategoryFT(**cat) for cat in res]
    
    async def get_category_items(self, category: str, orderType: str) -> List[MenuItemFT]:
        res = await self._http_client.get(f'menu/categories/{category}', params={'orderType': orderType})
        return [MenuItemFT(**item) for item in res['items']]
    
    async def get_item_details(self, item: str, category: str, orderType: str) -> MenuItemFT:
        res = await self._http_client.get(f'menu/categories/{category}/items/{item}', params={'orderType': orderType})
        return MenuItemFT(**res)
    
    async def get_specials(self, orderType: str) -> List[MenuItemFT]:
        res = await self._http_client.get('menu/specials', params={'orderType': orderType})
        return [MenuItemFT(**item) for item in res['items']]
        
