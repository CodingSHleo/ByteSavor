import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_sense_success_returns_vlm_observability_fields(client, monkeypatch):
    async def analyzed(_image_url):
        return {
            "ingredients": [{"name": "番茄", "confidence": 0.95, "freshness": "high", "state": "新鲜"}],
            "cache_hit": False,
            "cache_key": "bs:testkey",
            "latency_ms": 12,
            "model": "model-a",
            "prompt_version": "food-analysis-v1",
            "image_fingerprint": "abc123hash",
        }

    monkeypatch.setattr("app.routers.sense.vlm.analyze_food", analyzed)

    resp = await client.post("/v1/sense/analyze", json={
        "task_id": "task_test",
        "image_url": "https://example.com/food.jpg",
        "context": {"scene": "kitchen"},
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["cache_hit"] is False
    assert data["cache_key"] == "bs:testkey"
    assert data["latency_ms"] == 12
    assert data["model"] == "model-a"
    assert data["prompt_version"] == "food-analysis-v1"
    assert data["image_fingerprint"] == "abc123hash"


@pytest.mark.asyncio(loop_scope="session")
async def test_sense_rejects_too_large_image(client, monkeypatch):
    async def should_not_call(_image_url):
        raise AssertionError("VLM should not be called for oversized images")

    monkeypatch.setattr("app.routers.sense.vlm.analyze_food", should_not_call)

    resp = await client.post("/v1/sense/analyze", json={
        "task_id": "task_large",
        "image_url": "x" * (8 * 1024 * 1024 + 1),
        "context": {"scene": "kitchen"},
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "IMAGE_TOO_LARGE"


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
