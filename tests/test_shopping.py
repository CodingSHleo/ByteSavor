from app.services.shopping import _parse, _can_merge, _fmt_display


def test_parse_amount_g():
    q = _parse("300g")
    assert q["value"] == 300
    assert q["unit"] == "g"
    assert q["display"] == "300g"


def test_parse_amount_vague():
    q = _parse("少许")
    assert q["value"] is None
    assert q["unit"] == "少许"


def test_parse_amount_empty():
    q = _parse("")
    assert q["value"] is None


def test_can_merge_same_unit():
    assert _can_merge({"unit": "g"}, {"unit": "g"}) is True


def test_cannot_merge_different_unit():
    assert _can_merge({"unit": "g"}, {"unit": "个"}) is False


def test_fmt_display_int():
    assert _fmt_display(3, "g") == "3g"
    assert _fmt_display(700.0, "g") == "700g"


def test_fmt_display_none():
    assert _fmt_display(None, "少许") == "少许"
