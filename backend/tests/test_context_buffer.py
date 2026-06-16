# backend/tests/test_context_buffer.py

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.services.context_buffer import AgentContextBuffer, ContextEntry, agent_context_buffer

@pytest.mark.asyncio
async def test_add_entry_basic():
    """Verify adding an entry to context buffer and websocket event broadcast."""
    buffer = AgentContextBuffer(max_entries_per_task=5)
    task_id = "test-task-123"
    
    entry = ContextEntry(
        agent_name="TesterAgent",
        step=0,
        input_summary="run test code",
        output_summary="assertion error",
        status="failed",
        error_details="AssertionError: 1 != 2",
        healing_cycle=1
    )

    with patch("app.services.context_buffer.publish_event") as mock_publish:
        await buffer.add_entry(task_id, entry)
        
        # Verify stored correctly
        entries = buffer._store[task_id]
        assert len(entries) == 1
        assert entries[0].agent_name == "TesterAgent"
        assert entries[0].timestamp > 0.0
        
        # Verify publish_event called
        mock_publish.assert_called_once_with(
            "context_updated",
            {
                "task_id": task_id,
                "agent": "TesterAgent",
                "step": 0
            }
        )

@pytest.mark.asyncio
async def test_trim_buffer_max_entries():
    """Verify that buffer limits entries to max_entries_per_task."""
    max_entries = 3
    buffer = AgentContextBuffer(max_entries_per_task=max_entries)
    task_id = "trim-task"

    with patch("app.services.context_buffer.publish_event"):
        for i in range(5):
            entry = ContextEntry(
                agent_name="CoderAgent",
                step=i,
                input_summary=f"input-{i}",
                output_summary=f"output-{i}",
                status="passed"
            )
            await buffer.add_entry(task_id, entry)

        entries = buffer._store[task_id]
        assert len(entries) == max_entries
        # Verify oldest removed (first 2 should be gone)
        assert entries[0].step == 2
        assert entries[1].step == 3
        assert entries[2].step == 4

@pytest.mark.asyncio
async def test_relevance_filtering():
    """Verify filtering logic per requesting agent class name."""
    buffer = AgentContextBuffer(max_entries_per_task=10)
    task_id = "relevance-task"

    entries = [
        ContextEntry("CoderAgent", 0, "in", "out", "passed"),
        ContextEntry("TesterAgent", 1, "in", "out_fail", "failed", error_details="SyntaxError"),
        ContextEntry("DebuggerAgent", 2, "in", "fix", "passed", suggested_fix="fix code"),
        ContextEntry("TesterAgent", 3, "in2", "out_fail2", "failed", error_details="ZeroDivisionError"),
        ContextEntry("ReviewerAgent", 4, "in", "approved", "passed"),
    ]

    with patch("app.services.context_buffer.publish_event"):
        for e in entries:
            await buffer.add_entry(task_id, e)

    # 1. CoderAgent relevance check: needs all tester failures + debugger suggestions
    coder_ctx = await buffer.get_context_for_agent(task_id, "CoderAgent")
    assert len(coder_ctx) == 3
    assert coder_ctx[0].error_details == "SyntaxError"
    assert coder_ctx[1].suggested_fix == "fix code"
    assert coder_ctx[2].error_details == "ZeroDivisionError"

    # 2. DebuggerAgent relevance check: needs the most recent Tester failure only
    dbg_ctx = await buffer.get_context_for_agent(task_id, "DebuggerAgent")
    assert len(dbg_ctx) == 1
    assert dbg_ctx[0].error_details == "ZeroDivisionError"

    # 3. Default behavior: returns last N (e.g. 2)
    other_ctx = await buffer.get_context_for_agent(task_id, "ReviewerAgent", last_n=2)
    assert len(other_ctx) == 2
    assert other_ctx[0].agent_name == "TesterAgent"
    assert other_ctx[0].error_details == "ZeroDivisionError"
    assert other_ctx[1].agent_name == "ReviewerAgent"

@pytest.mark.asyncio
async def test_build_context_prompt():
    """Verify context prompt formatting handles entries correctly."""
    buffer = AgentContextBuffer()
    task_id = "prompt-task"

    entries = [
        ContextEntry("TesterAgent", 0, "in", "out", "failed", error_details="NameError", healing_cycle=1),
        ContextEntry("DebuggerAgent", 1, "in", "out", "passed", suggested_fix="Add import", healing_cycle=1),
    ]

    with patch("app.services.context_buffer.publish_event"):
        for e in entries:
            await buffer.add_entry(task_id, e)

    prompt = await buffer.build_context_prompt(task_id, "CoderAgent")
    
    assert "## Previous Execution Context" in prompt
    assert "Cycle 1 — TesterAgent [FAILED]" in prompt
    assert "**What went wrong**:\nNameError" in prompt
    assert "Cycle 1 — DebuggerAgent [PASSED]" in prompt
    assert "**Suggested fix**:\nAdd import" in prompt

@pytest.mark.asyncio
async def test_clear_buffer():
    """Verify clearing the buffer for a task."""
    buffer = AgentContextBuffer()
    task_id = "clear-task"
    entry = ContextEntry("CoderAgent", 0, "in", "out", "passed")

    with patch("app.services.context_buffer.publish_event"):
        await buffer.add_entry(task_id, entry)
        assert task_id in buffer._store

        await buffer.clear(task_id)
        assert task_id not in buffer._store
