import httpx
import json

from app.core.config import settings

PLANNER_SYSTEM_PROMPT = """
You are a workflow planning agent for SYNC, an AI orchestration
platform. When given a goal, you break it into concrete,
executable tasks for specialized AI agents.

Respond ONLY with a valid JSON array. No explanation. No markdown.
No code blocks. Just the raw JSON array.

Each task object must have exactly these fields:
{
  "name": "short task name (max 50 chars)",
  "description": "what this task does (max 200 chars)",
  "agent_name": "one of: programmer, tester, debugger, researcher, writer"
}

Create between 3 and 6 tasks. Make them specific and actionable.
"""


async def plan_workflow(goal: str) -> list[dict]:
    """
    Send a goal to Ollama/Mistral and get back a task list.
    Returns list of task dicts or empty list on failure.
    """
    prompt = f"Break this goal into tasks: {goal}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": f"{PLANNER_SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            result = response.json()
            raw = result.get("response", "[]")

            # Clean response in case model wraps in markdown
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            tasks = json.loads(raw)
            if isinstance(tasks, list):
                return tasks
            if isinstance(tasks, dict):
                if "tasks" in tasks and isinstance(tasks["tasks"], list):
                    return tasks["tasks"]
                if {"name", "description", "agent_name"}.issubset(tasks.keys()):
                    return [tasks]
            return []

    except Exception as e:
        print(f"[Planner] Ollama error: {e}")
        # Fallback tasks if Ollama fails
        return [
            {
                "name": "Research & Planning",
                "description": f"Research and plan approach for: {goal}",
                "agent_name": "researcher",
            },
            {
                "name": "Implementation",
                "description": "Implement the core solution",
                "agent_name": "programmer",
            },
            {
                "name": "Testing & Validation",
                "description": "Test and validate the implementation",
                "agent_name": "tester",
            },
        ]
