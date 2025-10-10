#!/usr/bin/env python3
"""
Phase 2 Integration Test
Verifies FoodTec adapter integration with MCP tools
"""
import asyncio
import sys
import os

# Add the parent directory to path to import mcp modules
test_dir = os.path.dirname(os.path.abspath(__file__))
orcha_dir = os.path.dirname(test_dir)
mcp_dir = os.path.join(orcha_dir, "mcp")
sys.path.insert(0, orcha_dir)
sys.path.insert(0, mcp_dir)

from loguru import logger
from adapters import get_pos_adapter, VendorType, AdapterFactory
from models.base import OrderDraft, Customer, OrderItem
import json

logger.add("logs/phase2_integration.log", rotation="1 day", level="DEBUG")

async def test_foodtec_adapter():
    """Test FoodTec adapter directly"""
    logger.info("🧪 Testing FoodTec adapter directly...")
    
    try:
        # Test 1: Create FoodTec adapter
        logger.info("📡 Creating FoodTec adapter...")
        adapter = get_pos_adapter(VendorType.FOODTEC)
        
        # Test 2: Fetch menu
        logger.info("📋 Testing menu fetch...")
        menu_data = await adapter.fetch_menu()
        
        print(f"✅ Menu fetch successful:")
        print(f"   Categories: {len(menu_data.get('categories', []))}")
        print(f"   Order types: {len(menu_data.get('orderTypes', []))}")
        
        # Test 3: Validate order (using mock data)
        logger.info("🔍 Testing order validation...")
        test_order = {
            "type": "To Go",
            "source": "API",
            "customer": {
                "name": "Test Customer", 
                "phone": "410-555-1234"
            },
            "items": [
                {
                    "item": "Margherita Pizza",
                    "category": "Pizza",
                    "size": "Small",
                    "quantity": 1,
                    "sellingPrice": 12.99
                }
            ]
        }
        
        validation_data = await adapter.validate_order(test_order)
        
        print(f"✅ Order validation successful:")
        print(f"   Success: {validation_data.get('success', False)}")
        print(f"   Price: ${validation_data.get('canonicalPrice', 0)}")
        
        # Test 4: Accept order (if validation passes)
        if validation_data.get("success"):
            logger.info("📤 Testing order submission...")
            submission_data = await adapter.accept_order(test_order)
            
            print(f"✅ Order submission successful:")
            print(f"   Success: {submission_data.get('success', False)}")
            print(f"   Order number: {submission_data.get('order_number', 'N/A')}")
        
        await adapter.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ FoodTec adapter test failed: {e}")
        print(f"❌ FoodTec adapter test failed: {e}")
        return False

async def test_mcp_tools_integration():
    """Test MCP tools with adapter integration"""
    logger.info("🧪 Testing MCP tools integration...")
    
    try:
        # Import MCP tools
        from main import get_menu, validate_order, submit_order, health_check
        
        # Test 1: Health check
        logger.info("💗 Testing health check...")
        health = await health_check()
        
        print(f"✅ Health check:")
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Services: {list(health.get('services', {}).keys())}")
        
        # Test 2: Get menu via MCP tool
        logger.info("📋 Testing MCP get_menu tool...")
        menu = await get_menu(orderType="Pickup", vendor="foodtec")
        
        print(f"✅ MCP get_menu successful:")
        print(f"   Categories: {len(menu.categories)}")
        print(f"   Order types: {len(menu.orderTypes)}")
        
        # Test 3: Validate order via MCP tool
        logger.info("🔍 Testing MCP validate_order tool...")
        test_draft = {
            "type": "To Go",
            "source": "Voice",
            "customer": {
                "name": "Integration Test",
                "phone": "410-555-TEST"
            },
            "items": [
                {
                    "item": "Margherita Pizza",
                    "category": "Pizza",
                    "size": "Small",
                    "quantity": 1,
                    "sellingPrice": 12.99,
                    "externalRef": "test-item-001"
                }
            ],
            "externalRef": "test-order-001"
        }
        
        validation = await validate_order(test_draft, vendor="foodtec")
        
        print(f"✅ MCP validate_order successful:")
        print(f"   Success: {validation.success}")
        print(f"   Price: ${validation.canonicalPrice}")
        print(f"   Errors: {len(validation.validationErrors)}")
        
        # Test 4: Submit order via MCP tool (if validation passes)
        if validation.success:
            logger.info("📤 Testing MCP submit_order tool...")
            submission = await submit_order(validation.model_dump(), vendor="foodtec")
            
            print(f"✅ MCP submit_order successful:")
            print(f"   Success: {submission.success}")
            print(f"   Order number: {submission.orderNumber}")
            print(f"   Errors: {len(submission.errors)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP tools integration test failed: {e}")
        print(f"❌ MCP tools integration test failed: {e}")
        return False

async def test_mock_fallback():
    """Test mock adapter fallback"""
    logger.info("🧪 Testing mock adapter fallback...")
    
    try:
        # Force mock adapter
        mock_adapter = get_pos_adapter(VendorType.MOCK)
        
        # Test all operations with mock
        menu_data = await mock_adapter.fetch_menu()
        
        test_order = {
            "type": "To Go",
            "customer": {"name": "Mock Test", "phone": "555-MOCK"},
            "items": [{"item": "Test Item", "quantity": 1}]
        }
        
        validation_data = await mock_adapter.validate_order(test_order)
        submission_data = await mock_adapter.accept_order(test_order)
        
        print(f"✅ Mock adapter fallback working:")
        print(f"   Menu categories: {len(menu_data.get('categories', []))}")
        print(f"   Validation success: {validation_data.get('success', False)}")
        print(f"   Submission success: {submission_data.get('success', False)}")
        
        await mock_adapter.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock fallback test failed: {e}")
        print(f"❌ Mock fallback test failed: {e}")
        return False

async def main():
    """Run all Phase 2 integration tests"""
    print("🚀 Phase 2 Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Mock Adapter Fallback", test_mock_fallback),
        ("FoodTec Adapter Direct", test_foodtec_adapter),
        ("MCP Tools Integration", test_mcp_tools_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            success = await test_func()
            results[test_name] = success
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            print(f"💥 {test_name} CRASHED: {e}")
            results[test_name] = False
    
    # Final summary
    print(f"\n📊 Phase 2 Integration Test Results")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 integration tests PASSED!")
        logger.info("🎉 Phase 2 integration verification complete - ALL TESTS PASSED")
    else:
        print(f"⚠️ {total - passed} tests failed")
        logger.warning(f"⚠️ Phase 2 integration had {total - passed} failures")
    
    # Cleanup
    await AdapterFactory.close_all_adapters()

if __name__ == "__main__":
    asyncio.run(main())