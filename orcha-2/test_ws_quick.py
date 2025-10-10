#!/usr/bin/env python3
"""Quick WebSocket test to verify LLM orchestration"""
import asyncio
import json
import websockets


async def test_ws_orchestration():
    uri = "ws://127.0.0.1:8000/automation/ws"
    
    test_cases = [
        {"text": "find pizza", "expected_event": "search_results"},
        {"text": "I want to order food", "expected_event": "info"},
        {"text": "hello", "expected_event": "info"}
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            for i, case in enumerate(test_cases, 1):
                print(f"\n🧪 Test {i}: '{case['text']}'")
                
                # Send message
                await websocket.send(json.dumps(case))
                
                # Get response
                response = await websocket.recv()
                data = json.loads(response)
                
                event = data.get("event", "unknown")
                llm_source = data.get("llm_source", "unknown")
                
                print(f"   Event: {event}")
                print(f"   LLM Source: {llm_source}")
                
                if event == case["expected_event"]:
                    print(f"   ✅ Expected event received")
                else:
                    print(f"   ⚠️  Expected {case['expected_event']}, got {event}")
                
                if event == "search_results":
                    results = data.get("data", {}).get("results", [])
                    print(f"   📊 Found {len(results)} search results")
                    if results:
                        print(f"      First result: {results[0].get('name', 'N/A')}")
            
            print("\n🎉 WebSocket orchestration test complete")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_ws_orchestration())