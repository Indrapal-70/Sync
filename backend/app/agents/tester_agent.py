import json

from app.agents.base_agent import BaseAgent
from app.tools.tool_executor import execute_tool


class TesterAgent(BaseAgent):
    name = "tester"
    role = "Validates code output, runs tests, identifies failures"

    SYSTEM_PROMPT = """
You are an expert QA engineer inside SYNC.

Analyze the provided code for:
1. Syntax errors
2. Logic errors
3. Missing edge case handling
4. Security vulnerabilities
5. Whether it solves the stated task

Optionally emit a "tool_call" to execute the code in the terminal.

Respond ONLY with raw JSON:
{
  "all_passed": true,
  "tests": [
    {
      "test_name": "descriptive name",
      "passed": true,
      "error_message": null,
      "severity": "critical"
    }
  ],
  "overall_quality": "good",
  "critical_issues": [],
  "warnings": [],
  "tool_call": {
    "tool": "run_command",
    "args": { "command": "python workspace/file.py" }
  }
}
Omit "tool_call" if not running code.
"""

    async def run(self, task_context: dict) -> dict:
        code_output = task_context.get("code_output", {})
        task_name = task_context.get("name", "")
        code = code_output.get("code", "")

        self.log(f"Testing: {task_name}")
        self.publish_stage("testing")

        if not code:
            self.log("No code to test", "error")
            return {
                "success": False,
                "all_passed": False,
                "agent": self.name,
                "tests": [
                    {
                        "test_name": "Code existence",
                        "passed": False,
                        "error_message": "No code produced",
                        "severity": "critical",
                    }
                ],
            }

        prompt = (
            f"Task: {task_name}\n"
            f"Code:\n{code}\n"
            f"Test hints: {code_output.get('test_hints', [])}"
        )

        try:
            raw = await self.call_ollama(prompt, self.SYSTEM_PROMPT)
            result = self._parse_json(raw)

            if "tool_call" in result:
                tc = result["tool_call"]
                exec_result = await execute_tool(tc["tool"], tc.get("args", {}))
                if not exec_result.get("success"):
                    result["all_passed"] = False
                    result["critical_issues"] = result.get("critical_issues", [])
                    result["critical_issues"].append(
                        f"Runtime error: {exec_result.get('stderr', exec_result.get('error'))}"
                    )
                self.log(
                    f"Executed code — return code: {exec_result.get('return_code', '?')}"
                )

            if result.get("all_passed"):
                self.log(f"Tests passed — quality: {result.get('overall_quality')}")
            else:
                self.log(
                    f"Tests FAILED — {len(result.get('critical_issues', []))} critical issues",
                    "warning",
                )

            return {
                "success": True,
                "all_passed": result.get("all_passed", False),
                "agent": self.name,
                "results": result,
            }
        except Exception as e:
            self.log(f"Testing error: {e}", "error")
            return {
                "success": False,
                "all_passed": False,
                "agent": self.name,
                "error": str(e),
            }

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
