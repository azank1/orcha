import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:5000/automation/ws"
    async with websockets.connect(uri) as websocket:
        # Test search intent
        await websocket.send(json.dumps({"text": "Show me pizza options", "session_id": "test1"}))
        response = await websocket.recv()
        print("Search Response:", response)

        # Test order intent
        await websocket.send(json.dumps({"text": "I want to order", "session_id": "test1"}))
        response = await websocket.recv()
        print("Order Response:", response)

        # Test unknown intent
        await websocket.send(json.dumps({"text": "Tell me a joke", "session_id": "test1"}))
        response = await websocket.recv()
        print("Unknown Response:", response)

if __name__ == "__main__":
    asyncio.run(test_ws())
