import pytest
import asyncio


@pytest.mark.asyncio
async def test_graceful_shutdown_cancels_all_tracked_tasks():
    """
    Every tracked task must be cancelled and awaited without raising an unhandled exception.
    """
    background_tasks = set()

    async def dummy_loop():
        while True:
            await asyncio.sleep(1)

    for _ in range(3):
        t = asyncio.create_task(dummy_loop())
        background_tasks.add(t)

    assert len(background_tasks) == 3

    for t in background_tasks:
        t.cancel()
    results = await asyncio.gather(*background_tasks, return_exceptions=True)

    assert all(isinstance(r, asyncio.CancelledError) for r in results)
    assert all(t.cancelled() for t in background_tasks)


@pytest.mark.asyncio
async def test_no_pending_tasks_after_full_shutdown_sequence():
    """After cancel+gather, no task in the tracked set should remain pending."""
    background_tasks = set()

    async def dummy_loop():
        while True:
            await asyncio.sleep(1)

    for _ in range(2):
        t = asyncio.create_task(dummy_loop())
        background_tasks.add(t)

    for t in background_tasks:
        t.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

    pending = [t for t in background_tasks if not t.done()]
    assert pending == [], f"{len(pending)} task(s) still pending after shutdown"
