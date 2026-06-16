# backend/tests/test_healing.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from app.services.graph_executor import GraphExecutor
from app.models.task import Task
from app.schemas.graph import FailurePolicy, HealingConfig


# ── T1: Graph Patching Logic ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_inject_healing_nodes_patches_graph():
    """Verify that a debugger node and loopback edges are added correctly."""
    executor = GraphExecutor()
    
    # Simple graph: Coder (node-coder) -> Tester (node-tester)
    graph = {
        "nodes": [
            {"id": "node-coder", "type": "agentNode", "data": {"agentType": "coder", "label": "Coder"}, "position": {"x": 100, "y": 100}},
            {"id": "node-tester", "type": "agentNode", "data": {"agentType": "tester", "label": "Tester"}, "position": {"x": 300, "y": 100}},
        ],
        "edges": [
            {"id": "edge-1", "source": "node-coder", "target": "node-tester", "data": {}}
        ]
    }

    patched = await executor._inject_healing_nodes(
        graph=graph,
        failed_node_id="node-tester",
        error_context={"error": "assertion error"},
        task_id="task-123",
        cycle_number=1
    )

    # Verify debugger node added
    nodes = patched["nodes"]
    assert len(nodes) == 3
    debugger = next((n for n in nodes if n["data"].get("agentType") == "debugger"), None)
    assert debugger is not None
    assert debugger["data"]["spawned_by_healing"] is True
    assert debugger["data"]["cycle"] == 1
    assert debugger["position"]["y"] == 250  # failed position y (100) + 150

    # Verify edges added (2 new edges)
    edges = patched["edges"]
    assert len(edges) == 3
    
    # 1. Tester -> Debugger
    t_to_d = next((e for e in edges if e["source"] == "node-tester" and e["target"] == debugger["id"]), None)
    assert t_to_d is not None
    assert t_to_d["data"]["healing"] is True

    # 2. Debugger -> Coder
    d_to_c = next((e for e in edges if e["source"] == debugger["id"] and e["target"] == "node-coder"), None)
    assert d_to_c is not None
    assert d_to_c["data"]["healing"] is True


# ── T2: Max Cycles Enforcement ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_graph_max_cycles_enforcement():
    """Verify that healing halts after exceeding max cycles."""
    executor = GraphExecutor()
    
    # Initial graph
    graph = {
        "nodes": [
            {"id": "node-coder", "type": "agentNode", "data": {"agentType": "coder", "label": "Coder"}, "position": {"x": 100, "y": 100}},
            {"id": "node-tester", "type": "agentNode", "data": {"agentType": "tester", "label": "Tester"}, "position": {"x": 300, "y": 100}},
        ],
        "edges": [
            {"id": "edge-1", "source": "node-coder", "target": "node-tester", "data": {}}
        ]
    }
    workflow_id = str(uuid4())
    executor.active_graphs[workflow_id] = graph

    # Mock DB Session
    db = MagicMock()
    
    # Mock tasks
    task_coder = Task(id=uuid4(), workflow_id=UUID(workflow_id), name="Coder", agent_name="coder", status="pending", node_id="node-coder")
    task_tester = Task(id=uuid4(), workflow_id=UUID(workflow_id), name="Tester", agent_name="tester", status="pending", node_id="node-tester")
    db.query.return_value.filter.return_value.all.return_value = [task_coder, task_tester]
    db.query.return_value.filter_by.side_effect = lambda id: MagicMock(first=lambda: next((t for t in [task_coder, task_tester] if str(t.id) == str(id)), None))

    # Mock Agents: coder passes, tester fails, debugger/others pass
    async def mock_agent_run(context):
        tid = context.get("task_id")
        if tid == str(task_coder.id):
            return {"status": "passed", "success": True}
        elif tid == str(task_tester.id):
            return {"status": "failed", "success": False}
        else:
            return {"status": "passed", "success": True}

    mock_run = AsyncMock(side_effect=mock_agent_run)

    # We need db.query().filter_by().first() to return the current task being run
    # Let's mock filter_by to return task_coder or task_tester based on ID passed
    def filter_by_side_effect(id):
        # return a mock with first returning the matching task
        tid = str(id)
        if tid == str(task_coder.id):
            return MagicMock(first=lambda: task_coder)
        elif tid == str(task_tester.id):
            return MagicMock(first=lambda: task_tester)
        else:
            # debugger task
            dbg_task = Task(id=UUID(tid), workflow_id=UUID(workflow_id), name="Debugger", agent_name="debugger", status="pending")
            return MagicMock(first=lambda: dbg_task)

    db.query.return_value.filter_by.side_effect = filter_by_side_effect

    with patch("app.services.graph_executor.get_agent_for_type") as mock_get_agent:
        mock_get_agent.side_effect = lambda name: lambda db, wf_id, t_id: MagicMock(run=mock_run)

        # Run graph
        await executor.run_graph(workflow_id, db)

    # Cycle counter should prevent infinite loops
    assert len(executor.healing_logs.get(str(task_tester.id), [])) == 3
    assert executor.healing_logs[str(task_tester.id)][-1]["resolved"] is False
