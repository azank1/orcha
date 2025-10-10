"""
Base models for vendor-agnostic order processing
Based on RP2A's model design but optimized for Orcha-2 orchestration
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class OrderType(BaseModel):
    """Order type configuration"""
    orderType: str = Field(..., description="Type of order: Pickup, Delivery, Dine In")
    requiresAddress: bool = Field(..., description="Whether address is required")
    
    def get_snake_case(self) -> str:
        return self.orderType.lower().replace(" ", "_")


class SizePrice(BaseModel):
    """Size and price combination"""
    size: str = Field(..., description="Size identifier: Sm, Md, Lg, XL, etc.")
    price: float = Field(..., description="Price for this size")


class IngredientQualifier(BaseModel):
    """Ingredient modification qualifiers"""
    name: str = Field(..., description="Qualifier: Light, Extra, No, etc.")
    priceFactor: float = Field(..., description="Price multiplier")
    recipeFactor: float = Field(..., description="Recipe amount multiplier")
    isDefault: bool = Field(False, description="Default selection")


class Ingredient(BaseModel):
    """Menu item ingredient option"""
    ingredient: str = Field(..., description="Ingredient name")
    sizePrices: List[SizePrice] = Field(default_factory=list, description="Size-specific pricing")
    allowHalfs: bool = Field(False, description="Allow half portions")
    isDefault: bool = Field(False, description="Default selection")
    qualifiers: List[IngredientQualifier] = Field(default_factory=list)
    code: Optional[str] = Field(None, description="Vendor-specific code")


class ItemChoice(BaseModel):
    """Choice group for menu item (toppings, crusts, etc.)"""
    choice: str = Field(..., description="Choice group name")
    enforcedIngredients: int = Field(0, description="Required selections")
    ingredients: List[Ingredient] = Field(default_factory=list)
    dependsOn: Optional[str] = Field(None, description="Dependency on other choice")


class MenuItem(BaseModel):
    """Complete menu item definition"""
    item: str = Field(..., description="Item name")
    code: Optional[str] = Field(None, description="Vendor item code")
    sizePrices: List[SizePrice] = Field(..., description="Base size/price options")
    choices: List[ItemChoice] = Field(default_factory=list, description="Customization options")
    category: Optional[str] = Field(None, description="Menu category")


class MenuItemSummary(BaseModel):
    """Lightweight menu item for listing"""
    item: str = Field(..., description="Item name")
    sizePrices: List[SizePrice] = Field(..., description="Available sizes/prices")
    category: Optional[str] = Field(None, description="Menu category")


class Category(BaseModel):
    """Menu category"""
    category: str = Field(..., description="Category name")
    items: List[MenuItem] = Field(default_factory=list)


class Menu(BaseModel):
    """Complete menu structure"""
    categories: List[Category] = Field(..., description="All menu categories")
    orderTypes: List[OrderType] = Field(default_factory=list)


class Customer(BaseModel):
    """Customer information"""
    name: str = Field(..., description="Customer name")
    phone: str = Field(..., description="Phone number with area code")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[Dict[str, Any]] = Field(None, description="Customer address")


class OrderItem(BaseModel):
    """Item in an order"""
    item: str = Field(..., description="Menu item name")
    category: str = Field(..., description="Menu category")
    size: str = Field(..., description="Selected size")
    quantity: int = Field(1, description="Quantity")
    sellingPrice: float = Field(..., description="Item price")
    customizations: List[Dict[str, Any]] = Field(default_factory=list)
    externalRef: Optional[str] = Field(None, description="External reference")


class OrderDraft(BaseModel):
    """Draft order for validation"""
    type: str = Field(..., description="Order type: To Go, Delivery, Dine In")
    source: str = Field("Voice", description="Order source")
    customer: Customer = Field(..., description="Customer information")
    items: List[OrderItem] = Field(..., description="Order items")
    externalRef: Optional[str] = Field(None, description="External order reference")


class OrderValidation(BaseModel):
    """Validated order response"""
    success: bool = Field(..., description="Validation success")
    canonicalPrice: float = Field(..., description="Final price with tax")
    orderDraft: OrderDraft = Field(..., description="Original draft")
    validationErrors: List[str] = Field(default_factory=list)
    externalRef: Optional[str] = Field(None)


class OrderSubmission(BaseModel):
    """Final order submission"""
    type: str = Field(..., description="Order type for submission")
    customer: Customer = Field(..., description="Customer info")
    items: List[OrderItem] = Field(..., description="Order items")
    canonicalPrice: float = Field(..., description="Validated total price")
    externalRef: Optional[str] = Field(None)


class OrderResult(BaseModel):
    """Order submission result"""
    success: bool = Field(..., description="Submission success")
    orderNumber: Optional[str] = Field(None, description="Assigned order number")
    confirmation: Optional[Dict[str, Any]] = Field(None, description="Confirmation details")
    errors: List[str] = Field(default_factory=list)


# Search models
class SearchResult(BaseModel):
    """Search result item"""
    item: str = Field(..., description="Item name")
    category: str = Field(..., description="Category")
    score: float = Field(..., description="Relevance score")
    snippet: Optional[str] = Field(None, description="Matching text snippet")


class SearchResponse(BaseModel):
    """Search results"""
    results: List[SearchResult] = Field(..., description="Ranked results")
    query: str = Field(..., description="Original query")
    total: int = Field(..., description="Total matches")
    searchTime: float = Field(..., description="Search time in seconds")