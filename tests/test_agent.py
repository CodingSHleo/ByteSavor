from app.services.agent import _parse_intent_regex


def test_parse_intent_fat_loss():
    intent = _parse_intent_regex("家里有牛肉和南瓜，30分钟做个减脂餐")
    assert intent["goal"] == "fat_loss"
    assert intent["time_limit"] == 30
    assert "牛肉" in intent["ingredients"]
    assert "南瓜" in intent["ingredients"]


def test_parse_intent_muscle_gain():
    intent = _parse_intent_regex("增肌餐，15分钟，有鸡胸肉和鸡蛋")
    assert intent["goal"] == "muscle_gain"
    assert intent["time_limit"] == 15


def test_parse_intent_spicy():
    intent = _parse_intent_regex("想吃辣的")
    assert intent["taste"] == "spicy"


def test_parse_intent_default():
    intent = _parse_intent_regex("随便吃点东西")
    assert intent["goal"] == "balanced"
    assert intent["time_limit"] == 30
