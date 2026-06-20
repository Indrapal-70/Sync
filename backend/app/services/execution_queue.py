import json
import asyncio
from app.services.redis_client import get_redis, publish_event

class ExecutionQueue:
    QUEUE_KEY = "sync:execution_queue"
    POSITION_KEY_PREFIX = "sync:queue_position:"

    async def enqueue(self, task_id: str, payload: dict) -> int:
        """RPUSH the JSON-serialized payload. Returns 0-indexed queue position."""
        def _run():
            r = get_redis()
            pipe = r.pipeline()
            pipe.rpush(self.QUEUE_KEY, json.dumps(payload))
            pipe.llen(self.QUEUE_KEY)
            res = pipe.execute()
            return res[1] - 1
        
        pos = await asyncio.to_thread(_run)
        return pos

    async def dequeue(self, timeout: int = 5) -> dict | None:
        """BLPOP with timeout. Returns the deserialized payload or None on timeout."""
        def _run():
            r = get_redis()
            res = r.blpop(self.QUEUE_KEY, timeout=timeout)
            if res:
                return json.loads(res[1])
            return None
        
        payload = await asyncio.to_thread(_run)
        if payload:
            await self._broadcast_positions()
        return payload

    async def get_queue_position(self, task_id: str) -> int | None:
        """LRANGE the full queue, find task_id, return its index. None if not present."""
        def _run():
            r = get_redis()
            items = r.lrange(self.QUEUE_KEY, 0, -1)
            for idx, item_str in enumerate(items):
                try:
                    item = json.loads(item_str)
                    if item.get("task_id") == task_id:
                        return idx
                except Exception:
                    continue
            return None
        
        return await asyncio.to_thread(_run)

    async def remove(self, task_id: str) -> bool:
        """LREM the entry matching task_id. Returns True if something was removed."""
        def _run():
            r = get_redis()
            items = r.lrange(self.QUEUE_KEY, 0, -1)
            for item_str in items:
                try:
                    item = json.loads(item_str)
                    if item.get("task_id") == task_id:
                        removed = r.lrem(self.QUEUE_KEY, count=1, value=item_str)
                        return removed > 0
                except Exception:
                    continue
            return False

        removed = await asyncio.to_thread(_run)
        if removed:
            await self._broadcast_positions()
        return removed

    async def queue_length(self) -> int:
        """LLEN of the queue."""
        def _run():
            r = get_redis()
            return r.llen(self.QUEUE_KEY)
        
        return await asyncio.to_thread(_run)

    async def _broadcast_positions(self):
        def _get_all():
            r = get_redis()
            return r.lrange(self.QUEUE_KEY, 0, -1)
        
        items = await asyncio.to_thread(_get_all)
        for idx, item_str in enumerate(items):
            try:
                payload = json.loads(item_str)
                tid = payload.get("task_id")
                if tid:
                    publish_event("queue_position_updated", {
                        "task_id": tid,
                        "position": idx
                    })
            except Exception:
                continue

execution_queue = ExecutionQueue()
