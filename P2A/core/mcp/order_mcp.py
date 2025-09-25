from mcp.server import FastMCP
from typing import List
from models.base.agent import Agent
from core.services.auth_service import AgentAuth
from core.services.menu.menu_sevice_resolver import MenuServiceResolver


mcp = FastMCP(
    name="OrderHelper",
    instructions="""
        This server provides tools to validate and place orders based on menu data.
    """,
    streamable_http_path='/'
)


