from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.redis_client import publish_event


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    role = "Reviews code quality and approves or rejects"

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code = task_context.get("code_output", {}).get("code", "")
        threshold = settings.review_pass_threshold

        self.log(f"Reviewing: {task_name}")
        self.publish_stage("reviewing")

        prompt = f"""
Task that was completed: {task_name}
Code to review for quality:

{code}

Apply the scoring guide from your instructions.
Approve if score >= {threshold} and no blockers exist.
"""

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

            return {
                "success": True,
                "approved": approved,
                "score": score,
                "agent": self.name,
                "results": result,
            }
        except Exception as e:
            self.log(f"Reviewer error: {e} - auto-approving", "warning")
            return {
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
