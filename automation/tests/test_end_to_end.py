"""
End-to-end test for the ordering flow
"""
import pytest
import json
import socket
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import using relative path
from workflows.ordering_flow import run_order_flow
from clients.mcp_client import MCPClient

def check_mcp_server_running():
    """Check if the MCP server is running on port 9090"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to connect to the MCP server
        s.connect(('127.0.0.1', 9090))
        s.close()
        return True
    except socket.error:
        s.close()
        return False

def test_complete_order_flow():
    """Test the complete ordering flow from menu export to order acceptance"""
    # Check if MCP server is running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', 9090))
        s.close()
    except socket.error:
        s.close()
        print("Checking if MCP server is running on port 9090...")
        print("MCP server is not running on port 9090")
        print("Make sure the MCP server is running with: cd MCP && node dist/index.js")
        pytest.skip("MCP server is not running on port 9090")
    
    # Run the complete order flow
    results = run_order_flow()
    
    # Verify menu was exported
    assert results['menu_preview']['categories'] > 0
    assert results['menu_preview']['first_item']['item'] != ""
    
    # Verify order was validated
    assert results['validation_status'] == 200
    assert results['canonical_price'] > 0
    
    # Verify order was accepted
    assert results['acceptance_status'] == 200

def test_complete_order_flow():
    """Test the complete ordering flow from menu export to order acceptance"""
    try:
        # Check if MCP server is running
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Try to connect to MCP server
            s.connect(("127.0.0.1", 9090))
            s.close()
        except ConnectionRefusedError:
            print("\n⚠️ Test skipped: MCP server is not running on port 9090")
            print("ℹ️ Make sure the MCP server is running with: cd MCP && node dist/index.js")
            pytest.skip("MCP server is not running on port 9090")
            
        # Run the complete flow
        results = run_order_flow()
        
        # Print diagnostics
        print(f"\n✅ Menu retrieved ({results['menu_preview']['categories']} categories)")
        print(f"   First item: {results['menu_preview']['first_item']['item']}")
        
        # Validate the results
        assert results["validation_status"] == 200, "Validation should succeed"
        print(f"✅ Validation OK (price={results['canonical_price']})")
        
        assert results["acceptance_status"] == 200, "Acceptance should succeed"
        print(f"✅ Acceptance OK")
        
        # Print final payloads for debugging
        print("\nDraft payload:")
        print(json.dumps(results["draft_payload"], indent=2))
        
        print("\nAcceptance payload:")
        print(json.dumps(results["acceptance_payload"], indent=2))
        
        print("\nAcceptance response:")
        print(json.dumps(results["acceptance_response"], indent=2))
        
    except Exception as e:
        pytest.fail(f"Order flow failed: {e}")

if __name__ == "__main__":
    # Allow running as standalone script too
    test_complete_order_flow()
    print("\n✅ All tests passed!")