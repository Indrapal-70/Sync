import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws/verify-test-001"
    try:
        async with websockets.connect(uri) as websocket:
            print("[VERIFY] WS Connected")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"[VERIFY] Event received: {data.get('event')}")
                    if data.get('event') == 'task_updated':
                        return
                except asyncio.TimeoutError:
                    print("Timeout waiting for message")
                    break
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_ws())
