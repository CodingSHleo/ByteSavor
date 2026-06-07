import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_sense_does_not_return_mock_when_vlm_unavailable(client, monkeypatch):
    async def unavailable(_image_url):
        return None

    monkeypatch.setattr("app.routers.sense.vlm.analyze_food", unavailable)

    resp = await client.post("/v1/sense/analyze", json={
        "task_id": "task_test",
        "image_url": "https://example.com/food.jpg",
        "context": {"scene": "kitchen"},
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "VLM_UNAVAILABLE"
    assert "西兰花" not in str(data)
    assert "牛肉" not in str(data)
