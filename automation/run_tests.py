"""
Helper script to run the end-to-end test with better error messages
"""
import subprocess
import socket
import sys
import time
import os

def check_mcp_server():
    """Check if MCP server is running on port 9090"""
    print("Checking if MCP server is running on port 9090...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 9090))
        s.close()
        print("✅ MCP server is running on port 9090")
        return True
    except ConnectionRefusedError:
        print("❌ MCP server is not running on port 9090")
        return False
        
def check_proxy_server():
    """Check if Proxy server is running on port 8080"""
    print("Checking if Proxy server is running on port 8080...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 8080))
        s.close()
        print("✅ Proxy server is running on port 8080")
        return True
    except ConnectionRefusedError:
        print("❌ Proxy server is not running on port 8080")
        return False

def run_test():
    """Run the end-to-end test"""
    print("🔍 Testing server availability...\n")
    
    mcp_running = check_mcp_server()
    proxy_running = check_proxy_server()
    
    if not mcp_running or not proxy_running:
        print("\n⚠️ Tests cannot proceed without all required servers running.")
        
        print("\nTo start MCP server (port 9090):")
        print("cd MCP && node dist/index.js")
        
        print("\nTo start Proxy server (port 8080):")
        print("cd proxy && python main.py")
        
        if mcp_running:
            print("\nThe MCP server on port 9090 is already running.")
        
        if proxy_running:
            print("\nThe proxy server on port 8080 is already running.")
            
        return 1
        
    print("\nRunning end-to-end test...\n")
    result = subprocess.run(
        ["pytest", "tests/test_end_to_end.py", "-v"], 
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_test())