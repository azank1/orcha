from __future__ import annotations
import os
import logging
from typing import Optional

from core.api_clients.api_client_ft import ApiClientFT
from core.services.menu_service_ft import MenuServiceFT
from core.services.order_service_ft import OrderServiceFT

logger = logging.getLogger(__name__)

# All mock services have been removed - using FoodTec with fallbacks only

# Global service cache for idempotency support
_service_cache = {}


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
    """Get menu and order services based on vendor selection with proper validation. Cached for idempotency."""
    vendor = (vendor or os.getenv("P2A_VENDOR", "mock")).lower()
    
    # Check cache first
    if vendor in _service_cache:
        logger.debug(f"[P2A] Returning cached services for vendor: {vendor}")
        return _service_cache[vendor]
    
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
                services = (MenuServiceFT(client), OrderServiceFT(client))
                _service_cache[vendor] = services
                return services
            except Exception as e:
                logger.error("[P2A] Failed to initialize FoodTec services: %s", e)
                logger.error("[P2A] Mock services no longer available - using FoodTec with fallbacks")
                # Try to initialize FoodTec anyway, it will use internal fallbacks
                try:
                    client = ApiClientFT()
                    services = (MenuServiceFT(client), OrderServiceFT(client))
                    _service_cache[vendor] = services
                    return services
                except Exception as e2:
                    logger.error("[P2A] Complete failure to initialize services: %s", e2)
                    raise RuntimeError("Cannot initialize any service provider") from e2
    
    elif vendor != "mock":
        logger.warning("[P2A] Unknown vendor '%s', falling back to FoodTec with fallbacks", vendor)
        vendor = "foodtec"
        # Use FoodTec with internal fallbacks
        client = ApiClientFT()
        services = (MenuServiceFT(client), OrderServiceFT(client))
        _service_cache[vendor] = services
        return services
    
    # Mock vendor no longer supported - use FoodTec with fallbacks
    logger.warning("[P2A] Mock vendor no longer supported, using FoodTec with fallbacks")
    client = ApiClientFT()
    services = (MenuServiceFT(client), OrderServiceFT(client))
    _service_cache["foodtec"] = services
    return services
