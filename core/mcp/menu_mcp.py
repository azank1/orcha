from fastmcp import FastMCP
from typing import List

menu_mcp = FastMCP(
    name="MenuProvider",
    instructions="""
        This server provides menu data to the order taking AI agent.
        It should be used to fetch accurate menu details, including categories, items, sizes, prices, ingredients, and specials.
    """,
)

@menu_mcp.tool
async def get_categories() -> List[str]:
    """
    Purpose:
        Return the canonical list of menu categories currently available for ordering.

    Output schema:
        - A JSON array of category names (strings). Example: ["Pizza", "Burgers", "Salads"]

    Usage notes for an order-taking AI agent:
        - Use this to present the high-level menu categories to customers or to validate a customer's requested category.
        - Responses must be treated as authoritative; the agent should not invent categories not present in this list.
        - Categories should be normalized (title case) and unique.

    Caching and freshness:
        - Categories change rarely. Agents may cache results for up to 5 minutes, but should call this tool again if the menu was recently updated or after failed lookups.

    Error behavior:
        - On transient failures, inform the caller that the menu is temporarily unavailable.

    """
   
    return ["Pizza", "Burgers", "Salads", "Desserts"]