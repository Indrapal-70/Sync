from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
import json
from datetime import datetime

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
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

            # Respond to ping keepalive
            if msg.get("event") == "ping":
                await manager.send_to_client(client_id, {
                    "event": "pong",
                    "payload": {},
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
