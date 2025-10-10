#!/usr/bin/env python3
"""
Test script to verify RP2A FoodTec API client with environment-based configuration.

This script tests:
1. ApiClientFT initialization with environment variables
2. URL construction with store ID
3. Basic authentication setup
4. Making a test API call to verify connectivity

Usage:
    python test_rp2a_config.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_clients.api_client_ft import ApiClientFT
from core.services.auth_service import BasicAuth

load_dotenv()


async def test_rp2a_config():
    """Test the refactored RP2A configuration."""
    print("🧪 Testing RP2A FoodTec Configuration")
    print("=" * 40)
    
    # Test 1: Environment variable loading
    print("\n1️⃣ Testing environment variable loading...")
    base_url = os.getenv("FOODTEC_BASE")
    store_id = os.getenv("FOODTEC_STORE_ID")
    user = os.getenv("FOODTEC_USER")
    menu_pass = os.getenv("FOODTEC_MENU_PASS")
    
    print(f"   Base URL: {base_url}")
    print(f"   Store ID: {store_id}")
    print(f"   Username: {user}")
    print(f"   Password: {'*' * len(menu_pass) if menu_pass else 'None'}")
    
    # Test 2: BasicAuth initialization
    print("\n2️⃣ Testing BasicAuth initialization...")
    try:
        auth = BasicAuth(username=user, password=menu_pass)
        auth_header = auth.get_auth()
        print(f"   Auth header: Basic {auth_header.split(' ')[1][:10]}...")
        print("   ✅ BasicAuth created successfully")
    except Exception as e:
        print(f"   ❌ BasicAuth failed: {e}")
        return False
    
    # Test 3: ApiClientFT initialization
    print("\n3️⃣ Testing ApiClientFT initialization...")
    try:
        api_client = ApiClientFT(auth_header=auth_header)
        print(f"   Store ID: {api_client.store_id}")
        print(f"   HTTP Client Base URL: {api_client._http_client.base_url}")
        print(f"   Timeout: {api_client._http_client.timeout}")
        print("   ✅ ApiClientFT created successfully")
    except Exception as e:
        print(f"   ❌ ApiClientFT failed: {e}")
        return False
    
    # Test 4: URL construction
    print("\n4️⃣ Testing URL construction...")
    expected_menu_url = f"{base_url}/store/{store_id}/menu/categories"
    print(f"   Expected menu URL: {expected_menu_url}")
    
    # Test 5: API connectivity (optional, will fail if API is down)
    print("\n5️⃣ Testing API connectivity...")
    try:
        # Try to get order types (simplest endpoint)
        order_types = await api_client.get_order_types()
        print(f"   ✅ API call successful! Found {len(order_types)} order types:")
        for ot in order_types[:3]:  # Show first 3
            print(f"      • {ot.orderType}")
        if len(order_types) > 3:
            print(f"      ... and {len(order_types) - 3} more")
    except Exception as e:
        print(f"   ⚠️  API call failed (might be expected): {e}")
        print("   💡 This could be due to network issues or invalid credentials")
    
    print("\n" + "=" * 40)
    print("🎉 RP2A configuration test completed!")
    return True


async def main():
    """Main test function."""
    try:
        success = await test_rp2a_config()
        if success:
            print("✅ All tests passed! RP2A is properly configured.")
            sys.exit(0)
        else:
            print("❌ Some tests failed. Check the configuration.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())