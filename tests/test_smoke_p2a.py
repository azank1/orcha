#!/usr/bin/env python3
"""
Root-level P2A smoke test - Direct FoodTec API integration test.
Tests P2A package directly without proxy layer.
"""
import sys
import os
from pathlib import Path

# Add P2A to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from P2A.core.menu_service import MenuService
from P2A.core.order_service import OrderService

def test_p2a_direct():
    """Test P2A package directly against FoodTec API."""
    print("-- P2A Direct API Test")
    print("=" * 40)
    
    try:
        # Initialize services
        menu_service = MenuService()
        order_service = OrderService()
        
        # Test 1: Menu Export
        print(" Testing Menu Export...")
        menu_result = menu_service.export_menu("Pickup")
        
        if not menu_result["success"]:
            print(f"❌ Menu export failed: {menu_result['raw'][:200]}")
            return False
            
        categories_count = len(menu_result["data"]) if menu_result["data"] else 0
        print(f"   ✅ Status {menu_result['status']}, {categories_count} categories")
        
        # Pick first item for testing
        item = menu_service.pick_first_item(menu_result["data"])
        if not item:
            print("❌ No valid item found in menu")
            return False
            
        print(f"   📋 Selected: {item['item']} ({item['size']}) - ${item['price']}")
        
        # Test 2: Order Validation
        print("\n2️⃣ Testing Order Validation...")
        validation_result = order_service.validate_order(item)
        
        if not validation_result["success"]:
            print(f"❌ Validation failed: {validation_result['raw'][:200]}")
            return False
            
        canonical_price = validation_result["canonical_price"]
        print(f"   ✅ Status {validation_result['status']}, canonical price: ${canonical_price}")
        
        # Test 3: Order Acceptance
        print("\n3️⃣ Testing Order Acceptance...")
        acceptance_result = order_service.accept_order(
            validation_result["payload"], 
            canonical_price
        )
        
        if not acceptance_result["success"]:
            print(f"❌ Acceptance failed: {acceptance_result['raw'][:200]}")
            return False
            
        order_id = acceptance_result["data"].get("orderNum", "Unknown") if acceptance_result["data"] else "Unknown"
        print(f"   ✅ Status {acceptance_result['status']}, Order ID: {order_id}")
        
        print("\n🎯 P2A Direct API test passed!")
        return True
        
    except Exception as e:
        print(f"❌ P2A test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_p2a_direct()
    sys.exit(0 if success else 1)