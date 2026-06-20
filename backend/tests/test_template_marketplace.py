import pytest


@pytest.mark.asyncio
async def test_marketplace_only_returns_public_templates(async_client):
    # 1. Create a private template
    private_payload = {
        "name": "Secret Template",
        "tasks_schema": [{"name": "Step 1", "description": "Desc 1", "agent_name": "coder"}],
        "is_public": False
    }
    response = await async_client.post("/api/templates/", json=private_payload)
    assert response.status_code == 200
    private_id = response.json()["id"]

    # 2. Create a public template
    public_payload = {
        "name": "Shared Template",
        "tasks_schema": [{"name": "Step 1", "description": "Desc 1", "agent_name": "coder"}],
        "is_public": True
    }
    response = await async_client.post("/api/templates/", json=public_payload)
    assert response.status_code == 200
    public_id = response.json()["id"]

    # 3. Fetch marketplace (v1)
    market_resp = await async_client.get("/api/v1/templates/marketplace")
    assert market_resp.status_code == 200
    market_data = market_resp.json()
    
    # Assert public is in list, private is not
    ids = [t["id"] for t in market_data]
    assert public_id in ids
    assert private_id not in ids


@pytest.mark.asyncio
async def test_publish_template_marketplace(async_client):
    # 1. Create private template
    payload = {
        "name": "Draft Template",
        "tasks_schema": [{"name": "Step 1", "description": "Desc 1", "agent_name": "coder"}],
        "is_public": False
    }
    response = await async_client.post("/api/templates/", json=payload)
    assert response.status_code == 200
    template_id = response.json()["id"]

    # 2. Publish it with tags
    publish_payload = {
        "tags": ["published", "v10"]
    }
    publish_resp = await async_client.post(f"/api/v1/templates/{template_id}/publish", json=publish_payload)
    assert publish_resp.status_code == 200
    publish_data = publish_resp.json()
    assert publish_data["is_public"] is True
    assert publish_data["tags"] == ["published", "v10"]

    # 3. Check it is now in marketplace
    market_resp = await async_client.get("/api/templates/marketplace")
    assert market_resp.status_code == 200
    ids = [t["id"] for t in market_resp.json()]
    assert template_id in ids


@pytest.mark.asyncio
async def test_use_template_increments_count(async_client):
    # 1. Create a template
    payload = {
        "name": "Reusable Template",
        "tasks_schema": [{"name": "Step 1", "description": "Desc 1", "agent_name": "coder"}]
    }
    response = await async_client.post("/api/templates/", json=payload)
    assert response.status_code == 200
    template_id = response.json()["id"]
    assert response.json()["usage_count"] == 0

    # 2. Call use (v1)
    use_resp1 = await async_client.post(f"/api/v1/templates/{template_id}/use")
    assert use_resp1.status_code == 200
    assert use_resp1.json()["usage_count"] == 1

    # 3. Call use (v0)
    use_resp2 = await async_client.post(f"/api/templates/{template_id}/use")
    assert use_resp2.status_code == 200
    assert use_resp2.json()["usage_count"] == 2
