from app.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    name = "coder"
    role = "Writes code to complete a task, can write files to workspace"

    async def run(self, task_context: dict) -> dict:
        task_name      = task_context.get("name", "")
        task_desc      = task_context.get("description", "")
        previous_error = task_context.get("previous_error")
        previous_code  = task_context.get("code_output", {}).get("code", "")
        db             = task_context.get("db")
        workflow_id    = task_context.get("workflow_id")
        task_id        = task_context.get("task_id")

        self.log(f"Starting task: {task_name}")
        self.publish_stage("coding")

        language_hint = self._detect_language(task_desc + " " + task_name)
        self.log(f"Detected language: {language_hint}", "debug")

        if previous_error:
            self.log("Running in REVISION mode", "debug")
            prompt = f"""
REVISION REQUEST - previous code failed.

Task: {task_name}
Description: {task_desc}
Language: {language_hint}

Previous code that failed:
{previous_code}

Errors to fix:
{previous_error}

Fix ONLY the errors. Keep working parts intact.
Write the complete fixed code in {language_hint}.
"""
        else:
            self.log("Running in INITIAL mode", "debug")
            prompt = f"""
Task: {task_name}
Description: {task_desc}
Language: Write this in {language_hint}.

Write complete, working code that solves this task.
"""

        try:
            raw = await self.call_skill("code", prompt)

            # ── P6-07: Detect and salvage truncated output ─────────────
            salvaged = False
            code_block_opens  = raw.count("```python") + raw.count("```javascript") \
                                + raw.count("```typescript") + raw.count("```sql") \
                                + raw.count("```bash")
            # Every open fence needs a closing ```, but there's also the
            # opening ``` itself — check if fences are balanced
            total_fences     = raw.count("```")
            code_block_closes = total_fences - code_block_opens  # closing fences

            is_truncated = (
                code_block_opens > 0
                and code_block_closes < code_block_opens
            )

            if is_truncated:
                self.log(
                    "[CODER] Truncated output detected — salvage pass starting",
                    "warning",
                )
                salvage_prompt = (
                    f"Complete this Python code "
                    f"(output ONLY the code, no explanation):\n\n{raw}"
                )
                raw = await self.call_skill("code", salvage_prompt)
                salvaged = True
                self.log("[CODER] Salvage pass complete")
            # ── End P6-07 ───────────────────────────────────────────────

            result = self.parse_json_robust(raw)

            code = result.get("code", "")
            if not code or len(code) < 10:
                self.log("Coder produced empty output", "error")
                return {
                    "success":  False,
                    "agent":    self.name,
                    "error":    "Empty code output",
                    "output":   {},
                    "salvaged": salvaged,
                }
            if len(code) > 50000:
                self.log(
                    f"Code too large ({len(code)} chars) - truncating",
                    "warning",
                )
                result["code"] = code[:50000]

            self.log(f"Code written in {result.get('language', language_hint)}")
            result["salvaged"] = salvaged
            return {"success": True, "agent": self.name, "output": result}

        except Exception as e:
            self.log(f"Coding failed: {e}", "error")
            return {
                "success":  False,
                "agent":    self.name,
                "error":    str(e),
                "output":   {"code": "", "explanation": "Failed"},
                "salvaged": False,
            }

    def _detect_language(self, text: str) -> str:
        text = text.lower()
        if any(w in text for w in ["python", "django", "flask", "fastapi", "pytest"]):
            return "Python"
        if any(
            w in text
            for w in ["javascript", "react", "node", "typescript", "vue", "next"]
        ):
            return "TypeScript"
        if any(w in text for w in ["sql", "postgres", "database", "query", "schema"]):
            return "SQL"
        if any(w in text for w in ["bash", "shell", "script", "linux", "grep", "awk"]):
            return "Bash"
        return "Python"
