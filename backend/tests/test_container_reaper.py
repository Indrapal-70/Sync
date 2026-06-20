import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, call
from app.services.container_reaper import container_reaper


@pytest.mark.asyncio
@patch("app.services.docker_executor.docker_executor.available", True)
@patch("asyncio.create_subprocess_exec")
async def test_container_reaper_kills_stale_only(mock_exec):
    # Mock docker ps
    mock_ps = AsyncMock()
    mock_ps.returncode = 0
    mock_ps.communicate.return_value = (b"container1\ncontainer2\n", b"")
    
    # Mock docker inspect State.StartedAt
    now_ts = time.time()
    stale_iso = datetime.fromtimestamp(now_ts - 600, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    fresh_iso = datetime.fromtimestamp(now_ts - 10, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    
    mock_inspect1 = AsyncMock()
    mock_inspect1.returncode = 0
    mock_inspect1.communicate.return_value = (stale_iso.encode(), b"")
    
    mock_inspect2 = AsyncMock()
    mock_inspect2.returncode = 0
    mock_inspect2.communicate.return_value = (fresh_iso.encode(), b"")
    
    mock_kill = AsyncMock()
    mock_kill.returncode = 0
    mock_kill.wait = AsyncMock()
    
    mock_rm = AsyncMock()
    mock_rm.returncode = 0
    mock_rm.wait = AsyncMock()
    
    mock_exec.side_effect = [
        mock_ps,         # ps
        mock_inspect1,   # inspect container1
        mock_inspect2,   # inspect container2
        mock_kill,       # kill container1
        mock_rm,         # rm container1
    ]
    
    await container_reaper.reap_containers(max_age_seconds=300)
    
    # Check that container1 was reaped and container2 was spared
    kill_called = False
    rm_called = False
    for args, kwargs in mock_exec.call_args_list:
        if args[:3] == ("docker", "kill", "container1"):
            kill_called = True
        if args[:3] == ("docker", "rm", "container1"):
            rm_called = True
        # container2 should not be killed or removed
        assert args[:3] != ("docker", "kill", "container2")
        assert args[:3] != ("docker", "rm", "container2")

    assert kill_called
    assert rm_called
