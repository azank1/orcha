"""
Ordering flow workflow for FoodTec integration
"""
import uuid
import sys
import os
import json
from typing import Dict, Any

# Ensure the parent directory is in the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the client
from clients.mcp_client import MCPClient

def run_order_flow() -> dict:
    """
    Run the complete ordering flow:
    1. Export menu
    2. Build draft order with first item
    3. Validate order
    4. Accept order with canonical price
    
    Returns:
        Dict with summary of the workflow execution
    """
    # Initialize the MCP client
    client = MCPClient("http://127.0.0.1:9090/rpc")
    
    # Step 1: Export menu
    print("Exporting menu...")
    menu_response = client.call("foodtec.export_menu", {"orderType": "Pickup"})
    
    # Extract menu data
    menu_data = menu_response.get("result", {})
    menu_categories = []
    
    # Handle different response formats
    if "data" in menu_data and isinstance(menu_data["data"], list):
        menu_categories = menu_data["data"]
    elif "raw" in menu_data:
        try:
            # Parse raw data if it's a string
            if isinstance(menu_data["raw"], str):
                menu_categories = json.loads(menu_data["raw"])
            else:
                menu_categories = menu_data["raw"]
        except Exception as e:
            print(f"Failed to parse menu data: {e}")
            menu_categories = []
    
    if not menu_categories:
        raise ValueError("Failed to extract menu categories from response")
    
    # Extract the first item from the first category
    first_category = menu_categories[0]
    first_item = first_category["items"][0]
    
    # Extract item name and category (using correct keys from FoodTec response)
    item_name = first_item.get("item", "Unknown Item")
    category_name = first_category.get("category", "Unknown Category")
    
    # Find size and price (using sizePrices key)
    size = "Reg"
    price = 0.00
    if "sizePrices" in first_item and first_item["sizePrices"]:
        size = first_item["sizePrices"][0].get("size", "Reg")
        price = first_item["sizePrices"][0].get("price", 0.00)
    
    # Step 2: Create draft order (simple format for proxy)
    # The proxy will handle converting this to full FoodTec format
    draft_order = {
        "category": category_name,
        "item": item_name,
        "size": size,
        "price": price,
        "customer": {
            "name": "Test Customer",
            "phone": "410-555-1234"
        }
    }

    # Step 3: Validate the order
    print(f"Validating order with item: {item_name}...")
    validation_response = client.call("foodtec.validate_order", draft_order)    # Extract canonical price from validation response
    canonical_price = None
    validation_status = 0
    
    if "result" in validation_response:
        result = validation_response["result"]
        validation_status = result.get("status", 0)
        
        # Try different possible locations for the price
        if "response" in result and "price" in result["response"]:
            canonical_price = result["response"]["price"]
        elif "price" in result:
            canonical_price = result["price"]
        elif "data" in result and "price" in result["data"]:
            canonical_price = result["data"]["price"]
    
    print(f"Validation OK - Canonical price: ${canonical_price}")
    
    # Step 4: Accept the order
    # Create acceptance payload (proxy expects same simple format)
    acceptance_payload = draft_order.copy()
    
    # Update with canonical price if available
    if canonical_price is not None:
        acceptance_payload["price"] = canonical_price
    
    print(f"Accepting order...")
    acceptance_response = client.call(
        "foodtec.accept_order", 
        acceptance_payload,
        idempotency_key=f"idem-{uuid.uuid4()}"
    )
    
    # Prepare the summary
    return {
        "menu_preview": {
            "categories": len(menu_categories),
            "first_item": {
                "category": category_name,
                "item": item_name,
                "size": size,
                "price": price
            }
        },
        "validation_status": validation_status,
        "canonical_price": canonical_price,
        "acceptance_status": acceptance_response.get("result", {}).get("status", 0),
        "draft_payload": draft_order,
        "acceptance_payload": acceptance_payload,
        "acceptance_response": acceptance_response
    }