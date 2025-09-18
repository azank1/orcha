from abc import ABC, abstractmethod
from typing import List
from models.base.menu_models import MenuItem, OrderType, Special


class MenuService(ABC):

    @abstractmethod
    async def get_order_types(self) -> List[OrderType]:
        pass
    
    @abstractmethod
    async def get_categories(self, orderType: str) -> List[str]:
        pass

    @abstractmethod
    async def get_category_items(self, category: str, orderType: str) -> List[str]:
        pass

    @abstractmethod
    async def get_item_details(self, item: str, category: str, orderType: str) -> MenuItem:
        pass

    @abstractmethod
    async def get_specials(self, orderType: str) -> List[str]:
        pass

    @abstractmethod
    async def get_special_details(self, special: str, orderType: str) -> Special:
        pass
