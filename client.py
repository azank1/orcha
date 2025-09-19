import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# HTTP server
client = Client(
    transport=StreamableHttpTransport(
        "http://localhost:8080/menu",
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiTWFyayIsInJvbGUiOiJtZW51SGVscGVyIiwicGxhdGZvcm0iOiJuOG4iLCJ2ZW5kb3IiOiJmb29kdGVjIiwiY3JlZGVudGlhbHMiOnsidXNlcm5hbWUiOiJhcGljbGllbnQiLCJwYXNzd29yZCI6IlRuMmR0UzZuNHU1ZVZZayJ9fQ.-E988ybXHVyKSWJTp4LTtf0967X5CMI4tTPtzx_3Scw"
        },
    )
)


async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        # resources = await client.list_resources()
        # prompts = await client.list_prompts()

        # Execute operations
        result = await client.call_tool("get_order_types")
        print(result)


asyncio.run(main())
