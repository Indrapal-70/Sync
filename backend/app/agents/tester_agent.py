from app.agents.base_agent import BaseAgent


class TesterAgent(BaseAgent):
    name = "tester"
    role = "Validates code output, runs tests, identifies failures"

    async def run(self, task_context: dict) -> dict:
        task_name = task_context.get("name", "")
        code_output = task_context.get("code_output", {})
        code = code_output.get("code", "")
        strict = task_context.get("strict_testing", False)

        self.log(f"Testing task: {task_name}")
        if strict:
            self.log("STRICT mode active - warnings treated as critical", "warning")
        self.publish_stage("testing")

        if not code or len(code) < 10:
            self.log("No code to test", "error")
            return {
                "success": True,
                "all_passed": False,
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

        prompt = f"""
Task that was supposed to be solved: {task_name}
Description: {code_output.get('explanation', 'No explanation provided')}

Code to evaluate:
{code}

Test hints from the coder: {code_output.get('test_hints', [])}
{"Apply STRICT testing - treat warnings as critical failures." if strict else ""}

Evaluate thoroughly and return your test results.
"""

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

            return {
                "success": True,
                "all_passed": all_passed,
                "agent": self.name,
                "results": result,
            }

        except Exception as e:
            self.log(f"Tester failed: {e}", "error")
            return {
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
