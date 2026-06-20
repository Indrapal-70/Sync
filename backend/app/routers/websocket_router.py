import asyncio
import json
import logging
import time
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager

logger = logging.getLogger("sync.websocket_router")
router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    
    last_pong_received = time.time()

    async def heartbeat():
        nonlocal last_pong_received
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break
            await asyncio.sleep(10)
            if time.time() - last_pong_received > 40:
                logger.warning(f"Heartbeat timeout for client {client_id}. Closing connection.")
                try:
                    await websocket.close()
                except Exception:
                    pass
                break

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        # Send welcome handshake immediately on connect
        await manager.send_to_client(client_id, {
            "event": "connected",
            "payload": {
                "client_id": client_id,
                "message": "Connected to SYNC WebSocket",
                "active_connections": manager.connection_count
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive, handle incoming messages
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "pong" or msg.get("event") == "pong":
                last_pong_received = time.time()

            # Respond to ping keepalive
            if msg.get("event") == "ping" or msg.get("type") == "ping":
                await manager.send_to_client(client_id, {
                    "event": "pong",
                    "payload": {},
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(client_id)
