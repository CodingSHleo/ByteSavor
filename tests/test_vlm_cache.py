import pytest


RAW_VLM_RESULT = {
    "ingredients": [
        {
            "name": "番茄",
            "confidence": 0.95,
            "freshness": "high",
            "state": "新鲜",
            "features": "红色",
            "weight_estimate": 120,
        }
    ],
    "portion_estimation": {"total_weight": 120},
}


@pytest.fixture
def memory_vlm_cache(monkeypatch):
    store = {}

    async def fake_get(key):
        value = store.get(key)
        return dict(value) if value is not None else None

    async def fake_set(key, value, ttl):
        store[key] = dict(value)

    monkeypatch.setattr("app.services.vlm.cache_get", fake_get)
    monkeypatch.setattr("app.services.vlm.cache_set", fake_set)
    return store


@pytest.mark.asyncio(loop_scope="session")
async def test_vlm_cache_miss_then_hit_returns_observability(memory_vlm_cache, monkeypatch):
    from app.services import vlm

    calls = 0

    async def fake_analyze_food(_image_url, _prompt):
        nonlocal calls
        calls += 1
        return RAW_VLM_RESULT

    monkeypatch.setattr(vlm._provider, "analyze_food", fake_analyze_food)
    monkeypatch.setattr(vlm.settings, "vlm_model", "model-a")
    monkeypatch.setattr(vlm, "FOOD_ANALYSIS_PROMPT_VERSION", "prompt-a")

    first = await vlm.analyze_food("data:image/jpeg;base64,abc")
    second = await vlm.analyze_food("data:image/jpeg;base64,abc")

    assert calls == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert first["cache_key"] == second["cache_key"]
    assert first["image_fingerprint"] == second["image_fingerprint"]
    assert "abc" not in first["cache_key"]
    assert "abc" not in first["image_fingerprint"]
    for result in (first, second):
        assert isinstance(result["latency_ms"], int)
        assert result["latency_ms"] >= 0
        assert result["model"] == "model-a"
        assert result["prompt_version"] == "prompt-a"
        assert result["cache_key"].startswith("bs:")
        assert len(result["ingredients"]) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_vlm_cache_key_changes_with_model_or_prompt_version(memory_vlm_cache, monkeypatch):
    from app.services import vlm

    async def fake_analyze_food(_image_url, _prompt):
        return RAW_VLM_RESULT

    monkeypatch.setattr(vlm._provider, "analyze_food", fake_analyze_food)

    monkeypatch.setattr(vlm.settings, "vlm_model", "model-a")
    monkeypatch.setattr(vlm, "FOOD_ANALYSIS_PROMPT_VERSION", "prompt-a")
    base = await vlm.analyze_food("https://example.com/food.jpg")

    monkeypatch.setattr(vlm.settings, "vlm_model", "model-b")
    changed_model = await vlm.analyze_food("https://example.com/food.jpg")

    monkeypatch.setattr(vlm.settings, "vlm_model", "model-a")
    monkeypatch.setattr(vlm, "FOOD_ANALYSIS_PROMPT_VERSION", "prompt-b")
    changed_prompt = await vlm.analyze_food("https://example.com/food.jpg")

    assert base["cache_key"] != changed_model["cache_key"]
    assert base["cache_key"] != changed_prompt["cache_key"]
    assert changed_model["model"] == "model-b"
    assert changed_prompt["prompt_version"] == "prompt-b"
