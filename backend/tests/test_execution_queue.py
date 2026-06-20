import pytest
import pytest_asyncio
from app.services.execution_queue import ExecutionQueue


@pytest_asyncio.fixture
async def clean_queue():
    """Ensure the Redis-backed queue is empty before and after each test."""
    queue = ExecutionQueue()
    # Drain anything left over from a previous run
    while await queue.dequeue(timeout=1) is not None:
        pass
    yield queue
    while await queue.dequeue(timeout=1) is not None:
        pass


@pytest.mark.asyncio
async def test_enqueue_returns_correct_position(clean_queue):
    pos0 = await clean_queue.enqueue("task-1", {"task_id": "task-1"})
    pos1 = await clean_queue.enqueue("task-2", {"task_id": "task-2"})
    assert pos0 == 0
    assert pos1 == 1


@pytest.mark.asyncio
async def test_dequeue_is_fifo(clean_queue):
    await clean_queue.enqueue("task-a", {"task_id": "task-a"})
    await clean_queue.enqueue("task-b", {"task_id": "task-b"})

    first = await clean_queue.dequeue(timeout=2)
    second = await clean_queue.dequeue(timeout=2)

    assert first["task_id"] == "task-a"
    assert second["task_id"] == "task-b"


@pytest.mark.asyncio
async def test_dequeue_returns_none_on_empty_timeout(clean_queue):
    result = await clean_queue.dequeue(timeout=1)
    assert result is None


@pytest.mark.asyncio
async def test_get_queue_position_for_existing_task(clean_queue):
    await clean_queue.enqueue("task-x", {"task_id": "task-x"})
    await clean_queue.enqueue("task-y", {"task_id": "task-y"})
    pos = await clean_queue.get_queue_position("task-y")
    assert pos == 1


@pytest.mark.asyncio
async def test_get_queue_position_returns_none_if_absent(clean_queue):
    pos = await clean_queue.get_queue_position("never-enqueued")
    assert pos is None


@pytest.mark.asyncio
async def test_remove_deletes_specific_task(clean_queue):
    await clean_queue.enqueue("task-keep", {"task_id": "task-keep"})
    await clean_queue.enqueue("task-remove", {"task_id": "task-remove"})

    removed = await clean_queue.remove("task-remove")
    assert removed is True

    remaining = await clean_queue.dequeue(timeout=2)
    assert remaining["task_id"] == "task-keep"


@pytest.mark.asyncio
async def test_queue_survives_new_client_instance(clean_queue):
    """
    Simulates a backend restart: a brand-new ExecutionQueue object pointed
    at the same Redis key must see previously enqueued items.
    """
    await clean_queue.enqueue("task-persisted", {"task_id": "task-persisted"})

    fresh_queue = ExecutionQueue()
    result = await fresh_queue.dequeue(timeout=2)
    assert result["task_id"] == "task-persisted"
