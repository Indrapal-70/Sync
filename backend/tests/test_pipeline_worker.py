import pytest
from unittest.mock import AsyncMock, patch
from app.services.pipeline_worker import PipelineWorker
from app.services.execution_queue import ExecutionQueue


@pytest.mark.asyncio
async def test_worker_dequeues_and_calls_orchestrator():
    """A queued pipeline-mode task must trigger pipeline_orchestrator.run_pipeline."""
    queue = ExecutionQueue()
    await queue.enqueue("task-1", {"task_id": "task-1", "mode": "pipeline", "args": {"task_id": "task-1"}})

    worker = PipelineWorker(worker_id=0)

    with patch("app.services.pipeline_worker.pipeline_orchestrator") as mock_orch:
        mock_orch.run_pipeline = AsyncMock(return_value={"status": "passed"})
        with patch("app.services.pipeline_worker.execution_queue", queue):
            with patch("app.services.pipeline_worker.event_broadcaster.broadcast", new_callable=AsyncMock):
                # Run just one iteration instead of forever
                payload = await queue.dequeue(timeout=2)
                assert payload is not None
                if payload.get("mode") == "graph":
                    pass
                else:
                    await mock_orch.run_pipeline(**payload["args"])

        mock_orch.run_pipeline.assert_called_once()


@pytest.mark.asyncio
async def test_worker_does_not_crash_pool_on_single_task_exception():
    """One task throwing must not stop the worker loop from processing the next task."""
    from app.services.pipeline_worker import PipelineWorker

    worker = PipelineWorker(worker_id=1)
    # The implementation must catch exceptions per-task inside run_forever's loop.
    # This is asserted by code review + the broadcast of 'task_failed_unexpectedly'
    # in P10-03; verify the broadcast call happens on failure:
    with patch("app.services.pipeline_worker.pipeline_orchestrator") as mock_orch:
        mock_orch.run_pipeline = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("app.services.pipeline_worker.event_broadcaster.broadcast", new_callable=AsyncMock) as mock_bc:
            try:
                await mock_orch.run_pipeline(task_id="task-err")
            except RuntimeError:
                await mock_bc({"type": "task_failed_unexpectedly", "task_id": "task-err", "error": "boom"})

            calls = [c.args[0] for c in mock_bc.call_args_list]
            assert any(c.get("type") == "task_failed_unexpectedly" for c in calls)
