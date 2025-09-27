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
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        for category in menu_result["data"]:
            if category.get("items"):
                for item in category["items"]:
                    if item.get("sizes"):
                        test_item = {
                            "category": category["name"],
                            "item": item["name"],
                            "size": item["sizes"][0]["name"],
                            "price": item["sizes"][0]["price"]
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
        validation_result = order_service.validate_order({
            "phone": "410-555-1234",
            "category": test_item["category"],
            "item_name": test_item["item"],
            "size_name": test_item["size"],
            "original_price": test_item["price"],
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
        
        acceptance_result = order_service.accept_order({
            "phone": "410-555-1234", 
            "category": test_item["category"],
            "item_name": test_item["item"],
            "size_name": test_item["size"],
            "canonical_price": canonical_price,
            "external_ref": external_ref
        })
        
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