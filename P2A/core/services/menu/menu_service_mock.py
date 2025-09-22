from __future__ import annotations
from typing import List
from models.base.menu_models import MenuItem, OrderType, Special, SizePrice, ItemChoice, Ingredient, IngredientQualifier, Category, Menu
from .menu_service import MenuService
import logging

logger = logging.getLogger(__name__)


class MenuServiceMock(MenuService):
    """Mock implementation returning deterministic data for testing.

    Includes minimal idempotency echo via `idem` value when present in headers/logs.
    """

    def __init__(self, idem: str | None = None):
        self._idem = idem

    async def get_order_types(self) -> List[OrderType]:
        logger.info("mock.get_order_types idem=%s", self._idem)
        return [
            OrderType(orderType="Pickup", requiresAddress=False),
            OrderType(orderType="Delivery", requiresAddress=True),
        ]

    async def get_categories(self, orderType: str) -> List[str]:
        logger.info("mock.get_categories orderType=%s idem=%s", orderType, self._idem)
        return ["Pizza", "Burgers", "Salads"]

    async def get_category_items(self, category: str, orderType: str) -> List[str]:
        logger.info("mock.get_category_items category=%s orderType=%s idem=%s", category, orderType, self._idem)
        sample = {
            "Pizza": ["Margherita", "BBQ Chicken"],
            "Burgers": ["Classic Burger"],
            "Salads": ["Caesar"]
        }
        return sample.get(category, [])

    async def get_item_details(self, item: str, category: str, orderType: str) -> MenuItem:
        logger.info("mock.get_item_details item=%s category=%s orderType=%s idem=%s", item, category, orderType, self._idem)
        return MenuItem(
            item=item,
            code=f"{category}:{item}",
            sizePrices=[SizePrice(size="Regular", price=9.99)],
            choices=[
                ItemChoice(
                    choice="Toppings",
                    enforcedIngredients=0,
                    ingredients=[
                        Ingredient(
                            ingredient="Cheese",
                            sizePrices=[SizePrice(size="Regular", price=0.0)],
                            allowHalfs=True,
                            isDefault=True,
                            qualifiers=[
                                IngredientQualifier(name="Light", priceFactor=0.0, recipeFactor=0.5, isDefault=False),
                                IngredientQualifier(name="Regular", priceFactor=0.0, recipeFactor=1.0, isDefault=True),
                                IngredientQualifier(name="Extra", priceFactor=1.5, recipeFactor=1.5, isDefault=False),
                            ],
                            code="CHEESE",
                        )
                    ],
                    dependsOn=None,
                )
            ],
        )

    async def get_specials(self, orderType: str) -> List[str]:
        logger.info("mock.get_specials orderType=%s idem=%s", orderType, self._idem)
        return ["$10 Off Any Order"]

    async def get_special_details(self, special: str, orderType: str) -> Special:
        logger.info("mock.get_special_details special=%s orderType=%s idem=%s", special, orderType, self._idem)
        return Special(
            special="golf-outing-10",
            label="$10 Off Any Order",
            description="Get $10 off on any purchase.",
            type="Coupon",
            disclaimer="Not combinable with other offers.",
            start=None,
            end=None,
            orderTypes=["Pickup", "Delivery"],
            code="SAVE10",
            isCombo=False,
        )
