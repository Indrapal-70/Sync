"""
P6-17 — Integration test for Template-driven Workflow Execution.

Validates the full lifecycle:
  1. Create a template via POST /api/templates
  2. Verify template persists via GET /api/templates/{id}
  3. Create a workflow
  4. Execute the workflow with template_id injection (bypasses LLM planner)
  5. Verify task count matches template schema
  6. Save the executed workflow back as a new template
  7. Verify the round-trip template has correct schema
  8. Cleanup: delete both templates and the workflow

Requirements:
  - Backend must be running on http://localhost:8000
  - Database and Redis must be healthy
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def _req(method, path, body=None):
    """Minimal stdlib HTTP helper — no third-party deps required."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        # Handle 307 redirect (trailing slash) by retrying with Location header
        if e.code == 307:
            location = e.headers.get("Location", "")
            if location:
                req2 = urllib.request.Request(location, data=data, method=method)
                req2.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req2, timeout=30) as resp:
                    return json.loads(resp.read().decode())
        err_body = e.read().decode()
        print(f"  HTTP {e.code}: {err_body}")
        raise


def check(label, condition, detail=""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    extra = f" — {detail}" if detail else ""
    print(f"  [{status}] {label}{extra}")
    return condition


def main():
    global PASS, FAIL
    print("=" * 72)
    print("  SYNC Phase 6 — Template-driven Workflow Integration Test")
    print("=" * 72)

    # ── Step 0: Health gate ──────────────────────────────────────────────
    print("\n[Step 0] Health gate")
    try:
        h = _req("GET", "/health")
        check("Server alive", h.get("status") == "ok", f"status={h.get('status')}")
        check("Database ok", h.get("database") == "ok")
        check("Redis ok", h.get("redis") == "ok")
    except Exception as e:
        print(f"  [FATAL] Cannot reach server: {e}")
        sys.exit(1)

    # ── Step 1: Create a template ────────────────────────────────────────
    print("\n[Step 1] Create template via API")
    template_payload = {
        "name": "E2E Test Template",
        "description": "Integration test template for P6-17",
        "tasks_schema": [
            {
                "name": "Analyze Requirements",
                "description": "Parse and validate the input requirements",
                "agent_name": "coder",
                "priority": 1,
                "dependencies": [],
            },
            {
                "name": "Generate Implementation",
                "description": "Write the core implementation code",
                "agent_name": "coder",
                "priority": 2,
                "dependencies": ["Analyze Requirements"],
            },
            {
                "name": "Run Unit Tests",
                "description": "Execute test suite against implementation",
                "agent_name": "tester",
                "priority": 3,
                "dependencies": ["Generate Implementation"],
            },
        ],
    }
    tmpl = _req("POST", "/api/templates", template_payload)
    template_id = tmpl.get("id")
    check("Template created", template_id is not None, f"id={template_id}")
    check("Name matches", tmpl.get("name") == "E2E Test Template")
    check(
        "Schema has 3 tasks",
        len(tmpl.get("tasks_schema", [])) == 3,
        f"got {len(tmpl.get('tasks_schema', []))}",
    )

    # ── Step 2: Verify template persists via GET ─────────────────────────
    print("\n[Step 2] Verify template via GET")
    fetched = _req("GET", f"/api/templates/{template_id}")
    check("GET returns same id", fetched.get("id") == template_id)
    check(
        "Schema intact after round-trip",
        len(fetched.get("tasks_schema", [])) == 3,
    )

    # ── Step 3: Create a workflow ────────────────────────────────────────
    print("\n[Step 3] Create workflow")
    wf = _req("POST", "/api/workflows", {
        "name": "P6-17 Template Test Workflow",
        "description": "Testing template-driven execution",
    })
    workflow_id = wf.get("id")
    check("Workflow created", workflow_id is not None, f"id={workflow_id}")

    # ── Step 4: Execute with template_id (bypasses LLM) ──────────────────
    print("\n[Step 4] Execute workflow with template_id injection")
    exec_result = _req("POST", f"/api/workflows/{workflow_id}/execute", {
        "template_id": template_id,
    })
    tasks_created = exec_result.get("tasks_created", 0)
    check(
        "Pipeline started",
        exec_result.get("message") == "Pipeline started",
        exec_result.get("message"),
    )
    check(
        "Task count matches template (3)",
        tasks_created == 3,
        f"tasks_created={tasks_created}",
    )

    # ── Step 5: Verify tasks in DB ───────────────────────────────────────
    print("\n[Step 5] Verify tasks persisted in database")
    time.sleep(1)  # brief wait for DB commit
    tasks = _req("GET", f"/api/tasks?workflow_id={workflow_id}")
    check(
        "Tasks found in DB",
        len(tasks) == 3,
        f"found {len(tasks)} tasks",
    )
    task_names = sorted([t.get("name", "") for t in tasks])
    expected_names = sorted(["Analyze Requirements", "Generate Implementation", "Run Unit Tests"])
    check(
        "Task names match template schema",
        task_names == expected_names,
        f"got {task_names}",
    )

    # Verify agent assignments
    agent_map = {t["name"]: t["agent_name"] for t in tasks}
    check(
        "Agent assignments preserved",
        agent_map.get("Analyze Requirements") == "coder"
        and agent_map.get("Run Unit Tests") == "tester",
        f"agents={agent_map}",
    )

    # ── Step 6: Save executed workflow back as a template ─────────────────
    print("\n[Step 6] Save-as-template round-trip")
    save_result = _req("POST", f"/api/workflows/{workflow_id}/save-as-template")
    round_trip_template_id = save_result.get("template_id")
    check(
        "Save-as-template succeeded",
        round_trip_template_id is not None,
        f"new_template_id={round_trip_template_id}",
    )
    check(
        "Correct task count saved",
        save_result.get("tasks_saved") == 3,
        f"tasks_saved={save_result.get('tasks_saved')}",
    )

    # ── Step 7: Verify round-trip template ────────────────────────────────
    print("\n[Step 7] Verify round-trip template integrity")
    rt_tmpl = _req("GET", f"/api/templates/{round_trip_template_id}")
    check(
        "Round-trip template has 3 tasks",
        len(rt_tmpl.get("tasks_schema", [])) == 3,
    )
    rt_names = sorted([t["name"] for t in rt_tmpl.get("tasks_schema", [])])
    check(
        "Round-trip names match originals",
        rt_names == expected_names,
        f"got {rt_names}",
    )

    # ── Step 8: Cleanup ──────────────────────────────────────────────────
    print("\n[Step 8] Cleanup test data")
    try:
        _req("DELETE", f"/api/templates/{template_id}")
        print("  Deleted original template")
    except Exception:
        print("  Warning: could not delete original template")

    try:
        _req("DELETE", f"/api/templates/{round_trip_template_id}")
        print("  Deleted round-trip template")
    except Exception:
        print("  Warning: could not delete round-trip template")

    try:
        _req("DELETE", f"/api/workflows/{workflow_id}")
        print("  Deleted test workflow")
    except Exception:
        print("  Warning: could not delete test workflow")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    total = PASS + FAIL
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed")
    if FAIL == 0:
        print("  [OK] ALL CHECKS PASSED - Template-driven workflow is fully operational")
    else:
        print("  [!!] SOME CHECKS FAILED - review output above")
    print("=" * 72)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
