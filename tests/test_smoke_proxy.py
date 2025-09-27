#!/usr/bin/env python3
"""
Root-level Proxy smoke test - JSON-RPC integration test.
Tests the complete proxy loop: Client → JSON-RPC → Proxy → P2A → FoodTec.
"""
import sys
import json
import httpx
from pathlib import Path

def load_fixtures():
    """Load test fixtures from canonical location."""
    fixture_path = Path(__file__).parent / "fixtures" / "payload_fixture.json"
    with open(fixture_path) as f:
        return json.load(f)

def test_proxy_rpc():
    """Test proxy JSON-RPC endpoints."""
    print("Proxy JSON-RPC Test")
    print("=" * 40)
    
    fixtures = load_fixtures()
    proxy_url = "http://127.0.0.1:8080/rpc"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            
            # Test 1: Menu Export
            print("[1] Testing Menu Export...")
            menu_payload = fixtures["json_rpc_tests"]["menu_export"]
            response = client.post(proxy_url, json=menu_payload)
            
            if response.status_code != 200:
                print(f"FAIL: Menu export failed: HTTP {response.status_code}")
                return False
                
            menu_result = response.json()
            if "error" in menu_result:
                print(f"FAIL: Menu export error: {menu_result['error']}")
                return False
                
            categories = len(menu_result["result"]["data"]) if menu_result["result"]["data"] else 0
            print(f"   PASS: Menu export successful: {categories} categories")
            
            # Test 2: Order Validation
            print("\n[2] Testing Order Validation...")
            validate_payload = fixtures["json_rpc_tests"]["validate_order"]
            response = client.post(proxy_url, json=validate_payload)
            
            if response.status_code != 200:
                print(f"FAIL: Validation failed: HTTP {response.status_code}")
                return False
                
            validate_result = response.json()
            if "error" in validate_result:
                print(f"FAIL: Validation error: {validate_result['error']}")
                return False
                
            canonical_price = validate_result["result"]["canonical_price"]
            print(f"   PASS: Validation successful: canonical price ${canonical_price}")
            
            # Test 3: Order Acceptance
            print("\n[3] Testing Order Acceptance...")
            accept_payload = fixtures["json_rpc_tests"]["accept_order"]
            response = client.post(proxy_url, json=accept_payload)
            
            if response.status_code != 200:
                print(f"FAIL: Acceptance failed: HTTP {response.status_code}")
                return False
                
            accept_result = response.json()
            if "error" in accept_result:
                print(f"FAIL: Acceptance error: {accept_result['error']}")
                return False
                
            order_id = accept_result["result"]["data"].get("orderNum", "Unknown") if accept_result["result"]["data"] else "Unknown"
            print(f"   PASS: Acceptance successful: Order ID {order_id}")
            
            print("\nProxy JSON-RPC test passed!")
            return True
            
    except Exception as e:
        print(f"FAIL: Proxy test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_proxy_rpc()
    sys.exit(0 if success else 1)