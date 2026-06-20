import pytest


@pytest.mark.asyncio
async def test_create_template_default_version(async_client):
    payload = {
        "name": "Versioning Test Template",
        "description": "A template to test default versioning",
        "tasks_schema": [
            {"name": "Step 1", "description": "Desc 1", "agent_name": "coder", "priority": 1}
        ]
    }
    response = await async_client.post("/api/templates/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["parent_template_id"] is None
    assert data["is_public"] is False
    assert data["usage_count"] == 0


@pytest.mark.asyncio
async def test_create_template_custom_version(async_client):
    payload = {
        "name": "Custom Version Template",
        "description": "Test custom version",
        "tasks_schema": [
            {"name": "Step 1", "description": "Desc 1", "agent_name": "coder", "priority": 1}
        ],
        "version": "2.1.0",
        "author": "Indra"
    }
    response = await async_client.post("/api/v1/templates/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.1.0"
    assert data["author"] == "Indra"


@pytest.mark.asyncio
async def test_fork_template_lifecycle(async_client):
    # 1. Create a parent template
    parent_payload = {
        "name": "Parent Template",
        "description": "Parent description",
        "tasks_schema": [
            {"name": "Step 1", "description": "Desc 1", "agent_name": "coder", "priority": 1}
        ],
        "version": "3.0.0",
        "is_public": True,
        "tags": ["parent", "gold"]
    }
    parent_resp = await async_client.post("/api/v1/templates/", json=parent_payload)
    assert parent_resp.status_code == 200
    parent_data = parent_resp.json()
    parent_id = parent_data["id"]

    # 2. Fork without payload (check defaults)
    fork_resp = await async_client.post(f"/api/v1/templates/{parent_id}/fork")
    assert fork_resp.status_code == 200
    fork_data = fork_resp.json()
    assert fork_data["id"] != parent_id
    assert fork_data["name"] == "Fork of Parent Template"
    assert fork_data["description"] == "Parent description"
    assert fork_data["version"] == "1.0.0"
    assert fork_data["parent_template_id"] == parent_id
    assert fork_data["is_public"] is False
    assert fork_data["tags"] == ["parent", "gold"]
    assert fork_data["usage_count"] == 0

    # 3. Fork with payload (check custom name and author)
    fork_payload = {
        "name": "My Custom Fork",
        "author": "Forker Bob"
    }
    fork_custom_resp = await async_client.post(f"/api/templates/{parent_id}/fork", json=fork_payload)
    assert fork_custom_resp.status_code == 200
    fork_custom_data = fork_custom_resp.json()
    assert fork_custom_data["name"] == "My Custom Fork"
    assert fork_custom_data["author"] == "Forker Bob"
    assert fork_custom_data["parent_template_id"] == parent_id
    assert fork_custom_data["is_public"] is False
