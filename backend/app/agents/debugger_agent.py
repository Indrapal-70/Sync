import json

from app.agents.base_agent import BaseAgent


class DebuggerAgent(BaseAgent):
    name = "debugger"
    role = "Analyzes test failures and produces fixed code"

    SYSTEM_PROMPT = """
You are an expert debugger inside SYNC powered by DeepSeek.

You receive: original failing code + test failures + original task.
Fix ALL critical issues. Use deep reasoning.

Respond ONLY with raw JSON:
{
  "fixed_code": "complete fixed code",
  "language": "python",
  "changes_made": ["specific change 1", "specific change 2"],
  "root_cause": "what caused the failure",
  "confidence": "high"
}
"""

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code = task_context.get("code_output", {}).get("code", "")
        test_results = task_context.get("test_results", {})
        critical = test_results.get("results", {}).get("critical_issues", [])

        self.log(f"Debugging: {task_name}", "warning")
        self.publish_stage("debugging")

        prompt = (
            f"Task: {task_name}\n\n"
            f"Failing code:\n{code}\n\n"
            f"Critical issues:\n{json.dumps(critical, indent=2)}\n\n"
            f"All test results:\n{json.dumps(test_results.get('results', {}), indent=2)}"
        )

        try:
            raw = await self.call_ollama(prompt, self.SYSTEM_PROMPT)
            raw = raw.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())

            self.log(f"Root cause: {result.get('root_cause', '?')}")
            self.log(f"Changes: {result.get('changes_made', [])}", "debug")
            return {
                "success": True,
                "agent": self.name,
                "fixed_code": result.get("fixed_code", ""),
                "output": result,
            }
        except Exception as e:
            self.log(f"Debug failed: {e}", "error")
            return {"success": False, "agent": self.name, "error": str(e)}
