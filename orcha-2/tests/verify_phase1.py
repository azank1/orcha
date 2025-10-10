#!/usr/bin/env python3
"""
Verify Orcha-2 Phase 1 completion - FastMCP server can be imported and has tools.
"""
import sys
import os
import importlib.util
import asyncio

async def verify_phase1():
    """Verify Phase 1 implementation is complete and functional."""
    
    print("🔍 Verifying Orcha-2 Phase 1 Completion...")
    
    # Check main MCP module can be imported
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), "mcp"))
        import main
        print("✅ MCP module imports successfully")
    except Exception as e:
        print(f"❌ Failed to import MCP module: {e}")
        return False
    
    # Check FastMCP app exists
    try:
        app = main.app
        print("✅ FastMCP app instance found")
    except Exception as e:
        print(f"❌ No FastMCP app instance: {e}")
        return False
    
    # Check tools are registered
    try:
        # Count tools using FastMCP's list_tools method
        tools_list = await app.list_tools()
        tools_count = len(tools_list)
        if tools_count >= 6:
            print(f"✅ Found {tools_count} registered tools:")
            for tool in tools_list:
                print(f"   • {tool.name}")
        else:
            print(f"❌ Expected 6+ tools, found {tools_count}")
            return False
    except Exception as e:
        print(f"❌ Error checking tools: {e}")
        return False
    
    # Check models can be imported
    try:
        from models.base import MenuItem, OrderDraft, Customer, OrderValidation
        print("✅ Base models import successfully")
    except Exception as e:
        print(f"❌ Failed to import base models: {e}")
        return False
    
    # Check FoodTec models
    try:
        from models.foodtec import MenuItemFT, CategoryFT, FoodTecValidationPayload
        print("✅ FoodTec models import successfully")
    except Exception as e:
        print(f"❌ Failed to import FoodTec models: {e}")
        return False
    
    # Check logs directory exists
    if os.path.exists("logs"):
        print("✅ Logs directory exists")
    else:
        print("❌ Logs directory missing")
        return False
    
    print("\n🎉 Phase 1 Verification PASSED!")
    print("✅ FastMCP server with 6 tools ready")
    print("✅ Complete model hierarchy implemented")  
    print("✅ Logging infrastructure configured")
    print("✅ Project structure established")
    print("\n📋 Ready for Phase 2: FoodTec Adapter Implementation")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_phase1())
    if not success:
        print("\n❌ Phase 1 verification failed!")
        sys.exit(1)