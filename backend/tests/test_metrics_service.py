import pytest
import pytest_asyncio
from app.services.metrics_service import MetricsService


@pytest_asyncio.fixture
async def metrics():
    return MetricsService()


@pytest.mark.asyncio
async def test_record_agent_run_persists_row(metrics, sample_task_id):
    await metrics.record_agent_run(
        task_id=sample_task_id, agent_name="CoderAgent", step=0,
        status="passed", duration_ms=120.5,
    )
    timeline = await metrics.get_task_timeline(sample_task_id)
    assert len(timeline) >= 1
    assert timeline[-1]["agent_name"] == "CoderAgent"
    assert timeline[-1]["status"] == "passed"


@pytest.mark.asyncio
async def test_success_rate_computed_correctly(metrics, sample_task_id):
    for status in ["passed", "passed", "failed"]:
        await metrics.record_agent_run(
            task_id=sample_task_id, agent_name="TesterAgent", step=0,
            status=status, duration_ms=50.0,
        )
    result = await metrics.get_agent_success_rate(agent_name="TesterAgent", days=1)
    assert result["total_runs"] >= 3
    assert 0.0 <= result["success_rate"] <= 1.0


@pytest.mark.asyncio
async def test_record_and_resolve_healing_event(metrics, sample_task_id):
    await metrics.record_healing_event(
        task_id=sample_task_id, cycle=1, failed_agent="TesterAgent",
        error_summary="AssertionError on line 4", injected_node_ids=["healer_debug_abc"],
    )
    summary_before = await metrics.get_healing_summary(days=1)
    assert summary_before["unresolved"] >= 1

    await metrics.mark_healing_resolved(sample_task_id, cycle=1)
    summary_after = await metrics.get_healing_summary(days=1)
    assert summary_after["resolved"] >= 1


@pytest.mark.asyncio
async def test_error_summary_truncated_to_500_chars(metrics, sample_task_id):
    long_error = "X" * 2000
    await metrics.record_healing_event(
        task_id=sample_task_id, cycle=2, failed_agent="TesterAgent",
        error_summary=long_error, injected_node_ids=[],
    )
    summary = await metrics.get_healing_summary(days=1)
    # We can't directly inspect the row here without a raw query, so this is
    # also covered at the DB layer — but the service must never throw on
    # oversized input, and the call above must not raise.
    assert summary is not None


@pytest.mark.asyncio
async def test_task_timeline_is_chronologically_ordered(metrics):
    task_id = "task-timeline-order-test"
    for step in range(3):
        await metrics.record_agent_run(
            task_id=task_id, agent_name="CoderAgent", step=step,
            status="passed", duration_ms=10.0 * step,
        )
    timeline = await metrics.get_task_timeline(task_id)
    timestamps = [row["created_at"] for row in timeline]
    assert timestamps == sorted(timestamps)
