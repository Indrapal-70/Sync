from app.agents.base_agent import BaseAgent
from app.services.docker_executor import docker_executor
from app.services.redis_client import publish_event
from app.services.context_buffer import agent_context_buffer, ContextEntry
import time
import json

def _summarize(data) -> str:
    if not data:
        return ""
    try:
        s = json.dumps(data)
    except Exception:
        s = str(data)
    return s[:200]


class TesterAgent(BaseAgent):
    name = "tester"
    role = "Validates code output, runs tests, identifies failures"

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code_output = task_context.get("code_output", {})
        code = code_output.get("code", "") or task_context.get("code", "")
        strict = task_context.get("strict_testing", False)
        test_code = task_context.get("test_code", "") or code_output.get("test_code", "") or "# No tests provided\nassert True"
        task_id = task_context.get("task_id") or self.task_id

        self.log(f"Testing task: {task_name}")
        if strict:
            self.log("STRICT mode active - warnings treated as critical", "warning")
        self.publish_stage("testing")

        context_prompt = ""
        if task_id:
            context_prompt = await agent_context_buffer.build_context_prompt(
                task_id=str(task_id),
                requesting_agent=self.__class__.__name__
            )

        if not code or len(code) < 10:
            self.log("No code to test", "error")
            res = {
                "success": True,
                "all_passed": False,
                "status": "failed",
                "agent": self.name,
                "results": {
                    "all_passed": False,
                    "tests": [
                        {
                            "test_name": "Code existence",
                            "passed": False,
                            "error_message": "No code was produced",
                            "severity": "critical",
                        }
                    ],
                    "overall_quality": "poor",
                    "critical_issues": ["No code provided"],
                    "warnings": [],
                },
            }
            if task_id:
                await agent_context_buffer.add_entry(
                    task_id=str(task_id),
                    entry=ContextEntry(
                        agent_name=self.__class__.__name__,
                        step=len(agent_context_buffer._store.get(str(task_id), [])),
                        input_summary=_summarize(task_context),
                        output_summary=_summarize(res),
                        status="failed",
                        error_details="No code was produced",
                        timestamp=time.time(),
                        healing_cycle=task_context.get("cycle", 0)
                    )
                )
            return res

        # Check if Docker is available
        docker_active = await docker_executor.health_check()
        if docker_active:
            try:
                sandbox_result = await docker_executor.run_code_in_sandbox(
                    code=code,
                    test_code=test_code,
                    timeout_seconds=30
                )
                
                # Broadcast sandbox result event
                publish_event("sandbox_result", {
                    "task_id": str(self.task_id),
                    "agent": self.name,
                    "success": sandbox_result["success"],
                    "exit_code": sandbox_result["exit_code"],
                    "duration_ms": sandbox_result["duration_ms"]
                })

                # Build the LLM prompt using real results
                prompt = f"""
You are a senior Python QA engineer reviewing real test execution output.

## Code Under Test
{code}

## Test Results (REAL EXECUTION)
Exit Code: {sandbox_result["exit_code"]}
Timed Out: {sandbox_result["timed_out"]}
Duration: {sandbox_result["duration_ms"]:.0f}ms

### STDOUT
{sandbox_result["stdout"][:3000]}

### STDERR
{sandbox_result["stderr"][:2000]}

## Your Job
{"Tests PASSED. Briefly confirm what was verified." if sandbox_result["success"] else "Tests FAILED. Identify the root cause from the output above and suggest a specific code fix."}
Do not re-run the tests. Do not invent results. Only analyze the output provided.
"""
                if context_prompt:
                    prompt = f"{context_prompt}\n\n{prompt}"

                llm_analysis = await self.call_skill("test", prompt)

                # Format backward-compatible results
                res = {
                    "status": "passed" if sandbox_result["success"] else "failed",
                    "success": True,
                    "all_passed": sandbox_result["success"],
                    "sandbox_result": sandbox_result,
                    "analysis": llm_analysis,
                    "results": {
                        "all_passed": sandbox_result["success"],
                        "tests": [
                            {
                                "test_name": "Sandbox Test Execution",
                                "passed": sandbox_result["success"],
                                "error_message": sandbox_result["stderr"] if not sandbox_result["success"] else None,
                                "severity": "critical" if not sandbox_result["success"] else "info"
                            }
                        ],
                        "overall_quality": "good" if sandbox_result["success"] else "poor",
                        "critical_issues": [sandbox_result["stderr"]] if not sandbox_result["success"] else []
                    },
                    "agent": self.name
                }
                if task_id:
                    await agent_context_buffer.add_entry(
                        task_id=str(task_id),
                        entry=ContextEntry(
                            agent_name=self.__class__.__name__,
                            step=len(agent_context_buffer._store.get(str(task_id), [])),
                            input_summary=_summarize(task_context),
                            output_summary=_summarize(res),
                            status=res["status"],
                            error_details=sandbox_result["stderr"] if not sandbox_result["success"] else None,
                            timestamp=time.time(),
                            healing_cycle=task_context.get("cycle", 0)
                        )
                    )
                return res
            except Exception as e:
                self.log(f"Sandbox execution failed: {e}", "error")
                # Fall through to fallback simulation on sandbox error

        # FALLBACK: Docker unavailable, using LLM simulation
        self.log("Docker unavailable, falling back to LLM simulation", "warning")
        publish_event("model_fallback_used", {
            "task_id": str(self.task_id),
            "agent_name": self.name,
            "reason": "Docker unavailable"
        })

        prompt = f"""
Task that was supposed to be solved: {task_name}
Description: {code_output.get('explanation', 'No explanation provided')}

Code to evaluate:
{code}

Test hints from the coder: {code_output.get('test_hints', [])}
{"Apply STRICT testing - treat warnings as critical failures." if strict else ""}

Evaluate thoroughly and return your test results.
"""
        if context_prompt:
            prompt = f"{context_prompt}\n\n{prompt}"

        try:
            raw = await self.call_skill("test", prompt)
            result = self.parse_json_robust(raw)

            tests = result.get("tests", [])
            if not tests:
                tests = [
                    {
                        "test_name": "Basic output check",
                        "passed": True,
                        "error_message": None,
                        "severity": "info",
                    }
                ]
                result["tests"] = tests
                self.log("No tests returned - adding default pass", "warning")

            all_passed = True
            for t in tests:
                if not t.get("passed"):
                    severity = t.get("severity", "critical")
                    if severity == "critical" or (strict and severity == "warning"):
                        all_passed = False
                        self.log(
                            f"FAIL [{severity}]: {t.get('test_name')}",
                            "error",
                        )
                    else:
                        self.log(f"WARN: {t.get('test_name')}", "warning")

            result["all_passed"] = all_passed

            passed = len([t for t in tests if t.get("passed")])
            failed = len(tests) - passed
            critical = len(
                [
                    t
                    for t in tests
                    if not t.get("passed") and t.get("severity") == "critical"
                ]
            )
            self.log(
                f"Tests: {passed} passed, {failed} failed "
                f"({critical} critical) - quality: {result.get('overall_quality')}"
            )

            res = {
                "status": "passed" if all_passed else "failed",
                "success": True,
                "all_passed": all_passed,
                "agent": self.name,
                "results": result,
            }
            if task_id:
                err_details = None
                if not all_passed:
                    err_details = str(result.get("critical_issues", [])) or "Simulation test failure"
                await agent_context_buffer.add_entry(
                    task_id=str(task_id),
                    entry=ContextEntry(
                        agent_name=self.__class__.__name__,
                        step=len(agent_context_buffer._store.get(str(task_id), [])),
                        input_summary=_summarize(task_context),
                        output_summary=_summarize(res),
                        status=res["status"],
                        error_details=err_details,
                        timestamp=time.time(),
                        healing_cycle=task_context.get("cycle", 0)
                    )
                )
            return res
        except Exception as e:
            self.log(f"Tester simulation failed: {e}", "error")
            res = {
                "status": "failed",
                "success": True,
                "all_passed": False,
                "agent": self.name,
                "results": {
                    "all_passed": False,
                    "tests": [
                        {
                            "test_name": "Tester error",
                            "passed": False,
                            "error_message": str(e),
                            "severity": "critical",
                        }
                    ],
                    "overall_quality": "unknown",
                    "critical_issues": [str(e)],
                    "warnings": [],
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
                        status="failed",
                        error_details=str(e),
                        timestamp=time.time(),
                        healing_cycle=task_context.get("cycle", 0)
                    )
                )
            return res
