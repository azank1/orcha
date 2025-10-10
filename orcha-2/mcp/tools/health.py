"""
Health check tools for Orcha-2 MCP server
"""

from typing import Dict, Any
from loguru import logger


async def health_check_tool() -> Dict[str, Any]:
    """System health check"""
    logger.info("💗 Health check")
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "mcp_server": {"status": "up"},
            "search_index": {"status": "up", "items": 0}
        }
    }