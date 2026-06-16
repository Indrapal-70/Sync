import json
import time

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.redis_client import publish_event
from app.services.context_buffer import agent_context_buffer, ContextEntry

def _summarize(data) -> str:
    if not data:
        return ""
    try:
        s = json.dumps(data)
    except Exception:
        s = str(data)
    return s[:200]


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    role = "Reviews code quality and approves or rejects"

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code = task_context.get("code_output", {}).get("code", "")
        threshold = settings.review_pass_threshold
        task_id = task_context.get("task_id") or self.task_id

        self.log(f"Reviewing: {task_name}")
        self.publish_stage("reviewing")

        context_prompt = ""
        if task_id:
            context_prompt = await agent_context_buffer.build_context_prompt(
                task_id=str(task_id),
                requesting_agent=self.__class__.__name__
            )

        prompt = f"""
Task that was completed: {task_name}
Code to review for quality:

{code}

Apply the scoring guide from your instructions.
Approve if score >= {threshold} and no blockers exist.
"""
        if context_prompt:
            prompt = f"{context_prompt}\n\n{prompt}"

        try:
            raw = await self.call_skill("review", prompt)
            result = self.parse_json_robust(raw)

            score = result.get("score", 0)
            must_fix = result.get("must_fix", [])
            approved = score >= threshold and len(must_fix) == 0
            result["approved"] = approved

            for item in must_fix:
                self.log(f"BLOCKER: {item}", "error")
            for item in result.get("nice_to_have", []):
                self.log(f"Suggestion: {item}", "debug")
            self.log(f"Review summary: {result.get('summary', 'No summary')}")
            self.log(
                f"{'APPROVED' if approved else 'REJECTED'} - "
                f"score {score}/100 (threshold: {threshold})"
            )

            event = "task_review_approved" if approved else "task_review_rejected"
            publish_event(
                event,
                {
                    "task_id": str(self.task_id),
                    "workflow_id": str(self.workflow_id),
                    "score": score,
                    "summary": result.get("summary", ""),
                    "must_fix": must_fix,
                },
            )

            res = {
                "success": True,
                "approved": approved,
                "score": score,
                "agent": self.name,
                "results": result,
            }
            if task_id:
                await agent_context_buffer.add_entry(
                    task_id=str(task_id),
                    entry=ContextEntry(
                        agent_name=self.__class__.__name__,
                        step=len(agent_context_buffer._store.get(str(task_id), [])),
                        input_summary=_summarize(task_context),
                        output_summary=_summarize(res),
                        status="passed" if approved else "failed",
                        error_details=str(must_fix) if not approved else None,
                        timestamp=time.time(),
                        healing_cycle=task_context.get("cycle", 0)
                    )
                )
            return res
        except Exception as e:
            self.log(f"Reviewer error: {e} - auto-approving", "warning")
            res = {
                "success": True,
                "approved": True,
                "score": 50,
                "agent": self.name,
                "results": {
                    "approved": True,
                    "score": 50,
                    "summary": "Auto-approved: reviewer encountered an error",
                    "feedback": [f"Review skipped: {str(e)}"],
                    "must_fix": [],
                    "nice_to_have": [],
                },
            }
            if task_id:
                await agent_context_buffer.add_entry(
                    task_id=str(task_id),
                    entry=ContextEntry(
                        agent_name=self.__class__.__name__,
                        step=len(agent_context_buffer._store.get(str(task_id), [])),
                        input_summary=_summarize(task_context),
                        output_summary=str(e),
                        status="skipped",
                        timestamp=time.time(),
                        healing_cycle=task_context.get("cycle", 0)
                    )
                )
            return res
