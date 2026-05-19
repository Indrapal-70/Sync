from app.skills.skill_router import skill_router
from app.agents.base_agent import BaseAgent


async def plan_workflow(goal: str, workflow_id=None, db=None) -> list[dict]:
    """
    Use the 'plan' skill (mistral) to break a goal into tasks.
    Returns list of task dicts or fallback list on any failure.
    """
    print(f"[Planner] Planning workflow for goal: {goal[:80]}...")

    prompt = f"""
    Project goal: {goal}

    Break this into specific, executable tasks for our AI agents.
    Remember: agents available are coder, tester, debugger, reviewer.
    """

    try:
        raw = await skill_router.call(
            skill_name="plan",
            prompt=prompt,
        )

        result = BaseAgent.parse_json_robust(raw)

        if isinstance(result, list) and len(result) > 0:
            print(f"[Planner] Generated {len(result)} tasks")
            return result

        print("[Planner] Response was not a valid task list")
        return _fallback_tasks(goal)

    except Exception as e:
        print(f"[Planner] Failed: {e} - using fallback tasks")
        return _fallback_tasks(goal)


def _fallback_tasks(goal: str) -> list[dict]:
    """Return 3 basic fallback tasks when planner fails."""
    return [
        {
            "name": "Research and Design",
            "description": f"Research approach and design solution for: {goal}",
            "agent_name": "coder",
            "priority": 1,
            "estimated_complexity": "medium",
            "dependencies": [],
        },
        {
            "name": "Implementation",
            "description": "Implement the designed solution",
            "agent_name": "coder",
            "priority": 2,
            "estimated_complexity": "medium",
            "dependencies": [],
        },
        {
            "name": "Testing and Validation",
            "description": "Test and validate the implementation",
            "agent_name": "tester",
            "priority": 3,
            "estimated_complexity": "low",
            "dependencies": [],
        },
    ]
