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


@pytest.mark.asyncio(loop_scope="session")
async def test_guide_infers_sashimi_rice_when_vlm_returns_ingredients_only(monkeypatch):
    async def fake_analyze_food(_image_data, _prompt=None):
        return {
            "ingredients": [
                {"name": "三文鱼刺身", "amount": "4片"},
                {"name": "金枪鱼刺身", "amount": "3片"},
                {"name": "甜虾", "amount": "2只"},
                {"name": "米饭", "amount": "1碗"},
                {"name": "海苔", "amount": "少量"},
            ],
            "portion_estimation": {"total_weight": 520},
        }

    async def fake_enrich(dish_name, base):
        assert "刺身" in dish_name
        assert "米饭" in dish_name or "海鲜" in dish_name
        return {
            "cuisine": "日式料理",
            "category": "主食",
            "history": "刺身饭常见于日式海鲜丼，把多种生食海鲜铺在醋饭或米饭上。",
            "features": "海鲜鲜甜，米饭承托油脂与鲜味。",
            "best_eat": "蘸少量酱油和芥末，先吃清淡鱼类再吃油脂更足的鱼类。",
            "estimated_calories": 620,
            "difficulty": "中等",
        }

    monkeypatch.setattr(food_guide, "analyze_food", fake_analyze_food)
    monkeypatch.setattr(food_guide, "_llm_enrich_guide", fake_enrich)

    result = await food_guide.guide("data:image/jpeg;base64:sashimi")

    assert result["status"] == "ok"
    assert "刺身" in result["dish_name"]
    assert result["cuisine"] == "日式料理"
    assert result["history"]
    assert result["ingredients"][0]["name"] == "三文鱼刺身"


@pytest.mark.asyncio(loop_scope="session")
async def test_guide_uses_stable_knowledge_for_sashimi_platter(monkeypatch):
    async def fake_analyze_food(_image_data, _prompt=None):
        return {
            "ingredients": [
                {"name": "三文鱼", "amount": "100克"},
                {"name": "金枪鱼", "amount": "100克"},
                {"name": "北极贝", "amount": "50克"},
                {"name": "甜虾", "amount": "8只"},
            ],
        }

    async def should_not_enrich(_dish_name, _base):
        raise AssertionError("刺身类 demo 应优先走稳定知识库，避免 LLM 讲解漂移")

    monkeypatch.setattr(food_guide, "analyze_food", fake_analyze_food)
    monkeypatch.setattr(food_guide, "_llm_enrich_guide", should_not_enrich)

    result = await food_guide.guide("data:image/jpeg;base64:sashimi_platter")

    assert result["status"] == "ok"
    assert result["dish_name"] == "刺身拼盘"
    assert result["cuisine"] == "日式料理"
    assert result["category"] == "海鲜"
    assert "竹签" not in result["history"]
    assert "新鲜度" in result["history"] or "生食海鲜" in result["history"]
    assert result["estimated_calories"] > 0
    assert result["difficulty"]
