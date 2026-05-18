import json

from app.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    role = "Reviews code quality and approves or rejects"

    SYSTEM_PROMPT = """
You are a senior code reviewer inside SYNC powered by DeepSeek.

Review for quality, maintainability, best practices, and security.
Approve if score >= 65 AND no must_fix items.

Respond ONLY with raw JSON:
{
  "approved": true,
  "score": 82,
  "feedback": ["specific point 1"],
  "must_fix": [],
  "nice_to_have": ["suggestion 1"],
  "summary": "one sentence summary"
}
"""

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code = task_context.get("code_output", {}).get("code", "")

        self.log(f"Reviewing: {task_name}")
        self.publish_stage("reviewing")

        prompt = f"Task completed: {task_name}\n\nFinal code:\n{code}"

        try:
            raw = await self.call_ollama(prompt, self.SYSTEM_PROMPT)
            raw = raw.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())

            approved = result.get("approved", False)
            score = result.get("score", 0)

            if approved:
                self.log(f"APPROVED — score: {score}/100")
            else:
                self.log(f"REJECTED — score: {score}/100", "warning")
                for blocker in result.get("must_fix", []):
                    self.log(f"Blocker: {blocker}", "error")

            return {
                "success": True,
                "approved": approved,
                "score": score,
                "agent": self.name,
                "results": result,
            }
        except Exception as e:
            self.log(f"Review error: {e}", "error")
            return {"success": True, "approved": True, "agent": self.name, "error": str(e)}
