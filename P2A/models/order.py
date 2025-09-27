from pydantic import BaseModel
from typing import List, Optional


class OrderItem(BaseModel):
    """Single item in an order"""
    menu_item_id: int
    quantity: int
    price: Optional[float] = None
    canonical_price: Optional[float] = None


class OrderRequest(BaseModel):
    """Order request payload for validation and acceptance"""
    external_reference: str
    phone: str
    source: str = "Voice"  # Only supported value
    category: Optional[int] = None
    items: List[OrderItem]


class ValidationResponse(BaseModel):
    """Response from order validation"""
    status: str
    message: Optional[str] = None
    canonical_price: Optional[float] = None
    validated_items: Optional[List[OrderItem]] = None


class AcceptanceResponse(BaseModel):
    """Response from order acceptance"""
    status: str
    order_id: Optional[str] = None
    message: Optional[str] = None