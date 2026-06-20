import pytest
import asyncio
import time
from app.services.sandbox_pool import SandboxPool


@pytest.mark.asyncio
async def test_pool_allows_up_to_max_concurrent():
    """N tasks acquiring a pool of size N must all succeed concurrently."""
    pool = SandboxPool(max_concurrent=3)
    acquired_order = []

    async def worker(i):
        async with pool.acquire_slot(f"task-{i}"):
            acquired_order.append(i)
            await asyncio.sleep(0.05)

    await asyncio.gather(*[worker(i) for i in range(3)])
    assert len(acquired_order) == 3


@pytest.mark.asyncio
async def test_pool_blocks_beyond_max_concurrent():
    """
    With max_concurrent=2, a 3rd task must NOT start until one of the first
    two releases its slot. Verified via a shared counter that must never
    exceed 2 at any instant.
    """
    pool = SandboxPool(max_concurrent=2)
    concurrent_count = 0
    max_observed = 0
    lock = asyncio.Lock()

    async def worker(i):
        nonlocal concurrent_count, max_observed
        async with pool.acquire_slot(f"task-{i}"):
            async with lock:
                concurrent_count += 1
                max_observed = max(max_observed, concurrent_count)
            await asyncio.sleep(0.1)
            async with lock:
                concurrent_count -= 1

    await asyncio.gather(*[worker(i) for i in range(5)])
    assert max_observed <= 2, f"Pool allowed {max_observed} concurrent slots, expected max 2"


@pytest.mark.asyncio
async def test_pool_releases_slot_after_exception():
    """If the wrapped code raises, the slot must still be released."""
    pool = SandboxPool(max_concurrent=1)

    with pytest.raises(ValueError):
        async with pool.acquire_slot("task-fail"):
            raise ValueError("boom")

    assert pool.active_count == 0, "Slot was not released after an exception"
    # A subsequent acquire must not deadlock
    async with pool.acquire_slot("task-after"):
        assert pool.active_count == 1


@pytest.mark.asyncio
async def test_active_count_and_available_slots_are_accurate():
    pool = SandboxPool(max_concurrent=4)
    assert pool.available_slots == 4

    async with pool.acquire_slot("task-a"):
        assert pool.active_count == 1
        assert pool.available_slots == 3
