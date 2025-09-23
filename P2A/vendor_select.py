from __future__ import annotations
import os
import logging
from typing import Optional

from core.api_clients.api_client_ft import ApiClientFT
from core.services.menu_service_ft import MenuServiceFT
from core.services.order_service_ft import OrderServiceFT
from order_service_mock import OrderServiceMock
from menu_service_mock_export import MenuServiceExportMock

logger = logging.getLogger(__name__)

# Mock fallbacks (if available)
try:
    from core.services.menu.menu_service_mock import MenuServiceMock  # type: ignore
except Exception:  # pragma: no cover
    MenuServiceMock = None


def _validate_foodtec_config() -> bool:
    """Validate that all required FoodTec environment variables are present"""
    # Debug: Print FoodTec base URL for verification
    base_url = os.getenv("FOODTEC_BASE")
    logger.info("[P2A] FoodTec base URL from environment: %s", base_url)
    
    required_vars = [
        "FOODTEC_BASE",
        "FOODTEC_USER", 
        "FOODTEC_MENU_PASS",
        "FOODTEC_VALIDATE_PASS",
        "FOODTEC_ACCEPT_PASS",
        "FOODTEC_MENU_PATH",
        "FOODTEC_VALIDATE_PATH",
        "FOODTEC_ACCEPT_PATH"
    ]
    
    missing_vars = []
    present_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            present_vars.append(var)
            # Log API key presence (without revealing the actual keys)
            if "PASS" in var:
                logger.info("[P2A] %s is configured (length: %d)", var, len(value))
    
    logger.info("[P2A] FoodTec config check - Present: %d, Missing: %d", len(present_vars), len(missing_vars))
    
    if missing_vars:
        logger.error("[P2A] Missing FoodTec config: %s", ", ".join(missing_vars))
        logger.error("[P2A] Set P2A_VENDOR=mock or configure missing environment variables")
        return False
        
    logger.info("[P2A] All FoodTec environment variables are present and configured")
    return True


def get_services(vendor: Optional[str] = None):
    """Get menu and order services based on vendor selection with proper validation"""
    vendor = (vendor or os.getenv("P2A_VENDOR", "mock")).lower()
    
    if vendor == "foodtec":
        logger.info("[P2A] Attempting to initialize FoodTec vendor services")
        
        # Validate required configuration
        if not _validate_foodtec_config():
            logger.warning("[P2A] FoodTec configuration incomplete, falling back to mock services")
            vendor = "mock"
        else:
            try:
                client = ApiClientFT()
                logger.info("[P2A] FoodTec services initialized successfully")
                return MenuServiceFT(client), OrderServiceFT(client)
            except Exception as e:
                logger.error("[P2A] Failed to initialize FoodTec services: %s", e)
                logger.warning("[P2A] Falling back to mock services")
                vendor = "mock"
    
    elif vendor != "mock":
        logger.warning("[P2A] Unknown vendor '%s', falling back to mock", vendor)
        vendor = "mock"
    
    # Default to mock services
    logger.info("[P2A] Using mock vendor services")
    if MenuServiceMock is None:
        # Use export-shaped mock for menu export contract
        return MenuServiceExportMock(), OrderServiceMock()
    
    return MenuServiceExportMock(), OrderServiceMock()
