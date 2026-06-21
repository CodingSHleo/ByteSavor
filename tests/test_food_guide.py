import pytest

from app.services import food_guide


@pytest.mark.asyncio(loop_scope="session")
async def test_guide_uses_llm_when_vlm_only_identifies_dish(monkeypatch):
    async def fake_analyze_food(_image_data, _prompt=None):
        return {
            "dish_name": "豉汁蒸排骨",
            "cuisine": "粤菜",
            "category": "荤菜",
            "ingredients": [{"name": "排骨", "amount": "300g"}],
            "estimated_calories": 420,
            "difficulty": "中等",
        }

    async def fake_enrich(dish_name, base):
        assert dish_name == "豉汁蒸排骨"
        assert base["cuisine"] == "粤菜"
        return {
            "history": "豉汁蒸排骨是广式早茶常见点心，强调豆豉香气与排骨嫩度。",
            "features": "豆豉咸香、蒜香明显，蒸制保留肉汁。",
            "best_eat": "趁热配白粥或米饭，先吃带汁排骨。",
        }

    monkeypatch.setattr(food_guide, "analyze_food", fake_analyze_food)
    monkeypatch.setattr(food_guide, "_llm_enrich_guide", fake_enrich)

    result = await food_guide.guide("data:image/jpeg;base64,test")

    assert result["status"] == "ok"
    assert result["dish_name"] == "豉汁蒸排骨"
    assert result["history"]
    assert result["features"]
    assert result["best_eat"]
    assert result["from_llm"] is True
