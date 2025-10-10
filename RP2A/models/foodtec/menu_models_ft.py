
from pydantic import BaseModel, Field
from typing import List, Optional

class OrderTypeFT(BaseModel):
	orderType: str = Field(..., description="Type of order, e.g., 'delivery', 'pickup', etc.")
	requiresAddress: bool = Field(..., description="Indicates if an address is required for this order type.")

class SizePriceFT(BaseModel):
	size: str = Field(..., description="Size of the item, e.g., '14' for 14-inch pizza.")
	price: float = Field(..., description="Price for the specified size.")

class IngredientQualifierFT(BaseModel):
	name: str = Field(..., description="Qualifier name, e.g., 'Light', 'Extra', etc.")
	priceFactor: float = Field(..., description="Multiplier for price based on qualifier, e.g., 0.0 for no extra charge.")
	recipeFactor: float = Field(..., description="Multiplier for recipe quantity based on qualifier, e.g., 0.0 for no extra ingredient.")
	isDefault: bool = Field(..., description="Indicates if this qualifier is the default selection.")
	

# Ingredient model
class IngredientFT(BaseModel):
	ingredient: str = Field(..., description="Ingredient name, e.g., 'Cheese'.")
	sizePrices: List[SizePriceFT] = Field(..., description="List of size-specific prices for this ingredient.")
	allowHalfs: bool = Field(..., description="Whether halves are allowed for this ingredient.")
	isDefault: bool = Field(..., description="Whether this ingredient is selected by default.")
	qualifiers: List[IngredientQualifierFT] = Field(..., description="Available qualifiers for this ingredient.")
	code: Optional[str] = Field(None, description="Optional external/code identifier for the ingredient; may be null.")


# ItemChoice model
class ItemChoiceFT(BaseModel):
	choice: str = Field(..., description="Name of the choice/group, e.g., 'Toppings' or 'Crusts'.")
	enforcedIngredients: int = Field(..., description="Number of ingredients that are enforced/required from this choice.")
	ingredients: List[IngredientFT] = Field(..., description="List of ingredient options available under this choice.")
	dependsOn: Optional[str] = Field(None, description="Optional dependency key indicating this choice depends on another selection; may be null.")


# MenuItem model
class MenuItemFT(BaseModel):
	item: str = Field(..., description="Name of the menu item, e.g., 'BBQ Chicken'.")
	code: Optional[str] = Field(None, description="Optional merchant item code or identifier.")
	sizePrices: List[SizePriceFT] = Field(..., description="List of size-specific prices for the item.")
	choices: List[ItemChoiceFT] = Field(..., description="List of choice groups available for the item (toppings, crusts, etc.).")


# Category model
class CategoryFT(BaseModel):
	category: str = Field(..., description="Category name, e.g., 'Pizza'.")
	items: List[MenuItemFT] = Field(..., description="List of menu items in this category.")


# Top-level Menu model
class MenuFT(BaseModel):
    categories: List[CategoryFT] = Field(..., description="Top-level list of categories in the menu.")


# Special model
class SpecialFT(BaseModel):
	special: str = Field(..., description="Short title of the special, e.g., '$10 Off (Golf outing)'.")
	label: str = Field(..., description="Display label for the special, e.g., '$10 Off Any Order'.")
	description: str = Field(..., description="Longer description of the special.")
	type: str = Field(..., description="Type of special, e.g., 'Coupon', 'Deal', etc.")
	disclaimer: Optional[str] = Field(None, description="Optional disclaimer text shown with the special.")
	start: Optional[int] = Field(None, description="Start time as epoch milliseconds or null if not specified.")
	end: Optional[int] = Field(None, description="End time as epoch milliseconds or null if not specified.")
	orderTypes: List[str] = Field(..., description="Allowed order types for this special (strings).")
	code: Optional[str] = Field(None, description="Optional coupon/code string used to apply the special.")
	isCombo: bool = Field(..., description="Indicates whether the special is a combo offer.")


