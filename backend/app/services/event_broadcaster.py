import asyncio
import json
import redis
from app.core.config import settings
from app.websocket.manager import manager

async def start_broadcaster():
    """
    Background task: Redis pub/sub → WebSocket broadcast bridge.
    Runs forever. Start this with asyncio.create_task() on startup.
    """
    r = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe("sync_events")
    print("[Broadcaster] Subscribed to Redis channel: sync_events")

    while True:
        try:
            message = await asyncio.to_thread(pubsub.get_message,
                                              ignore_subscribe_messages=True,
                                              timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast(data)
                print(f"[Broadcaster] Broadcast event: {data.get('event')}")
        except Exception as e:
            print(f"[Broadcaster] Error: {e}")
            await asyncio.sleep(1)
        await asyncio.sleep(0.01)
