from core.services.auth_service import BasicAuth
from core.services.menu.menu_search_service import MenuSearchService
from core.services.menu.menu_service_ft import MenuServiceFT
import asyncio

menu_service = MenuServiceFT(
        auth=BasicAuth(
            username="apiclient",
            password="Tn2dtS6n4u5eVYk"
        )
    )

menu_search = MenuSearchService(
    menu_service=menu_service
)


async def main():

    # await menu_search.sync_indexes()

    available_cats = await menu_service.get_categories(orderType="Delivery")
    print(f"Available categories: {available_cats}")

    query = "pizzas"
    found_cats = await menu_search.simple_search_categories(query=query, orderType="Delivery", top_n=5)
    print(f"Search query: '{query}'")
    print(f"Found categories: {found_cats}")


asyncio.run(main())