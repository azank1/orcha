import contextlib
import os
from starlette.applications import Starlette
from starlette.routing import Mount
from dotenv import load_dotenv
from core.mcp.menu_mcp import mcp as menu_mcp
from core.mcp.order_mcp import mcp as order_mcp
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application configuration
APP_NAME = "RP2A MCP"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Restaurant POS Agent Adapter MCP Server"


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(menu_mcp.session_manager.run())
        await stack.enter_async_context(order_mcp.session_manager.run())
        yield


app = Starlette(
    routes=[
        Mount(
            "/menu",
            app=menu_mcp.streamable_http_app(),
        ),
        Mount("/order", app=order_mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
