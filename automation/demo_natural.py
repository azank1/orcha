"""
Demo script for natural language ordering
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from workflows.natural_flow import NaturalFlow


def demo_queries():
    """
    Run a series of demo queries to show capabilities
    """
    print("🤖 OrchaPOS Natural Language Demo")
    print("=" * 60)
    
    # Initialize
    print("\n🔧 Initializing...")
    try:
        flow = NaturalFlow(llm_provider="openai")
        print("✅ Connected to MCP and LLM")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\nMake sure:")
        print("  1. MCP server is running (port 9090)")
        print("  2. Proxy server is running (port 8080)")
        print("  3. OPENAI_API_KEY is set in .env")
        return 1
    
    # Demo queries
    queries = [
        "Show me the appetizers",
        "What pizzas do you have?",
        "I want to order chicken strips for pickup. Customer is Jane Smith, phone 410-555-9876"
    ]
    
    for i, query in enumerate(queries, 1):
        print("\n" + "=" * 60)
        print(f"Demo {i}/{len(queries)}")
        print("=" * 60)
        
        try:
            results = flow.process(query)
            
            print(f"\n🤖 Response: {results['llm_response']}")
            
            if results["actions"]:
                print(f"\n📋 Actions: {len(results['actions'])}")
                for j, action in enumerate(results["actions"], 1):
                    print(f"\n  {j}. {action['tool']}")
                    if action.get("success"):
                        print(f"     ✅ Success")
                        
                        # Show relevant details
                        if "summary" in action:
                            summary = action["summary"]
                            if "categories" in summary:
                                print(f"     📦 Found {len(summary['categories'])} categories")
                                for cat in summary["categories"][:2]:
                                    print(f"        - {cat['name']}: {cat['item_count']} items")
                        
                        if "canonical_price" in action:
                            print(f"     💰 Canonical Price: ${action['canonical_price']:.2f}")
                            print(f"     💵 Base Price: ${action['base_price']:.2f}")
                            print(f"     🧾 Tax: ${action['tax']:.2f}")
                        
                        if "order_number" in action:
                            print(f"     🎫 Order Number: {action['order_number']}")
                            print(f"     💵 Total: ${action['total_price']:.2f}")
                    else:
                        print(f"     ❌ Failed: {action.get('error', 'Unknown')}")
            
            if not results.get("success"):
                print("\n⚠️  Some actions failed")
                
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
        
        # Pause between queries
        if i < len(queries):
            input("\n⏸️  Press Enter to continue to next demo...")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("\nTo try interactive mode, run:")
    print("  python workflows/natural_flow.py")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(demo_queries())
