from typing import cast
from models.base.agent import Agent, Vendor
from core.services.menu.menu_service_ft import MenuServiceFT
from core.services.menu.menu_service import MenuService
from core.services.auth_service import AuthResolver, AuthService, BasicAuth

class MenuServiceResolver:

    def __init__(self, agent: Agent):
        self._agent = agent

    def resolve(self) -> MenuService:
        auth = AuthResolver(self._agent).resolve()
        if self._agent.vendor == Vendor.foodtec:  
            return MenuServiceFT(auth=cast(BasicAuth, auth))
        else:
            raise NotImplementedError(f"MenuService for vendor {self._agent.vendor} is not implemented")