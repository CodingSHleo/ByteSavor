import pytest

from app.services import quality


@pytest.mark.asyncio(loop_scope="session")
async def test_quality_does_not_use_unobserved_watermelon_sound_or_weight(monkeypatch):
    async def fake_analyze_food(_image_data):
        return {
            "ingredients": [{
                "name": "西瓜",
                "confidence": 0.96,
                "freshness": "high",
                "state": "新鲜",
                "features": "瓜皮颜色鲜亮，条纹清晰，表面未见裂口、软斑或霉点",
            }],
            "portion_estimation": {},
        }

    monkeypatch.setattr(quality, "analyze_food", fake_analyze_food)

    result = await quality.assess("data:image/jpeg;base64,test")

    assert result["status"] == "ok"
    text = str(result["items"][0])
    assert "拍打" not in text
    assert "声音" not in text
    assert "同等大小较重" not in text
    assert "重量" not in text
    assert "纹路清晰" in text
