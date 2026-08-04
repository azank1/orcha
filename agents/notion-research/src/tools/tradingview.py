"""TradingView chart embedding tool"""
import structlog
from typing import Dict, Any, List, Optional
from notion_client import AsyncClient
from ..config import settings

logger = structlog.get_logger()


def generate_tradingview_widget(
    symbol: str,
    interval: str = "1D",
    chart_type: str = "candlestick",
    indicators: Optional[List[str]] = None,
    theme: str = "light"
) -> str:
    """
    Generate TradingView widget embed URL
    
    Args:
        symbol: Trading symbol
        interval: Chart interval
        chart_type: Chart visualization type
        indicators: List of technical indicators
        theme: Color theme
        
    Returns:
        TradingView embed URL
    """
    # Map chart types
    chart_map = {
        "candlestick": "1",
        "line": "2",
        "area": "3"
    }
    
    # Build widget URL
    base_url = "https://s.tradingview.com/widgetembed/"
    params = {
        "symbol": symbol,
        "interval": interval,
        "style": chart_map.get(chart_type, "1"),
        "theme": theme,
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": "false",
        "allow_symbol_change": "true",
        "save_image": "false",
        "hide_side_toolbar": "false"
    }
    
    # Add indicators if specified
    if indicators:
        indicator_map = {
            "RSI": "RSI@tv-basicstudies",
            "MACD": "MACD@tv-basicstudies",
            "BB": "BB@tv-basicstudies",
            "EMA": "EMA@tv-basicstudies",
            "SMA": "SMA@tv-basicstudies"
        }
        studies = [indicator_map.get(ind, ind) for ind in indicators if ind in indicator_map]
        params["studies"] = studies
    
    # Build URL
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    embed_url = f"{base_url}?{param_str}"
    
    return embed_url


async def add_tradingview_chart(
    page_id: str,
    symbol: str,
    oauth_token: str,
    interval: str = "1D",
    chart_type: str = "candlestick",
    indicators: Optional[List[str]] = None,
    theme: str = "light"
) -> Dict[str, Any]:
    """
    Add TradingView chart embedding to Notion page
    
    Args:
        page_id: Notion page ID
        symbol: Trading symbol
        oauth_token: Google OAuth token (for future auth)
        interval: Chart interval
        chart_type: Chart type
        indicators: Technical indicators
        theme: Chart theme
        
    Returns:
        Dict with embed status
    """
    logger.info("add_tradingview_chart", page_id=page_id, symbol=symbol)
    
    # Validate OAuth token (placeholder - in production, verify with Google)
    if not oauth_token or len(oauth_token) < 10:
        logger.warning("invalid_oauth_token")
        raise ValueError("Valid OAuth token required for TradingView access")
    
    # Generate widget embed URL
    embed_url = generate_tradingview_widget(
        symbol=symbol,
        interval=interval,
        chart_type=chart_type,
        indicators=indicators or [],
        theme=theme
    )
    
    # Initialize Notion client
    notion = AsyncClient(auth=settings.notion_api_key)
    
    try:
        # Create embed block
        block = {
            "object": "block",
            "type": "embed",
            "embed": {
                "url": embed_url
            }
        }
        
        # Add caption with metadata
        caption = f"TradingView: {symbol} ({interval}, {chart_type})"
        if indicators:
            caption += f" - Indicators: {', '.join(indicators)}"
        
        block["embed"]["caption"] = [
            {"type": "text", "text": {"content": caption}}
        ]
        
        # Append block to page
        await notion.blocks.children.append(
            block_id=page_id,
            children=[block]
        )
        
        logger.info("tradingview_chart_added", page_id=page_id, symbol=symbol)
        
        return {
            "status": "embedded",
            "page_id": page_id,
            "symbol": symbol,
            "embed_url": embed_url,
            "chart_type": chart_type,
            "indicators": indicators or []
        }
        
    except Exception as e:
        logger.error("tradingview_embed_error", error=str(e))
        raise Exception(f"Failed to add TradingView chart: {str(e)}")
