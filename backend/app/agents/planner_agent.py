import httpx
import json

from app.core.config import settings
from app.agents.model_router import get_model

PLANNER_SYSTEM_PROMPT = """
You are a master orchestrator inside SYNC, powered by Kimi.
Decompose the user's goal into 3-6 concrete tasks.

Return ONLY a raw JSON array:
[
    {
        "name": "short task name",
        "description": "detailed description",
        "agent_name": "coder",
        "priority": 1,
        "dependencies": []
    }
]

agent_name must be one of: coder, tester, debugger, reviewer
Use "coder" for most tasks. Priority is execution order (1 = first).
dependencies is a list of task names that must complete first.
No markdown, no extra text.
"""


async def plan_workflow(goal: str) -> list[dict]:
    """
    Send a goal to Ollama/Kimi and get back a task list.
    Returns list of task dicts or fallback list on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": get_model("planner"),
                    "prompt": f"{PLANNER_SYSTEM_PROMPT}\n\nGoal: {goal}",
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            raw = response.json().get("response", "[]")

            tasks = json.loads(raw)
            if isinstance(tasks, list) and tasks:
                return tasks
    except Exception as e:
        print(f"[Planner] Ollama error: {e}")

    return [
        {
            "name": "Implement core logic",
            "description": goal,
            "agent_name": "coder",
            "priority": 1,
            "dependencies": [],
        },
        {
            "name": "Write tests",
            "description": f"Test: {goal}",
            "agent_name": "coder",
            "priority": 2,
            "dependencies": ["Implement core logic"],
        },
        {
            "name": "Review quality",
            "description": f"Review: {goal}",
            "agent_name": "coder",
            "priority": 3,
            "dependencies": ["Write tests"],
        },
    ]
