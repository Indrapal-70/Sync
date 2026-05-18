import json

from app.agents.base_agent import BaseAgent
from app.tools.tool_executor import execute_tool


class CoderAgent(BaseAgent):
    name = "coder"
    role = "Writes code to complete a task, can write files to workspace"

    SYSTEM_PROMPT = """
You are an expert software engineer inside SYNC, an AI orchestration platform.
Your job: write clean, working code to complete the given task.

You may optionally emit a tool call to write output files. If you do, include a
"tool_call" field in your JSON.

Respond with ONLY a raw JSON object — no markdown, no code fences:
{
  "code": "complete code here",
  "language": "python",
  "explanation": "brief explanation",
  "dependencies": ["list", "of", "imports"],
  "test_hints": ["things the tester should verify"],
  "tool_call": {
    "tool": "write_file",
    "args": { "path": "relative/path.py", "content": "..." }
  }
}
Omit "tool_call" if no file write is needed.
"""

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        task_desc = task_context.get("description", "")
        prev_error = task_context.get("previous_error", "")

        self.log(f"Starting to code: {task_name}")
        self.publish_stage("coding")

        prompt = f"Task: {task_name}\nDescription: {task_desc}"
        if prev_error:
            prompt += f"\n\nPrevious attempt FAILED:\n{prev_error}\nFix these issues."

        try:
            raw = await self.call_ollama(prompt, self.SYSTEM_PROMPT)
            result = self._parse_json(raw)

            if "tool_call" in result:
                tc = result["tool_call"]
                tool_result = await execute_tool(tc["tool"], tc.get("args", {}))
                self.log(
                    f"Tool {tc['tool']}: {tool_result.get('result', tool_result.get('error'))}"
                )

            self.log(f"Code written ({result.get('language', '?')})")
            return {"success": True, "agent": self.name, "output": result}
        except Exception as e:
            self.log(f"Coding failed: {e}", "error")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "output": {"code": "", "explanation": "Failed"},
            }

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
