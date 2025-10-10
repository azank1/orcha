from models.base import menu_models as base_models
from models.foodtec import menu_models_ft as ft_models
from typing import List


class MenuAdapterFT:
    """Adapter to convert FoodTec FT models to base menu models.

    The FoodTec FT models and the base models share similar field names; we use
    Pydantic's `parse_obj` to convert between them safely.
    """

    @staticmethod
    def adapt_order_types(
        order_types_ft: List[ft_models.OrderTypeFT],
    ) -> List[base_models.OrderType]:
        # FT and base OrderType have the same fields (orderType, requiresAddress)
        return [base_models.OrderType.parse_obj(ot.dict()) for ot in order_types_ft]

    @staticmethod
    def adapt_categories(categories_ft: List[ft_models.CategoryFT]) -> List[str]:
        """Return a list of category names (strings) from FT CategoryFT models."""
        return [cat.category for cat in categories_ft]

    @staticmethod
    def adapt_category_models(
        categories_ft: List[ft_models.CategoryFT],
    ) -> List[base_models.Category]:
        """Convert FT CategoryFT models to base Category models."""
        adapted: List[base_models.Category] = []
        for cat in categories_ft:
            try:
                adapted.append(base_models.Category.parse_obj(cat.dict()))
            except Exception as exc:
                # provide context for parsing error
                raise ValueError(
                    f"Failed to parse CategoryFT -> Category: {exc}"
                ) from exc
        return adapted

    @staticmethod
    def adapt_menu_items(
        menu_items_ft: List[ft_models.MenuItemFT],
    ) -> List[base_models.MenuItem]:
        adapted_items: List[base_models.MenuItem] = []
        for item in menu_items_ft:
            # Use parse_obj to convert FT model dict into the base model
            try:
                adapted = base_models.MenuItem.parse_obj(item.dict())
            except Exception as exc:
                raise ValueError(
                    f"Failed to parse MenuItemFT -> MenuItem for item={getattr(item, 'item', '<unknown>')}: {exc}"
                ) from exc
            adapted_items.append(adapted)
        return adapted_items
    
    @staticmethod
    def adapt_menu_item(
        menu_item_ft: ft_models.MenuItemFT,
    ) -> base_models.MenuItem:
        # Use parse_obj to convert FT model dict into the base model
        try:
            return base_models.MenuItem.parse_obj(menu_item_ft.dict())
        except Exception as exc:
            raise ValueError(
                f"Failed to parse MenuItemFT -> MenuItem for item={getattr(menu_item_ft, 'item', '<unknown>')}: {exc}"
            ) from exc
    
    @staticmethod
    def adapt_menu_item_summarized(
        menu_item_ft: ft_models.MenuItemFT,
    ) -> base_models.MenuItemSummarized:
        # Use parse_obj to convert FT model dict into the base model
        try:
            return base_models.MenuItemSummarized.parse_obj(menu_item_ft.dict())
        except Exception as exc:
            raise ValueError(
                f"Failed to parse MenuItemFT -> MenuItem for item={getattr(menu_item_ft, 'item', '<unknown>')}: {exc}"
            ) from exc

    @staticmethod
    def adapt_menu(menu_ft: ft_models.MenuFT) -> base_models.Menu:
        """Convert a full FT MenuFT into the base Menu model."""
        try:
            return base_models.Menu.parse_obj(menu_ft.dict())
        except Exception as exc:
            raise ValueError(f"Failed to parse MenuFT -> Menu: {exc}") from exc
