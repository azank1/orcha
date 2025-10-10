#!/usr/bin/env python3
"""
Low-level FastMCP tool testing - verify each tool works independently
"""
import sys
import asyncio
import json
sys.path.insert(0, 'mcp')

import main

async def test_individual_tools():
    """Test each MCP tool directly via FastMCP call_tool method"""
    
    print("🔧 Testing Individual FastMCP Tools...")
    
    # Test 1: orders.get_menu
    try:
        result = await main.app.call_tool("orders.get_menu", {"vendor": "foodtec", "orderType": "Pickup"})
        print(f"✅ orders.get_menu: {len(result.get('categories', []))} categories returned")
    except Exception as e:
        print(f"❌ orders.get_menu failed: {e}")
        return False
    
    # Test 2: orders.search
    try:
        result = await main.app.call_tool("orders.search", {"query": "pizza", "vendor": "foodtec"})
        print(f"✅ orders.search: {len(result.get('results', []))} results returned")
    except Exception as e:
        print(f"❌ orders.search failed: {e}")
        return False
    
    # Test 3: orders.prepare_draft
    try:
        result = await main.app.call_tool("orders.prepare_draft", {
            "item": "Margherita Pizza", 
            "category": "Pizza", 
            "size": "Large",
            "quantity": 2
        })
        print(f"✅ orders.prepare_draft: Draft with {result.get('quantity', 0)} items created")
    except Exception as e:
        print(f"❌ orders.prepare_draft failed: {e}")
        return False
    
    # Test 4: orders.validate
    try:
        draft = {"item": "test", "quantity": 1, "vendor": "foodtec"}
        result = await main.app.call_tool("orders.validate", {"order_draft": draft})
        print(f"✅ orders.validate: Status '{result.get('status', 'unknown')}'")
    except Exception as e:
        print(f"❌ orders.validate failed: {e}")
        return False
    
    # Test 5: orders.submit
    try:
        validation = {"status": "valid", "total": 12.99}
        result = await main.app.call_tool("orders.submit", {"order_validation": validation})
        print(f"✅ orders.submit: Order #{result.get('order_number', 'unknown')}")
    except Exception as e:
        print(f"❌ orders.submit failed: {e}")
        return False
    
    # Test 6: system.health
    try:
        result = await main.app.call_tool("system.health", {})
        print(f"✅ system.health: Status '{result.get('status', 'unknown')}'")
    except Exception as e:
        print(f"❌ system.health failed: {e}")
        return False
    
    print("\n🎉 All 6 tools passed individual testing!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_individual_tools())
    if success:
        print("✅ FastMCP tool functionality verified!")
    else:
        print("❌ Some tools failed testing!")
        sys.exit(1)