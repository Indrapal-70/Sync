import asyncio
from datetime import datetime
from uuid import UUID
from app.core.config import settings
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.coder_agent import CoderAgent
from app.agents.tester_agent import TesterAgent
from app.agents.debugger_agent import DebuggerAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.models.task import Task
from app.models.workflow import Workflow
from app.services.log_service import create_log
from app.services.redis_client import publish_event

MAX_DEBUG_RETRIES = 3
MAX_REVIEW_RETRIES = 2

def _get_model_for_agent(agent_name: str) -> str:
    if agent_name in ["coder", "tester"]:
        return settings.builder_model
    return settings.thinker_model

async def run_pipeline(workflow_id: UUID, db: Session):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return

    _set_workflow_status(db, workflow, "running")
    create_log(
        db,
        workflow_id,
        f"🚀 Pipeline started: {workflow.name}",
        "info",
        agent_name="planner",
        pipeline_stage="planning",
    )

    tasks = (
        db.query(Task)
        .filter(Task.workflow_id == workflow_id)
        .order_by(Task.created_at.asc())
        .all()
    )

    completed_names: set[str] = set()
    all_success = True

    remaining = list(tasks)
    while remaining:
        ready = [
            t
            for t in remaining
            if all(dep in completed_names for dep in (t.input_data or {}).get("dependencies", []))
        ]
        if not ready:
            ready = [remaining[0]]

        for task in ready:
            success = await _run_task_pipeline(task, workflow_id, db)
            if success:
                completed_names.add(task.name)
            else:
                all_success = False
            remaining.remove(task)

    final = "completed" if all_success else "failed"
    _set_workflow_status(db, workflow, final)
    create_log(
        db,
        workflow_id,
        f"✅ Pipeline {final}: {workflow.name}",
        "info",
        agent_name="planner",
        pipeline_stage="done",
    )


async def _run_task_pipeline(task: Task, workflow_id: UUID, db: Session) -> bool:
    task_id = task.id
    context = {
        "name": task.name,
        "description": task.description,
        "input_data": task.input_data or {},
        "previous_error": None,
        "code_output": {},
        "test_results": {},
    }

    _set_task(db, task, status="running", current_agent="coder", pipeline_stage="coding")

    coder = CoderAgent(db, workflow_id, task_id)
    coder_result = await coder.run(context)
    coder_result["model_used"] = _get_model_for_agent("coder")
    create_log(db, workflow_id, f"[CODER] Completed via {coder_result['model_used']}", "debug", task_id)
    _save_agent_output(db, task, "coder", coder_result)

    if not coder_result["success"]:
        _set_task(db, task, status="failed", pipeline_stage="coding_failed")
        return False

    context["code_output"] = coder_result["output"]

    tests_passed = False
    debug_attempts = 0

    while debug_attempts <= MAX_DEBUG_RETRIES:
        _set_task(db, task, current_agent="tester", pipeline_stage="testing")
        tester = TesterAgent(db, workflow_id, task_id)
        test_result = await tester.run(context)
        test_result["model_used"] = _get_model_for_agent("tester")
        create_log(db, workflow_id, f"[TESTER] Completed via {test_result['model_used']}", "debug", task_id)
        context["test_results"] = test_result
        _save_agent_output(db, task, "tester", test_result)

        if test_result.get("all_passed"):
            tests_passed = True
            break

        if debug_attempts >= MAX_DEBUG_RETRIES:
            create_log(
                db,
                workflow_id,
                f"❌ Max debug retries ({MAX_DEBUG_RETRIES}) reached for: {task.name}",
                "error",
                task_id,
                agent_name="debugger",
                pipeline_stage="debugging_failed",
            )
            break

        debug_attempts += 1
        create_log(
            db,
            workflow_id,
            f"🔧 Debug attempt {debug_attempts}/{MAX_DEBUG_RETRIES}: {task.name}",
            "warning",
            task_id,
            agent_name="debugger",
            pipeline_stage="debugging",
        )

        _set_task(
            db,
            task,
            current_agent="debugger",
            pipeline_stage="debugging",
            retry_count=debug_attempts,
        )
        debugger = DebuggerAgent(db, workflow_id, task_id)
        debug_result = await debugger.run(context)
        debug_result["model_used"] = _get_model_for_agent("debugger")
        create_log(db, workflow_id, f"[DEBUGGER] Completed via {debug_result['model_used']}", "debug", task_id)
        _save_agent_output(db, task, "debugger", debug_result)

        if debug_result["success"]:
            context["code_output"]["code"] = debug_result["fixed_code"]
            context["previous_error"] = str(
                test_result.get("results", {}).get("critical_issues", [])
            )

    if not tests_passed:
        _set_task(db, task, status="failed", pipeline_stage="testing_failed")
        return False

    review_passed = False
    review_attempts = 0

    while review_attempts <= MAX_REVIEW_RETRIES:
        _set_task(db, task, current_agent="reviewer", pipeline_stage="reviewing")
        reviewer = ReviewerAgent(db, workflow_id, task_id)
        review_result = await reviewer.run(context)
        review_result["model_used"] = _get_model_for_agent("reviewer")
        create_log(db, workflow_id, f"[REVIEWER] Completed via {review_result['model_used']}", "debug", task_id)
        _save_agent_output(db, task, "reviewer", review_result)

        if review_result.get("approved"):
            review_passed = True
            break

        review_attempts += 1
        if review_attempts > MAX_REVIEW_RETRIES:
            break

        must_fix = review_result.get("results", {}).get("must_fix", [])
        create_log(
            db,
            workflow_id,
            f"🔁 Review rejected (attempt {review_attempts}): {must_fix}",
            "warning",
            task_id,
            agent_name="reviewer",
            pipeline_stage="reviewing",
        )
        context["previous_error"] = str(must_fix)

        _set_task(db, task, current_agent="coder", pipeline_stage="coding_revision")
        coder = CoderAgent(db, workflow_id, task_id)
        coder_result = await coder.run(context)
        coder_result["model_used"] = _get_model_for_agent("coder")
        create_log(db, workflow_id, f"[CODER] Completed via {coder_result['model_used']}", "debug", task_id)
        if coder_result["success"]:
            context["code_output"] = coder_result["output"]

    _finalize_task(db, task, context)
    return review_passed

def _finalize_task(db, task, context):
    model_summary = {}
    if task.agent_output:
        for output in task.agent_output.values():
            if isinstance(output, dict) and "model_used" in output:
                m = output["model_used"]
                model_summary[m] = model_summary.get(m, 0) + 1
    
    out_data = context.get("code_output", {})
    if not isinstance(out_data, dict):
        out_data = {"raw": out_data}
    out_data["model_summary"] = model_summary
    
    _set_task(
        db,
        task,
        status="completed",
        current_agent=None,
        pipeline_stage="done",
        output_data=out_data,
        model_summary=model_summary
    )


def _set_workflow_status(db, workflow, status: str):
    workflow.status = status
    workflow.updated_at = datetime.utcnow()
    db.commit()
    publish_event("workflow_updated", {"id": str(workflow.id), "status": status})


def _set_task(db, task, **kwargs):
    for k, v in kwargs.items():
        if hasattr(task, k):
            setattr(task, k, v)
    task.updated_at = datetime.utcnow()
    db.commit()
    payload = {
        "id": str(task.id),
        "workflow_id": str(task.workflow_id),
        "status": task.status,
        "current_agent": task.current_agent,
        "pipeline_stage": task.pipeline_stage,
        "retry_count": task.retry_count,
        "name": task.name,
    }
    if kwargs.get("model_summary"):
        payload["model_summary"] = kwargs["model_summary"]
    
    publish_event("task_updated", payload)


def _save_agent_output(db, task, agent_name: str, result: dict):
    outputs = task.agent_output or {}
    outputs[agent_name] = result
    task.agent_output = outputs
    if agent_name == "tester":
        task.test_results = result
    if agent_name == "reviewer":
        task.review_results = result
    task.updated_at = datetime.utcnow()
    db.commit()
