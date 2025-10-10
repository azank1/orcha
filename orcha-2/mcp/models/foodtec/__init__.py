"""
FoodTec-specific models
Mirrors base models but with vendor-specific extensions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from ..base import (
    SizePrice, IngredientQualifier, Ingredient, ItemChoice, 
    MenuItem, Category, Customer, OrderItem
)


class SizePriceFT(SizePrice):
    """FoodTec size/price with vendor extensions"""
    pass


class IngredientFT(Ingredient):
    """FoodTec ingredient with vendor extensions"""
    pass


class ItemChoiceFT(ItemChoice):
    """FoodTec item choice with vendor extensions"""
    pass


class MenuItemFT(MenuItem):
    """FoodTec menu item with vendor extensions"""
    pass


class CategoryFT(Category):
    """FoodTec category with vendor extensions"""
    pass


class OrderTypeFT(BaseModel):
    """FoodTec order type"""
    orderType: str = Field(..., description="FoodTec order type")
    requiresAddress: bool = Field(..., description="Address requirement")


# FoodTec-specific validation models
class FoodTecValidationPayload(BaseModel):
    """FoodTec validation request format"""
    type: str = Field(..., description="Order type: To Go, Delivery")
    source: str = Field("Voice", description="Order source")
    customer: Dict[str, Any] = Field(..., description="Customer data")
    items: List[Dict[str, Any]] = Field(..., description="Items array")
    externalRef: Optional[str] = Field(None)


class FoodTecAcceptancePayload(BaseModel):
    """FoodTec acceptance request format"""
    type: str = Field(..., description="Order type: Pickup, Delivery")
    customer: Dict[str, Any] = Field(..., description="Customer data")
    items: List[Dict[str, Any]] = Field(..., description="Items array")
    canonicalPrice: float = Field(..., description="Final price with tax")
    externalRef: Optional[str] = Field(None)