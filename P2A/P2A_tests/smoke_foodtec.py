#!/usr/bin/env python3
"""
P2A FoodTec Integration Smoke Test - Direct API testing.
"""
import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

# Add parent directory to path for P2A package imports
parent_dir = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, parent_dir)

from P2A.core.menu_service import MenuService
from P2A.core.order_service import OrderService


def test_p2a_integration():
    """Test P2A package integration with FoodTec API."""
    print("P2A FoodTec Integration Smoke Test")
    print("==================================================")
    
    try:
        menu_service = MenuService()
        order_service = OrderService()
        
        # Test 1: Menu Export
        print("[1] Testing menu export...")
        menu_result = menu_service.export_menu("Pickup")
        
        if not menu_result["success"]:
            print(f"FAIL: Menu export failed: Status {menu_result['status']}")
            return False
            
        categories_count = len(menu_result["data"])
        print(f"PASS: Menu export successful: {categories_count} categories")
        
        # Find a valid item for testing
        test_item = None
        print(f"DEBUG: Menu structure: {json.dumps(menu_result['data'][0], indent=2)[:200]}...")
        
        # Let's examine the actual structure of the menu data
        for category in menu_result["data"]:
            print(f"Category: {category.get('category', 'Unknown')}")
            if category.get("items"):
                for item in category["items"]:
                    # Check different possible structures
                    if item.get("sizePrices") and len(item.get("sizePrices", [])) > 0:
                        test_item = {
                            "category": category.get("category", ""),
                            "item": item.get("item", ""),
                            "size": item["sizePrices"][0].get("size", ""),
                            "price": item["sizePrices"][0].get("price", 0)
                        }
                        break
                if test_item:
                    break
        
        if not test_item:
            print("FAIL: No valid item found in menu")
            return False
            
        print(f"Selected: {test_item['item']} ({test_item['size']}) - ${test_item['price']}")
        
        # Test 2: Order Validation
        print("[2] Testing order validation...")
        # Let's print out the test item to see what we're working with
        print(f"Debug - Test Item: {json.dumps(test_item)}")
        
        validation_result = order_service.validate_order({
            "phone": "410-555-1234",
            "item": test_item["item"],  # Using "item" instead of "item_name"
            "category": test_item["category"],
            "size": test_item["size"],  # Using "size" instead of "size_name"
            "price": test_item["price"],  # Using "price" instead of "original_price"
            "external_ref": f"smoke-test-{datetime.now().timestamp()}"
        })
        
        if not validation_result["success"]:
            print(f"FAIL: Order validation failed: Status {validation_result['status']}")
            return False
            
        canonical_price = validation_result["canonical_price"]
        print(f"PASS: Order validation successful: canonical price ${canonical_price}")
        
        # Test 3: Order Acceptance
        print("[3] Testing order acceptance...")
        external_ref = f"smoke-test-accept-{datetime.now().timestamp()}"
        
        # Build validation payload for reuse in acceptance
        validation_payload = {
            "type": "To Go",
            "source": "Voice",
            "externalRef": external_ref,
            "customer": {"name": "Test Customer", "phone": "410-555-1234"},
            "items": [{
                "item": test_item["item"],
                "category": test_item["category"],
                "size": test_item["size"],
                "quantity": 1,
                "externalRef": f"{external_ref}-i1",
                "sellingPrice": test_item["price"]
            }]
        }
        
        # Call accept_order with the expected parameters
        acceptance_result = order_service.accept_order(validation_payload, canonical_price)
        
        if not acceptance_result["success"]:
            print(f"FAIL: Order acceptance failed: Status {acceptance_result['status']}")
            return False
            
        order_id = acceptance_result["data"].get("orderNum", "Unknown") if acceptance_result["data"] else "Unknown"
        print(f"PASS: Order acceptance successful: Order ID {order_id}")
        
        print("\nAll tests passed! P2A package is working correctly.")
        return True
        
    except Exception as e:
        print(f"FAIL: Smoke test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_p2a_integration()
    sys.exit(0 if success else 1)