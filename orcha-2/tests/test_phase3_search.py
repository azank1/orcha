import asyncio
from mcp.tools import orders_search

async def main():
    res = await orders_search.invoke("pizza")
    assert isinstance(res, list)
    print("Results:", res[:3])

if __name__ == "__main__":
    asyncio.run(main())
