"""
Natural language workflow powered by LLM
Interprets user intent and orchestrates tool calls
"""
import sys
import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from clients.mcp_client import MCPClient
from clients.llm_provider import LLMProvider, get_foodtec_tools


class NaturalFlow:
    """
    LLM-driven workflow that interprets natural language
    and orchestrates FoodTec operations
    """
    
    def __init__(self, mcp_url: str = "http://127.0.0.1:9090/rpc",
                 llm_provider: str = "openai"):
        """
        Initialize the natural flow
        
        Args:
            mcp_url: URL of the MCP server
            llm_provider: LLM provider ("openai" or "anthropic")
        """
        self.mcp_client = MCPClient(url=mcp_url)
        self.llm = LLMProvider(provider=llm_provider)
        self.tools = get_foodtec_tools()
        self.conversation_history = []
        self.menu_cache = None
        self.last_validation = None
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language input and orchestrate actions
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Dict with response and any actions taken
        """
        print(f"\n🤔 User: {user_input}")
        
        # Build context
        context = {}
        if self.menu_cache:
            context["menu_available"] = True
            context["menu_categories"] = len(self.menu_cache)
        if self.last_validation:
            context["last_validation"] = self.last_validation
        
        # Get LLM decision
        print("🧠 Asking LLM to interpret...")
        llm_response = self.llm.chat(
            prompt=user_input,
            context=context,
            tools=self.tools
        )
        
        print(f"💭 LLM Response: {llm_response['content'][:100]}...")
        
        # Execute tool calls if any
        results = {
            "user_input": user_input,
            "llm_response": llm_response["content"],
            "actions": [],
            "success": True
        }
        
        if llm_response["tool_calls"]:
            print(f"🔧 LLM wants to call {len(llm_response['tool_calls'])} tool(s)")
            
            for tool_call in llm_response["tool_calls"]:
                action_result = self._execute_tool(
                    tool_call["name"],
                    tool_call["arguments"]
                )
                results["actions"].append(action_result)
                
                # Update success flag
                if not action_result.get("success"):
                    results["success"] = False
        
        return results
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call via MCP
        
        Args:
            tool_name: Name of the tool (e.g., "foodtec.export_menu")
            arguments: Tool arguments
            
        Returns:
            Dict with tool execution results
        """
        print(f"\n🔧 Executing: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            # Call the MCP server
            response = self.mcp_client.call(tool_name, arguments)
            
            # Process based on tool type
            if tool_name == "foodtec.export_menu":
                return self._handle_menu_export(response, arguments)
            
            elif tool_name == "foodtec.validate_order":
                return self._handle_validation(response, arguments)
            
            elif tool_name == "foodtec.accept_order":
                return self._handle_acceptance(response, arguments)
            
            else:
                return {
                    "tool": tool_name,
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            print(f"❌ Tool execution failed: {e}")
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e),
                "arguments": arguments
            }
    
    def _handle_menu_export(self, response: Dict, arguments: Dict) -> Dict[str, Any]:
        """Handle menu export response"""
        result = response.get("result", {})
        
        if result.get("success"):
            menu_data = result.get("data", [])
            self.menu_cache = menu_data
            
            # Filter by category if requested
            category_filter = arguments.get("category")
            if category_filter:
                menu_data = [
                    cat for cat in menu_data 
                    if cat.get("category", "").lower() == category_filter.lower()
                ]
            
            print(f"✅ Menu exported: {len(menu_data)} categories")
            
            # Build summary
            summary = {
                "categories": []
            }
            
            for category in menu_data[:5]:  # Show first 5 categories
                cat_name = category.get("category", "Unknown")
                items = category.get("items", [])
                summary["categories"].append({
                    "name": cat_name,
                    "item_count": len(items),
                    "sample_items": [
                        {
                            "name": item.get("item"),
                            "sizes": [
                                {
                                    "size": sp.get("size"),
                                    "price": sp.get("price")
                                }
                                for sp in item.get("sizePrices", [])[:2]
                            ]
                        }
                        for item in items[:3]
                    ]
                })
            
            return {
                "tool": "foodtec.export_menu",
                "success": True,
                "summary": summary,
                "full_data": menu_data
            }
        else:
            print(f"❌ Menu export failed")
            return {
                "tool": "foodtec.export_menu",
                "success": False,
                "error": result.get("raw", "Unknown error")
            }
    
    def _handle_validation(self, response: Dict, arguments: Dict) -> Dict[str, Any]:
        """Handle order validation response"""
        result = response.get("result", {})
        
        if result.get("status") == 200:
            # Extract canonical price
            canonical_price = None
            data = result.get("data", {})
            
            if "price" in data:
                canonical_price = data["price"]
            
            print(f"✅ Validation successful: ${canonical_price}")
            
            # Cache validation for next step
            self.last_validation = {
                "category": arguments.get("category"),
                "item": arguments.get("item"),
                "size": arguments.get("size"),
                "base_price": arguments.get("price"),
                "canonical_price": canonical_price,
                "customer": arguments.get("customer")
            }
            
            return {
                "tool": "foodtec.validate_order",
                "success": True,
                "canonical_price": canonical_price,
                "base_price": arguments.get("price"),
                "tax": canonical_price - arguments.get("price") if canonical_price else 0,
                "validation_data": self.last_validation
            }
        else:
            print(f"❌ Validation failed")
            return {
                "tool": "foodtec.validate_order",
                "success": False,
                "error": result.get("raw", "Validation failed")
            }
    
    def _handle_acceptance(self, response: Dict, arguments: Dict) -> Dict[str, Any]:
        """Handle order acceptance response"""
        result = response.get("result", {})
        
        if result.get("status") == 200:
            data = result.get("data", {})
            order_num = data.get("orderNum", "Unknown")
            promise_time = data.get("promiseTime")
            
            print(f"✅ Order accepted: #{order_num}")
            
            return {
                "tool": "foodtec.accept_order",
                "success": True,
                "order_number": order_num,
                "promise_time": promise_time,
                "total_price": arguments.get("price"),
                "order_details": {
                    "item": arguments.get("item"),
                    "size": arguments.get("size"),
                    "customer": arguments.get("customer")
                }
            }
        else:
            print(f"❌ Order acceptance failed")
            return {
                "tool": "foodtec.accept_order",
                "success": False,
                "error": result.get("raw", "Acceptance failed")
            }
    
    def reset(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.menu_cache = None
        self.last_validation = None
        print("🔄 Conversation reset")


def main():
    """
    Main function for testing the natural flow
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Natural language FoodTec ordering")
    parser.add_argument("--provider", default="ollama", 
                       choices=["openai", "anthropic", "huggingface", "ollama"],
                       help="LLM provider to use")
    parser.add_argument("--query", type=str, help="Single query to process")
    args = parser.parse_args()
    
    print("🤖 OrchaPOS Natural Language Interface")
    print("=" * 50)
    
    # Initialize
    try:
        flow = NaturalFlow(llm_provider=args.provider)
        print(f"✅ Initialized with {args.provider.upper()}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Single query mode
    if args.query:
        results = flow.process(args.query)
        print("\n" + "=" * 50)
        print("📊 Results:")
        print(json.dumps(results, indent=2))
        return 0
    
    # Interactive mode
    print("\n💬 Interactive Mode (type 'quit' to exit, 'reset' to clear state)")
    print("Examples:")
    print("  - Show me the appetizers")
    print("  - I want chicken strips for pickup")
    print("  - Order a large pizza")
    print()
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == "reset":
                flow.reset()
                continue
            
            # Process the input
            results = flow.process(user_input)
            
            # Display results
            print("\n" + "=" * 50)
            print(f"🤖 OrchaPOS: {results['llm_response']}")
            
            if results["actions"]:
                print(f"\n📋 Actions taken: {len(results['actions'])}")
                for i, action in enumerate(results["actions"], 1):
                    print(f"\n  {i}. {action['tool']}")
                    if action.get("success"):
                        print(f"     ✅ Success")
                        if "canonical_price" in action:
                            print(f"     💰 Price: ${action['canonical_price']}")
                        if "order_number" in action:
                            print(f"     🎫 Order: #{action['order_number']}")
                    else:
                        print(f"     ❌ Failed: {action.get('error', 'Unknown')}")
            
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    sys.exit(main())
