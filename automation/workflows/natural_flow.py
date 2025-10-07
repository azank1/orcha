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
    
    def process(self, user_input: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Process natural language input and orchestrate actions
        Uses multi-turn agent loop to complete complex tasks
        
        Args:
            user_input: User's natural language request
            max_iterations: Maximum number of LLM turns (prevents infinite loops)
            
        Returns:
            Dict with response and any actions taken
        """
        print(f"\n👤 User: {user_input}")
        
        results = {
            "user_input": user_input,
            "llm_response": "",
            "actions": [],
            "success": True
        }
        
        # Agent loop - continue until LLM says it's done or max iterations reached
        current_prompt = user_input
        for iteration in range(max_iterations):
            print(f"\n🔄 Agent iteration {iteration + 1}/{max_iterations}")
            
            # Build context with current state
            context = {}
            
            # Include menu data if available (summarized to avoid token overflow)
            if self.menu_cache:
                # Send a summary of available items WITH PRICES
                menu_summary = []
                for cat in self.menu_cache[:10]:  # Limit to first 10 categories
                    items = cat.get("items", [])[:3]  # First 3 items per category
                    menu_summary.append({
                        "category": cat.get("category"),
                        "items": [
                            {
                                "name": item.get("name"), 
                                "sizes": item.get("sizes", []),
                                "price": item.get("price")  # Include price!
                            } 
                            for item in items
                        ]
                    })
                context["menu"] = menu_summary
                context["menu_note"] = f"Showing {len(menu_summary)} of {len(self.menu_cache)} categories. Menu already fetched - use this data with prices."
            
            if self.last_validation:
                context["last_validation"] = {
                    "category": self.last_validation.get("category"),
                    "item": self.last_validation.get("item"),
                    "size": self.last_validation.get("size"),
                    "menuPrice": self.last_validation.get("base_price"),
                    "canonicalPrice": self.last_validation.get("canonical_price"),
                    "note": "IMPORTANT: For accept_order, you MUST include ALL these fields: category, item, size, menuPrice, canonicalPrice, customer (with name and phone), and externalRef. Do NOT omit any fields!"
                }
            
            # Add previous actions to context so LLM knows what it already did
            if results["actions"]:
                context["completed_actions"] = [
                    {"tool": a.get("tool"), "success": a.get("success"), "summary": a.get("summary", "")} 
                    for a in results["actions"]
                ]
                context["note"] = "These actions are already completed. Do NOT repeat them. Move to the next step."
            
            # Get LLM decision
            print("🧠 Asking LLM to interpret...")
            llm_response = self.llm.chat(
                prompt=current_prompt,
                context=context,
                tools=self.tools
            )
            
            print(f"💭 LLM Response: {llm_response['content'][:100]}...")
            
            # Store the final response
            results["llm_response"] = llm_response["content"]
            
            # If no tool calls, LLM is done
            if not llm_response.get("tool_calls"):
                print("✅ LLM has no more tools to call - task complete!")
                break
            
            # Check if this is a browse query that already has menu data
            is_browse = any(kw in user_input.lower() for kw in ['what', 'how much', 'show', 'list', 'price', 'browse', 'see'])
            has_menu = self.menu_cache is not None
            wants_export = any(tc["name"] in ["foodtec.export_menu", "export_menu"] for tc in llm_response.get("tool_calls", []))
            wants_accept = any(tc["name"] in ["foodtec.accept_order", "accept_order"] for tc in llm_response.get("tool_calls", []))
            
            # Check if order was already accepted in previous actions
            order_already_accepted = any(
                action.get("tool") == "foodtec.accept_order" and action.get("success")
                for action in results["actions"]
            )
            
            # If it's a browse query with menu already fetched, and LLM wants to call export_menu again, force answer instead
            if is_browse and has_menu and wants_export and iteration > 0:
                print("⚠️ LLM trying to call export_menu again for browse query - forcing answer instead")
                results["llm_response"] = "I have the menu data. Let me answer your question based on what we have."
                break
            
            # If order was already accepted, don't accept again - just respond with confirmation
            if order_already_accepted and wants_accept:
                print("⚠️ Order already accepted - preventing duplicate acceptance")
                results["llm_response"] = "Your order has been successfully placed!"
                break
            
            # Execute tool calls
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
            
            # Update prompt for next iteration
            # Check if this was a browse/query request vs an order request
            if any(keyword in user_input.lower() for keyword in ['what', 'how much', 'show', 'list', 'price', 'browse', 'see']):
                # This is a query - instruct LLM to answer using the data
                current_prompt = f"Now that you have the data, answer the user's question: {user_input}"
            else:
                # This is an order - continue the workflow
                current_prompt = f"Previous action completed. Continue with: {user_input}"
        
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
            # Fix tool name if missing namespace prefix
            if not tool_name.startswith("foodtec."):
                # Ollama native tool calling might strip the namespace
                if tool_name in ["export_menu", "validate_order", "accept_order"]:
                    tool_name = f"foodtec.{tool_name}"
                    print(f"   ⚠️ Fixed tool name to: {tool_name}")
            
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
            
            # Get menu price (support both 'price' and 'menuPrice' parameter names)
            menu_price = arguments.get("price") or arguments.get("menuPrice") or 0
            
            # Cache validation for next step
            self.last_validation = {
                "category": arguments.get("category"),
                "item": arguments.get("item"),
                "size": arguments.get("size"),
                "base_price": menu_price,
                "canonical_price": canonical_price,
                "customer": arguments.get("customer")
            }
            
            return {
                "tool": "foodtec.validate_order",
                "success": True,
                "canonical_price": canonical_price,
                "base_price": menu_price,
                "tax": (canonical_price - menu_price) if (canonical_price and menu_price) else 0,
                "validation_data": self.last_validation,
                "summary": f"Validated: {arguments.get('item')} ({arguments.get('size')}) - Menu: ${menu_price}, Total: ${canonical_price}"
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
