from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from typing import List
from models.base.agent import Agent
from models.base.menu_models import MenuItem, OrderType, Special
from core.services.auth_service import AgentAuth
from core.services.menu.menu_sevice_resolver import MenuServiceResolver


mcp = FastMCP(
    name="MenuProvider",
    instructions="""
        This server provides menu data to the order taking AI agent.
        It should be used to fetch accurate menu details, including categories, items, sizes, prices, ingredients, and specials.
    """,
    streamable_http_path="/",
)


@mcp.add_tool
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
    print("Headers in get_categories:", headers)
    auth_header = headers.get("authorization")
    print("Authorization header in get_categories:", auth_header)

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_categories(orderType)


@mcp.add_tool
async def get_order_types() -> List[OrderType]:
    """
    Purpose:
        Return the list of available order types supported by the restaurant.

    Output schema:
        - A JSON array of OrderType objects with orderType and requiresAddress fields.

    Usage notes for an order-taking AI agent:
        - Use this to determine what order types are available (e.g., "Delivery", "Pickup", "Dine In").
        - Check requiresAddress to know if you need to collect customer address for the order type.
        - Present these options to customers when they haven't specified their preferred order type.

    Error behavior:
        - On failures, inform the caller that order types are temporarily unavailable.
    """
    headers = get_http_headers()
    auth_header = headers.get("authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_order_types()


@mcp.add_tool
async def get_category_items(category: str, orderType: str) -> List[str]:
    """
    Purpose:
        Return the list of menu items available within a specific category for a given order type.

    Parameters:
        - `category` (str): The menu category name
        - `orderType` (str): The order context

    Output schema:
        - A JSON array of item names (strings). Example: ["Margherita Pizza", "BBQ Chicken Pizza"]

    Usage notes for an order-taking AI agent:
        - Use this after a customer has selected a category to show available items.
        - Validate customer's item selection against this authoritative list.
        - Items may vary by order type (some items may not be available for delivery vs pickup).

    Error behavior:
        - If category doesn't exist, return an empty list.
        - On transient failures, inform the caller that the menu is temporarily unavailable.
    """
    headers = get_http_headers()
    auth_header = headers.get("authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_category_items(category, orderType)


@mcp.add_tool
async def get_item_details(item: str, category: str, orderType: str) -> MenuItem:
    """
    Purpose:
        Return detailed information about a specific menu item including sizes, prices, and available choices.

    Parameters:
        - `item` (str): The menu item name
        - `category` (str): The category the item belongs to
        - `orderType` (str): The order context

    Output schema:
        - A MenuItem object with item details, size/price combinations, and choice groups (toppings, crusts, etc.)

    Usage notes for an order-taking AI agent:
        - Use this when a customer wants to order a specific item to get pricing and customization options.
        - Present size options and let customer choose before showing toppings/choices.
        - Use the choices array to guide customers through customization (toppings, crust type, etc.).
        - Check enforcedIngredients in each choice to know how many selections are required.

    Error behavior:
        - If item doesn't exist in the category, raise an appropriate error.
        - On transient failures, inform the caller that item details are temporarily unavailable.
    """
    headers = get_http_headers()
    auth_header = headers.get("authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_item_details(item, category, orderType)


@mcp.add_tool
async def get_specials(orderType: str) -> List[str]:
    """
    Purpose:
        Return the list of current specials/deals available for a given order type.

    Parameters:
        - `orderType` (str): The order context

    Output schema:
        - A JSON array of special names (strings). Example: ["$10 Off Any Order", "Buy 2 Get 1 Free Pizza"]

    Usage notes for an order-taking AI agent:
        - Use this to inform customers about current deals and promotions.
        - Present specials early in the conversation to maximize value for customers.
        - Get detailed information using get_special_details if customer shows interest.

    Caching and freshness:
        - Specials change more frequently than menu items, cache for no more than 2 minutes.

    Error behavior:
        - If no specials are available, return an empty list.
        - On transient failures, inform the caller that specials are temporarily unavailable.
    """
    headers = get_http_headers()
    auth_header = headers.get("authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_specials(orderType)


@mcp.add_tool
async def get_special_details(special: str, orderType: str) -> Special:
    """
    Purpose:
        Return detailed information about a specific special/deal including terms, validity, and requirements.

    Parameters:
        - `special` (str): The special/deal name
        - `orderType` (str): The order context

    Output schema:
        - A Special object with complete details including description, type, validity period, and terms.

    Usage notes for an order-taking AI agent:
        - Use this when a customer expresses interest in a specific deal.
        - Check the start/end times to ensure the special is currently valid.
        - Present any disclaimer or terms clearly to the customer.
        - If the special has a code, inform the customer it will be applied automatically.
        - Check if it's a combo deal (isCombo) as this may affect how it's applied.

    Error behavior:
        - If special doesn't exist, raise an appropriate error.
        - On transient failures, inform the caller that special details are temporarily unavailable.
    """
    headers = get_http_headers()
    auth_header = headers.get("authorization")

    if auth_header is None:
        raise PermissionError("Not authorized: Missing Authorization header")

    agent_auth = AgentAuth(token=auth_header)
    agent: Agent = agent_auth.get_agent()
    idem = headers.get("Idempotency-Key")
    menu_service = MenuServiceResolver(agent=agent).resolve(idem=idem)
    return await menu_service.get_special_details(special, orderType)
