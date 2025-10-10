"""
Search tools for Orcha-2 MCP server
"""

from typing import List, Optional
from loguru import logger
from ..models.base import SearchResult, SearchResponse


async def search_menu_tool(
    query: str,
    orderType: str = "Pickup",
    vendor: Optional[str] = "foodtec",
    limit: int = 10
) -> SearchResponse:
    """Search menu items"""
    logger.info(f"🔍 Searching: '{query}' for {orderType}")
    
    # TODO: Implement BM25 search
    # For now, return simple results
    results = [
        SearchResult(
            item="Chicken Wings",
            category="Appetizers",
            score=0.95,
            snippet="Crispy wings with sauce"
        )
    ]
    
    return SearchResponse(
        results=results,
        query=query,
        total=len(results),
        searchTime=0.05
    )