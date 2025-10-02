"""
Main orchestration module for FoodTec automation
"""
import sys
import os
import socket

# Ensure the current directory is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    
def check_mcp_server():
    """Check if MCP server is running on port 9090"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 9090))
        s.close()
        return True
    except:
        s.close()
        return False

# Now we can import
from workflows.ordering_flow import run_order_flow

def main():
    """
    Run the complete ordering flow and print results
    """
    # Check if MCP server is running
    if not check_mcp_server():
        print("❌ MCP server is not running on port 9090")
        print("Please start the MCP server with: cd MCP && node dist/index.js")
        return 1
        
    try:
        print("Starting order flow automation...")
        results = run_order_flow()
        
        # Print results step by step
        menu_preview = results["menu_preview"]
        print(f"✅ Menu retrieved ({menu_preview['categories']} categories)")
        
        if results["validation_status"] == 200:
            print(f"✅ Order validated (canonical price = {results['canonical_price']})")
        else:
            print(f"❌ Order validation failed")
            return 1
        
        if results["acceptance_status"] == 200:
            print(f"✅ Order accepted (status {results['acceptance_status']})")
        else:
            print(f"❌ Order acceptance failed")
            return 1
        
        return 0
    except Exception as e:
        print(f"❌ Error in order flow: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())