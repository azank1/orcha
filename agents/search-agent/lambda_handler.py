from mangum import Mangum
from server import mcp

# FastMCP SSE transport — sse_app() returns a Starlette ASGI app
handler = Mangum(mcp.sse_app(), lifespan="off")
