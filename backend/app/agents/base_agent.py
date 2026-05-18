from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx

from app.core.config import settings
from app.services.log_service import create_log
from app.services.redis_client import publish_event
from app.agents.model_router import get_model


class BaseAgent:
    name = "agent"
    role = ""

    def __init__(self, db, workflow_id, task_id):
        self.db = db
        self.workflow_id = workflow_id
        self.task_id = task_id

    def log(self, message: str, level: str = "info") -> None:
        prefix = f"[{self.name.upper()}]"
        create_log(
            self.db,
            self.workflow_id,
            f"{prefix} {message}",
            level,
            self.task_id,
            agent_name=self.name,
        )

    async def call_ollama(self, prompt: str, system: str = "") -> str:
        model = get_model(self.name)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json().get("response", "")

    def publish_stage(self, stage: str) -> None:
        publish_event(
            "agent_status_changed",
            {
                "task_id": str(self.task_id),
                "workflow_id": str(self.workflow_id),
                "agent_name": self.name,
                "model": get_model(self.name),
                "pipeline_stage": stage,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
