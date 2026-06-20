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
                # Yield to the event loop briefly instead of starvation
                await original_sleep(0.001)
                return
            await original_sleep(seconds)
        
        current_time = [0.0]
        
        with patch("asyncio.sleep", mock_sleep), patch("time.time", lambda: current_time[0]):
            task = asyncio.create_task(websocket_endpoint(websocket, "test_client"))
            
            # Let it run the first iteration
            await original_sleep(0.02)
            
            # Advance time to trigger timeout
            current_time[0] = 45.0
            
            # Let it run the check
            await original_sleep(0.02)
            
            assert websocket.close.called
            
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

