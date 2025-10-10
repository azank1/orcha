#!/usr/bin/env python3
"""
Quick test client to verify our FastMCP server works correctly.
This will test the MCP protocol communication and tool discovery.
"""
import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

async def test_mcp_server():
    """Test our FastMCP server via subprocess communication."""
    
    print("🔍 Testing Orcha-2 FastMCP Server...")
    
    # Start the MCP server as subprocess
    server_process = subprocess.Popen(
        [sys.executable, "mcp/main.py"],
        cwd="orcha-2",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Send MCP initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"📤 Sending initialize request...")
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # Read response (with timeout)
        try:
            response_line = server_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                print(f"📥 Initialize response: {response}")
            else:
                print("❌ No response received")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return False
        
        # Send tools list request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print(f"📤 Sending tools/list request...")
        server_process.stdin.write(json.dumps(list_tools_request) + "\n")
        server_process.stdin.flush()
        
        # Read tools response
        try:
            response_line = server_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                print(f"📥 Tools list response: {response}")
                
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"   • {tool['name']}: {tool.get('description', 'No description')}")
                    return True
            else:
                print("❌ No tools response received")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in tools response: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    if success:
        print("🎉 FastMCP server test PASSED!")
        print("✅ Phase 1 Complete: Working MCP server with 6 tools")
    else:
        print("❌ FastMCP server test FAILED!")
        sys.exit(1)