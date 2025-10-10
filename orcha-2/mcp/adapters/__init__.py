"""
Adapter Factory for Orcha-2
Provides vendor-agnostic interface for POS system integration
"""
from typing import Dict, Any, Protocol
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger


class VendorType(Enum):
    """Supported POS vendor types"""
    FOODTEC = "foodtec"
    SQUARE = "square"
    TOAST = "toast"
    MOCK = "mock"


class POSAdapter(Protocol):
    """
    Protocol defining the interface that all POS adapters must implement
    This ensures consistent behavior across different vendor integrations
    """
    
    async def fetch_menu(self, store_id: str = "default") -> Dict[str, Any]:
        """Fetch menu from POS system"""
        ...
    
    async def validate_order(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order with POS system"""
        ...
    
    async def accept_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Submit order to POS system"""
        ...
    
    async def close(self) -> None:
        """Clean up adapter resources"""
        ...


class MockAdapter:
    """
    Mock adapter for testing and development
    Returns predefined responses without external API calls
    """
    
    async def fetch_menu(self, store_id: str = "default") -> Dict[str, Any]:
        """Return mock menu data"""
        logger.info("🧪 Mock adapter returning test menu")
        return {
            "categories": [
                {
                    "category": "Pizza",
                    "items": [
                        {
                            "item": "Margherita Pizza",
                            "code": "MARG_PIZZA",
                            "sizePrices": [
                                {"size": "Small", "price": 12.99},
                                {"size": "Medium", "price": 15.99},
                                {"size": "Large", "price": 18.99}
                            ],
                            "choices": [
                                {"choice": "Extra Cheese", "price": 2.00},
                                {"choice": "Pepperoni", "price": 1.50}
                            ],
                            "category": "Pizza"
                        }
                    ]
                }
            ],
            "orderTypes": [
                {"orderType": "Pickup", "requiresAddress": False},
                {"orderType": "Delivery", "requiresAddress": True}
            ]
        }
    
    async def validate_order(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock validation response"""
        logger.info("🧪 Mock adapter validating order")
        return {
            "success": True,
            "canonicalPrice": 25.99,
            "orderDraft": draft,
            "validationErrors": [],
            "externalRef": "MOCK_REF_12345"
        }
    
    async def accept_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock acceptance response"""
        logger.info("🧪 Mock adapter accepting order")
        return {
            "success": True,
            "order_number": "MOCK_ORDER_001",
            "confirmation": {"status": "accepted"},
            "estimatedTime": 25,
            "externalRef": "MOCK_REF_12345"
        }
    
    async def close(self):
        """Mock cleanup"""
        logger.info("🧪 Mock adapter closed")


class AdapterFactory:
    """
    Factory class for creating POS adapter instances
    Centralizes vendor selection and configuration
    """
    
    _adapters = {}
    
    @classmethod
    def create_adapter(cls, vendor: VendorType) -> POSAdapter:
        """
        Create and return a POS adapter for the specified vendor
        
        Args:
            vendor: The POS vendor type to create adapter for
            
        Returns:
            Configured adapter instance
            
        Raises:
            ValueError: If vendor type is not supported
        """
        if vendor in cls._adapters:
            return cls._adapters[vendor]
        
        logger.info(f"🏭 Creating {vendor.value} adapter")
        
        if vendor == VendorType.FOODTEC:
            try:
                from .foodtec_adapter import FoodTecAdapter
                adapter = FoodTecAdapter()
                cls._adapters[vendor] = adapter
                return adapter
            except ImportError as e:
                logger.error(f"❌ Failed to import FoodTecAdapter: {e}")
                logger.info("🔄 Falling back to MockAdapter")
                return cls._create_mock_adapter()
        
        elif vendor == VendorType.MOCK:
            return cls._create_mock_adapter()
        
        else:
            logger.warning(f"⚠️ Unsupported vendor: {vendor.value}")
            raise ValueError(f"Unsupported vendor type: {vendor.value}")
    
    @classmethod
    def _create_mock_adapter(cls) -> MockAdapter:
        """Create and cache mock adapter"""
        if VendorType.MOCK not in cls._adapters:
            cls._adapters[VendorType.MOCK] = MockAdapter()
        return cls._adapters[VendorType.MOCK]
    
    @classmethod
    def get_default_vendor(cls) -> VendorType:
        """
        Get the default vendor type from environment or fallback
        
        Returns:
            Default vendor type for adapter creation
        """
        import os
        vendor_name = os.getenv("DEFAULT_VENDOR", "mock").lower()
        
        try:
            return VendorType(vendor_name)
        except ValueError:
            logger.warning(f"⚠️ Invalid DEFAULT_VENDOR '{vendor_name}', using mock")
            return VendorType.MOCK
    
    @classmethod
    async def close_all_adapters(cls):
        """Close all cached adapter connections"""
        for vendor, adapter in cls._adapters.items():
            try:
                await adapter.close()
                logger.info(f"✅ Closed {vendor.value} adapter")
            except Exception as e:
                logger.error(f"❌ Error closing {vendor.value} adapter: {e}")
        
        cls._adapters.clear()


# Convenience function for easy adapter creation
def get_pos_adapter(vendor: VendorType = None) -> POSAdapter:
    """
    Get a POS adapter instance
    
    Args:
        vendor: Specific vendor type, or None for default
        
    Returns:
        Configured adapter instance
    """
    if vendor is None:
        vendor = AdapterFactory.get_default_vendor()
    
    return AdapterFactory.create_adapter(vendor)