from typing import cast, Optional
from models.base.agent import Agent, Vendor
from core.services.menu.menu_service_ft import MenuServiceFT
from core.services.menu.menu_service import MenuService
from core.services.auth_service import AuthResolver, AuthService, BasicAuth

class MenuServiceResolver:

    def __init__(self, agent: Agent):
        self._agent = agent

    def resolve(self, idem: Optional[str] = None) -> MenuService:
        if self._agent.vendor == Vendor.foodtec:
            auth = AuthResolver(self._agent).resolve()
            return MenuServiceFT(auth=cast(BasicAuth, auth))
        elif str(self._agent.vendor) == 'mock' or getattr(Vendor, 'mock', None) == self._agent.vendor:
            # Mock service no longer available - use FoodTec with fallbacks
            auth = AuthResolver(self._agent).resolve()
            return MenuServiceFT(auth=cast(BasicAuth, auth))
        else:
            raise NotImplementedError(f"MenuService for vendor {self._agent.vendor} is not implemented")