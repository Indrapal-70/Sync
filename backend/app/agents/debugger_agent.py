import json

from app.agents.base_agent import BaseAgent


class DebuggerAgent(BaseAgent):
    name = "debugger"
    role = "Analyzes test failures and produces fixed code"

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code = task_context.get("code_output", {}).get("code", "")
        test_results = task_context.get("test_results", {})
        critical_issues = test_results.get("results", {}).get("critical_issues", [])
        prev_attempts = task_context.get("prev_debug_attempts", [])

        self.log(f"Debugging: {task_name}", "warning")
        self.publish_stage("debugging")

        prev_context = ""
        if prev_attempts:
            prev_context = "Previous failed fix attempts:\n"
            for i, attempt in enumerate(prev_attempts):
                prev_context += (
                    f"  Attempt {i + 1}: {attempt.get('root_cause', 'unknown')}\n"
                )
            prev_context += "Try a DIFFERENT approach - do not repeat previous fixes.\n"

        prompt = f"""
Task: {task_name}

Code that failed tests:
{code}

Critical failures to fix:
{json.dumps(critical_issues, indent=2)}

All test results:
{json.dumps(test_results.get('results', {}), indent=2)}

{prev_context}
Produce the complete fixed code.
"""

        try:
            raw = await self.call_skill("debug", prompt)
            result = self.parse_json_robust(raw)

            fixed_code = result.get("fixed_code", "")
            if not fixed_code or len(fixed_code) < 10:
                import re

                code_blocks = re.findall(r"```[\w]*\n(.*?)```", raw, re.DOTALL)
                if code_blocks:
                    fixed_code = code_blocks[0]
                    result["fixed_code"] = fixed_code
                    self.log(
                        "Extracted code from markdown block as fallback",
                        "warning",
                    )

            for change in result.get("changes_made", []):
                self.log(f"Change: {change}", "debug")
            self.log(f"Root cause: {result.get('root_cause', 'unknown')}", "warning")

            confidence = result.get("confidence", "medium")
            low_confidence = confidence == "low"
            if low_confidence:
                self.log("Low confidence fix - extra testing will apply", "warning")

            return {
                "success": True,
                "agent": self.name,
                "fixed_code": fixed_code,
                "low_confidence": low_confidence,
                "output": result,
            }
        except Exception as e:
            self.log(f"Debug failed: {e}", "error")
            return {
                "success": False,
                "agent": self.name,
                "fixed_code": code,
                "low_confidence": True,
                "error": str(e),
                "output": {},
            }
