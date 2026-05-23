from __future__ import annotations

from datetime import datetime
import json

from app.skills.skill_router import skill_router
from app.services.log_service import create_log
from app.services.redis_client import publish_event


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

    async def call_skill(
        self, skill_name: str, prompt: str, extra_context: str = ""
    ) -> str:
        """
        Call a named skill via the SkillRouter.
        Logs timing and errors automatically.
        """
        self.log(f"Calling skill: {skill_name}", "debug")
        try:
            result = await skill_router.call(
                skill_name=skill_name,
                prompt=prompt,
                extra_context=extra_context,
            )
            self.log(f"Skill '{skill_name}' returned response", "debug")
            return result
        except Exception as e:
            self.log(
                f"Skill '{skill_name}' failed: {type(e).__name__}: {e}",
                "error",
            )
            raise

    def publish_stage(self, stage: str) -> None:
        publish_event(
            "agent_status_changed",
            {
                "task_id": str(self.task_id),
                "workflow_id": str(self.workflow_id),
                "agent_name": self.name,
                "model": "dynamic",
                "pipeline_stage": stage,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def parse_json_robust(raw: str) -> any:
        """
        Try multiple strategies to parse JSON from model response.
        Returns parsed dict/list or raises ValueError.
        """
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        cleaned = raw
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue

        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            return json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        raise ValueError(f"Could not parse JSON from response: {raw[:200]}")

def get_agent_for_type(agent_type: str):
    from app.agents.coder_agent    import CoderAgent
    from app.agents.tester_agent   import TesterAgent
    from app.agents.debugger_agent import DebuggerAgent
    from app.agents.reviewer_agent import ReviewerAgent
    from app.agents.planner_agent  import PlannerAgent

    agent_map = {
        "coder":    CoderAgent,
        "tester":   TesterAgent,
        "debugger": DebuggerAgent,
        "reviewer": ReviewerAgent,
        "planner":  PlannerAgent,
    }

    cls = agent_map.get(agent_type)
    return cls
