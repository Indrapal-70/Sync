import pytest
import time
from app.services.context_buffer import AgentContextBuffer, ContextEntry


@pytest.mark.asyncio
async def test_sweep_stale_evicts_inactive_only():
    buffer = AgentContextBuffer()
    
    # 1. Create entry for task-a
    entry_a = ContextEntry(
        agent_name="CoderAgent",
        step=0,
        input_summary="Input A",
        output_summary="Output A",
        status="passed"
    )
    await buffer.add_entry("task-a", entry_a)
    
    # 2. Create entry for task-b
    entry_b = ContextEntry(
        agent_name="TesterAgent",
        step=0,
        input_summary="Input B",
        output_summary="Output B",
        status="passed"
    )
    await buffer.add_entry("task-b", entry_b)
    
    # 3. Manually retroactively set last_accessed times:
    # task-a was accessed 100 seconds ago (stale)
    # task-b was accessed 5 seconds ago (fresh)
    now = time.time()
    buffer._last_accessed["task-a"] = now - 100
    buffer._last_accessed["task-b"] = now - 5
    
    # 4. Sweep with max_age_seconds = 30
    evicted_count = await buffer.sweep_stale(max_age_seconds=30)
    assert evicted_count == 1
    
    # 5. Verify task-a is gone, task-b remains
    assert "task-a" not in buffer._store
    assert "task-a" not in buffer._last_accessed
    assert "task-b" in buffer._store
    assert "task-b" in buffer._last_accessed
