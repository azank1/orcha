from __future__ import annotations
import os
from typing import Optional

from api_client_ft import ApiClientFT
from menu_service_ft import MenuServiceFT
from order_service_ft import OrderServiceFT
from order_service_mock import OrderServiceMock
from menu_service_mock_export import MenuServiceExportMock

# Mock fallbacks (if available)
try:
    from core.services.menu.menu_service_mock import MenuServiceMock  # type: ignore
except Exception:  # pragma: no cover
    MenuServiceMock = None


def get_services(vendor: Optional[str] = None):
    vendor = (vendor or os.getenv("P2A_VENDOR", "mock")).lower()
    if vendor == "foodtec":
        client = ApiClientFT()
        return MenuServiceFT(client), OrderServiceFT(client)
    # default to mock
    if MenuServiceMock is None:
        raise RuntimeError("Mock services not available; set P2A_VENDOR=foodtec with valid env vars.")
    # Use export-shaped mock for menu export contract
    return MenuServiceExportMock(), OrderServiceMock()
