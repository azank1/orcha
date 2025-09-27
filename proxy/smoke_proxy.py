#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Local proxy development test - hits /rpc endpoint directly.Smoke test for Proxy - tests JSON-RPC forwarding to P2A

For development and debugging of proxy handlers only."""

"""import requests

import sysimport uuid

import json

import httpxdef test_proxy():

from pathlib import Path    """Test proxy forwarding to P2A"""

    print("🚦 Testing Proxy → P2A forwarding...")

def load_fixtures():    

    """Load test fixtures from root location."""    payload = {

    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "payload_fixture.json"        "jsonrpc": "2.0",

    with open(fixture_path) as f:        "id": str(uuid.uuid4()),

        return json.load(f)        "method": "foodtec.export_menu",

        "params": {

def test_proxy_local():            "orderType": "Pickup"

    """Test proxy endpoints locally for development."""        }

    print("🔧 Proxy Local Development Test")    }

    print("=" * 40)    

        try:

    fixtures = load_fixtures()        # Test /healthz endpoint

    proxy_url = "http://127.0.0.1:8080/rpc"        print("1️⃣ Testing /healthz endpoint...")

            health_response = requests.get("http://127.0.0.1:8080/healthz")

    try:        print(f"Health check: {health_response.json()}")

        with httpx.Client(timeout=30.0) as client:        

                    # Test /rpc endpoint

            # Health check        print("2️⃣ Testing /rpc forwarding...")

            try:        response = requests.post("http://127.0.0.1:8080/rpc", json=payload)

                health_response = client.get("http://127.0.0.1:8080/healthz")        result = response.json()

                if health_response.status_code == 200:        print(f"RPC response: {result}")

                    print("✅ Proxy server is running")        

                else:        # Check if we got live FoodTec data

                    print("❌ Proxy server health check failed")        if "result" in result and "categories" in str(result):

                    return False            print("✅ Success: Proxy forwarded to P2A and got live FoodTec data!")

            except:        else:

                print("❌ Cannot connect to proxy server")            print("⚠️ Warning: Unexpected response format")

                print("   Make sure to run: python main.py")            

                return False    except Exception as e:

                    print(f"❌ Error: {e}")

            # Test JSON-RPC endpoints

            for test_name, payload in fixtures["json_rpc_tests"].items():

                print(f"\n🧪 Testing {test_name}...")if __name__ == "__main__":

                    test_proxy()

                response = client.post(proxy_url, json=payload)
                
                if response.status_code != 200:
                    print(f"❌ HTTP {response.status_code}")
                    continue
                    
                result = response.json()
                
                if "error" in result:
                    print(f"❌ JSON-RPC Error: {result['error']['message']}")
                    if "debug" in result["error"].get("data", {}):
                        debug = result["error"]["data"]["debug"]
                        print(f"   Debug: {json.dumps(debug, indent=2)}")
                else:
                    print("✅ Success")
                    if "result" in result and "status" in result["result"]:
                        print(f"   Status: {result['result']['status']}")
            
            print("\n🎯 Proxy local test completed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_proxy_local()
    sys.exit(0 if success else 1)