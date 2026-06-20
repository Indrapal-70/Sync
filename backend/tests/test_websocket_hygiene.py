import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.routers.websocket_router import websocket_endpoint


@pytest.mark.asyncio
async def test_websocket_heartbeat_timeout_closes_connection():
    with patch("app.websocket.manager.manager.connect", AsyncMock()), \
         patch("app.websocket.manager.manager.send_to_client", AsyncMock()), \
         patch("app.websocket.manager.manager.disconnect", AsyncMock()):
        
        websocket = AsyncMock()
        
        # Simulate receive_text hanging forever
        async def hang_forever():
            await asyncio.sleep(10)
            return "{}"
        websocket.receive_text.side_effect = hang_forever
        
        original_sleep = asyncio.sleep
        
        async def mock_sleep(seconds):
            if seconds in (30, 10):
                # Don't actually sleep 30s or 10s in unit tests
                return
            await original_sleep(seconds)
        
        with patch("asyncio.sleep", mock_sleep), patch("time.time") as mock_time:
            # First call is last_pong_received initialization (time 0)
            # Second call is inside heartbeat loop after sleep(30) + sleep(10) (time 41)
            # Third call is also inside time.time() check
            mock_time.side_effect = [0, 41, 41, 41, 41]
            
            task = asyncio.create_task(websocket_endpoint(websocket, "test_client"))
            
            # Allow task to run
            await original_sleep(0.05)
            
            assert websocket.close.called
            
            task.cancel()
            try:
                await task
            except Exception:
                pass
