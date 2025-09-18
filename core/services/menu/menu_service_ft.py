from core.services.menu.menu_service import MenuService
from models.base.menu_models import MenuItem, OrderType, Special
from typing import List
from core.api_clients.api_client_ft import ApiClientFT
from core.adapters.menu_adapter_ft import MenuAdapterFT
from core.services.auth_service import BasicAuth

class MenuServiceFT(MenuService):

    def __init__(self, auth: BasicAuth) -> None:
        self._api_client = ApiClientFT(auth_header=auth.get_auth())

    async def get_order_types(self) -> List[OrderType]:
        try:
            order_types_ft = await self._api_client.get_order_types()
            return MenuAdapterFT.adapt_order_types(order_types_ft)
        except Exception as exc:
            raise RuntimeError(f"Failed to get order types: {exc}") from exc
    
    async def get_categories(self, orderType: str) -> List[str]:
        try:
            categories_ft = await self._api_client.get_categories(orderType)
            return MenuAdapterFT.adapt_categories(categories_ft)
        except Exception as exc:
            raise RuntimeError(f"Failed to get categories for orderType={orderType}: {exc}") from exc

    async def get_category_items(self, category: str, orderType: str) -> List[str]:
        try:
            items_ft = await self._api_client.get_category_items(category, orderType)
            items = MenuAdapterFT.adapt_menu_items(items_ft)
            return [item.item for item in items]
        except Exception as exc:
            raise RuntimeError(f"Failed to get items for category={category}, orderType={orderType}: {exc}") from exc

    async def get_item_details(self, item: str, category: str, orderType: str) -> MenuItem:
        try:
            item_ft = await self._api_client.get_item_details(item, category, orderType)
            return MenuAdapterFT.adapt_menu_item(item_ft)
        except Exception as exc:
            raise RuntimeError(f"Failed to get item details for item={item}, category={category}, orderType={orderType}: {exc}") from exc

    async def get_specials(self, orderType: str) -> List[str]:
        try:
            specials_ft = await self._api_client.get_specials(orderType)
            specials = MenuAdapterFT.adapt_menu_items(specials_ft)
            return [special.item for special in specials]
        except Exception as exc:
            raise RuntimeError(f"Failed to get specials for orderType={orderType}: {exc}") from exc

    async def get_special_details(self, special: str, orderType: str) -> Special:
        try:
            special_ft = await self._api_client.get_item_details(special, "specials", orderType)
            special_item = MenuAdapterFT.adapt_menu_item(special_ft)
            return Special.parse_obj(special_item.dict())
        except Exception as exc:
            raise RuntimeError(f"Failed to get special details for special={special}, orderType={orderType}: {exc}") from exc