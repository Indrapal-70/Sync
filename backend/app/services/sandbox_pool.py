import os
import time
import asyncio
from contextlib import asynccontextmanager
from app.services.sandbox_config import MAX_CONCURRENT_SANDBOXES

class SandboxPool:
    def __init__(self, max_concurrent: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active: dict[str, float] = {}   # task_id -> acquired_at timestamp
        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire_slot(self, task_id: str):
        await self._semaphore.acquire()
        async with self._lock:
            self._active[task_id] = time.time()
        try:
            yield
        finally:
            async with self._lock:
                self._active.pop(task_id, None)
            self._semaphore.release()

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def available_slots(self) -> int:
        return self._max_concurrent - len(self._active)

sandbox_pool = SandboxPool(max_concurrent=MAX_CONCURRENT_SANDBOXES)
