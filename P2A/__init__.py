"""
P2A - Python Package for FoodTec API Integration

A minimal Python package that wraps FoodTec sandbox APIs with:
- Direct HTTP calls (no web servers)
- Pydantic models for data validation
- Comprehensive error handling and retry logic
- Debug capabilities for troubleshooting

Core endpoints:
- Menu Export: GET /menu/categories
- Order Validation: POST /validate/order  
- Order Acceptance: POST /orders

Usage:
    from P2A import MenuService, OrderService
    
    menu_service = MenuService()
    order_service = OrderService()
    
    # Export menu
    menu = menu_service.export_menu()
    
    # Validate and accept order
    item, category = menu_service.pick_first_item()
    validation, acceptance = order_service.validate_and_accept_order(item, category)
"""

__version__ = "2.0.0"

from .core.api_client import FoodTecAPIClient
from .core.menu_service import MenuService
from .core.order_service import OrderService

from .models.menu import MenuCategory, MenuItem, MenuResponse
from .models.order import OrderItem, OrderRequest, ValidationResponse, AcceptanceResponse

__all__ = [
    # Core services
    "FoodTecAPIClient",
    "MenuService", 
    "OrderService",
    # Models
    "MenuCategory",
    "MenuItem", 
    "MenuResponse",
    "OrderItem",
    "OrderRequest",
    "ValidationResponse",
    "AcceptanceResponse"
]