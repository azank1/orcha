#!/usr/bin/env python3
"""
Test MCP protocol level communication - simulate real MCP client
"""
import sys
import asyncio
import json
import subprocess
import time
sys.path.insert(0, 'mcp')

async def test_mcp_protocol():
    """Test MCP protocol communication like a real client would"""
    
    print("🔌 Testing MCP Protocol Level Communication...")
    
    # Start MCP server as subprocess
    server_process = subprocess.Popen(
        [sys.executable, "mcp/main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Give server time to start
        await asyncio.sleep(0.5)
        
        # Step 1: Initialize MCP session
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        print("📤 Sending MCP initialize...")
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # Read response with timeout
        response_line = server_process.stdout.readline()
        if response_line:
            init_response = json.loads(response_line.strip())
            print(f"📥 Initialize response: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("❌ No initialize response")
            return False
        
        # Step 2: List available tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,  
            "method": "tools/list"
        }
        
        print("📤 Requesting tools list...")
        server_process.stdin.write(json.dumps(list_request) + "\n")
        server_process.stdin.flush()
        
        response_line = server_process.stdout.readline()
        if response_line:
            tools_response = json.loads(response_line.strip())
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"📋 Found {len(tools)} tools:")
            for tool in tools:
                print(f"   • {tool['name']}")
        else:
            print("❌ No tools response")
            return False
        
        # Step 3: Call a tool (orders.get_menu)
        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "orders.get_menu",
                "arguments": {"vendor": "foodtec", "orderType": "Pickup"}
            }
        }
        
        print("📤 Calling orders.get_menu...")
        server_process.stdin.write(json.dumps(tool_request) + "\n")
        server_process.stdin.flush()
        
        response_line = server_process.stdout.readline()
        if response_line:
            tool_response = json.loads(response_line.strip())
            result = tool_response.get('result', {})
            print(f"📊 Tool response: {len(str(result))} characters")
            
            # Parse the actual content
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '{}')
                menu_data = json.loads(text_content)
                categories = menu_data.get('categories', [])
                print(f"✅ Menu loaded: {len(categories)} categories")
                return True
        else:
            print("❌ No tool response")
            return False
            
    except Exception as e:
        print(f"❌ MCP Protocol test failed: {e}")
        return False
    finally:
        server_process.terminate()
        server_process.wait()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_protocol())
    if success:
        print("\n🎉 MCP Protocol Test PASSED!")
        print("✅ Server handles initialize/list/call correctly")
        print("✅ Tools return proper JSON content")
        print("✅ FastMCP implementation is working!")
    else:
        print("\n❌ MCP Protocol Test FAILED!")
        sys.exit(1)