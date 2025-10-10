#!/usr/bin/env python3
"""
Debug tool output formats to understand return structures
"""
import sys
import asyncio
import json
sys.path.insert(0, 'mcp')

import main

async def debug_tool_outputs():
    """Debug what each tool actually returns"""
    
    print("🔍 Debugging FastMCP Tool Output Formats...")
    
    # Test orders.get_menu
    print("\n1. Testing orders.get_menu:")
    try:
        result = await main.app.call_tool("orders.get_menu", {"vendor": "foodtec", "orderType": "Pickup"})
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test orders.search  
    print("\n2. Testing orders.search:")
    try:
        result = await main.app.call_tool("orders.search", {"query": "pizza", "vendor": "foodtec"})
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test system.health
    print("\n3. Testing system.health:")
    try:
        result = await main.app.call_tool("system.health", {})
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tool_outputs())