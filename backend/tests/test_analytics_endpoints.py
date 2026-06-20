import pytest


@pytest.mark.asyncio
async def test_agent_performance_endpoint_200(async_client):
    response = await async_client.get("/api/v1/analytics/agent-performance?days=7")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_agent_performance_returns_list(async_client):
    response = await async_client.get("/api/v1/analytics/agent-performance?days=7")
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_healing_summary_endpoint_shape(async_client):
    response = await async_client.get("/api/v1/analytics/healing-summary?days=7")
    assert response.status_code == 200
    data = response.json()
    for key in ["total_healing_cycles", "resolved", "unresolved", "avg_cycles_per_task"]:
        assert key in data


@pytest.mark.asyncio
async def test_task_timeline_endpoint_unknown_task_returns_empty(async_client):
    response = await async_client.get("/api/v1/analytics/task-timeline/never-existed-999")
    assert response.status_code == 200
    assert response.json() == []
