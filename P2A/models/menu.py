from pydantic import BaseModel
from typing import List, Optional


class MenuCategory(BaseModel):
    """Menu category from FoodTec API"""
    id: int
    name: str
    description: Optional[str] = None


class MenuItem(BaseModel):
    """Menu item from FoodTec API"""
    id: int
    name: str
    price: float
    description: Optional[str] = None
    category_id: int


class MenuResponse(BaseModel):
    """Full menu response from FoodTec API"""
    categories: List[MenuCategory]
    items: List[MenuItem]