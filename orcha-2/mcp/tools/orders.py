"""
Order processing tools for Orcha-2 MCP server
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from ..models.base import Menu, OrderDraft, OrderValidation, OrderResult


async def get_menu_tool(
    orderType: str = "Pickup", 
    vendor: Optional[str] = "foodtec"
) -> Menu:
    """Get menu from vendor adapter"""
    logger.info(f"🍽️ Fetching menu: orderType={orderType}, vendor={vendor}")
    
    # TODO: Route to appropriate vendor adapter
    # For now, return static menu
    from ..adapters.foodtec_adapter import FoodTecAdapter
    adapter = FoodTecAdapter()
    return await adapter.get_menu(orderType)


async def validate_order_tool(
    order_draft: Dict[str, Any],
    vendor: Optional[str] = "foodtec"  
) -> OrderValidation:
    """Validate order with vendor"""
    logger.info(f"✅ Validating order with {vendor}")
    
    # TODO: Route to appropriate vendor adapter
    from ..adapters.foodtec_adapter import FoodTecAdapter
    adapter = FoodTecAdapter()
    return await adapter.validate_order(OrderDraft(**order_draft))


async def submit_order_tool(
    order_validation: Dict[str, Any],
    vendor: Optional[str] = "foodtec"
) -> OrderResult:
    """Submit order to vendor"""
    logger.info(f"🚀 Submitting order to {vendor}")
    
    # TODO: Route to appropriate vendor adapter
    from ..adapters.foodtec_adapter import FoodTecAdapter  
    adapter = FoodTecAdapter()
    return await adapter.submit_order(OrderValidation(**order_validation))