import logging
import asyncio
from app.services.execution_queue import execution_queue
from app.agents import pipeline_orchestrator
from app.services.graph_executor import graph_executor
from app.database.session import SessionLocal

logger = logging.getLogger("sync.pipeline_worker")

class EventBroadcasterPlaceholder:
    async def broadcast(self, event_data: dict):
        from app.services.redis_client import publish_event
        event_name = event_data.get("type")
        payload = {k: v for k, v in event_data.items() if k != "type"}
        publish_event(event_name, payload)

event_broadcaster = EventBroadcasterPlaceholder()

class PipelineWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self._running = False

    async def run_forever(self):
        self._running = True
        while self._running:
            try:
                payload = await execution_queue.dequeue(timeout=5)
                if payload is None:
                    continue
                task_id = payload["task_id"]
                await event_broadcaster.broadcast({"type": "task_dequeued", "task_id": task_id, "worker_id": self.worker_id})
                
                db = SessionLocal()
                try:
                    args = payload["args"].copy()
                    if payload.get("mode") == "graph":
                        await graph_executor.run_graph(args["workflow_id"], db)
                    else:
                        from uuid import UUID
                        wf_id = UUID(args["workflow_id"])
                        await pipeline_orchestrator.run_pipeline(wf_id, db)
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} failed task {task_id}: {e}")
                    await event_broadcaster.broadcast({"type": "task_failed_unexpectedly", "task_id": task_id, "error": str(e)})
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        self._running = False
