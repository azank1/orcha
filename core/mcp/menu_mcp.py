from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from typing import List
from models.base.agent import Agent
from services.auth_service import AgentAuth
from services.menu.menu_sevice_resolver import MenuServiceResolver


mcp = FastMCP(
    name="MenuProvider",
    instructions="""
        This server provides menu data to the order taking AI agent.
        It should be used to fetch accurate menu details, including categories, items, sizes, prices, ingredients, and specials.
    """,
)


@mcp.tool
async def get_categories(orderType: str) -> List[str]:
    """
    Purpose:
        Return the canonical list of menu categories currently available for ordering for
        a specific `orderType`.

    Parameters:
        - `orderType` (str): The order context

    Output schema:
        - A JSON array of category names (strings). Example: ["Pizza", "Burgers", "Salads"]

    Usage notes for an order-taking AI agent:
        - Use this to present high-level menu categories to customers or to validate a customer's requested category in the context of `orderType`.
        - Treat the response as authoritative for the given `orderType` and do not invent categories not present in this list.
        - Categories should be normalized (title case) and unique.

    Valid `orderType` values:
        - This depends on the store/system; common examples: "Delivery", "Pickup", "For Here", "Dine In".
        - The caller should provide the canonical order type value used by the system.

    Caching and freshness:
        - Categories change rarely. Agents may cache results for up to 5 minutes per `orderType`,
          but should call this tool again after menu updates or if a previous selection fails validation.

    Error behavior:
        - On transient failures, inform the caller that the menu is temporarily unavailable.
        - If there are no categories for the provided `orderType`, return an empty list.

    """

    headers = get_http_headers()
    auth_header = headers.get("Authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent: Agent = AgentAuth(token=auth_header).get_agent()

    menu_service = MenuServiceResolver(agent=agent).resolve()
    return await menu_service.get_categories(orderType)

