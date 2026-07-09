"""
食材同义词标准化映射 + 置信度分级。
用于 VLM 识别后处理：统一食材名称、低置信标记。
"""
from __future__ import annotations

# 同义词映射：key 为别名，value 为标准名
SYNONYM_MAP: dict[str, str] = {
    # 茄类
    "番茄": "西红柿",
    "蕃茄": "西红柿",
    "洋柿子": "西红柿",
    # 薯类
    "土豆": "马铃薯",
    "洋芋": "马铃薯",
    "山药蛋": "马铃薯",
    # 蔬菜
    "青菜": "小白菜",
    "小青菜": "小白菜",
    "飘儿白": "小白菜",
    "圆白菜": "卷心菜",
    "包菜": "卷心菜",
    "甘蓝": "卷心菜",
    "苞菜": "卷心菜",
    "空心菜": "蕹菜",
    "藤藤菜": "蕹菜",
    "韭菜黄": "韭黄",
    "韭黄": "韭黄",
    # 豆类
    "四季豆": "菜豆",
    "芸豆": "菜豆",
    "豇豆": "长豆角",
    "豆角": "长豆角",
    # 肉类
    "猪瘦肉": "猪肉",
    "猪里脊": "猪肉",
    "五花肉": "猪肉",
    "牛腩": "牛肉",
    "牛腱": "牛肉",
    "牛柳": "牛肉",
    "鸡胸": "鸡肉",
    "鸡胸肉": "鸡肉",
    "鸡腿肉": "鸡肉",
    "鸡翅": "鸡肉",
    # 蛋奶
    "鸡子": "鸡蛋",
    "土鸡蛋": "鸡蛋",
    # 主食
    "大米": "米饭",
    "白米饭": "米饭",
    "面": "面条",
    "拉面": "面条",
    "挂面": "面条",
    # 调料
    "葱": "大葱",
    "小葱": "香葱",
    "姜": "生姜",
    "蒜": "大蒜",
    "蒜头": "大蒜",
    "辣椒": "红辣椒",
    "青椒": "青辣椒",
    "香菜": "芫荽",
    # 水产
    "大虾": "虾",
    "对虾": "虾",
    "基围虾": "虾",
}

# 置信度阈值
HIGH_CONFIDENCE_THRESHOLD = 0.7


def normalize_ingredient_name(name: str) -> str:
    """将食材名标准化为统一名称。"""
    if not name:
        return name
    key = name.strip()
    std = SYNONYM_MAP.get(key)
    return std if std else key


def normalize_ingredients(ingredients: list[dict]) -> list[dict]:
    """对 VLM 识别结果进行后处理：
    1. 标准化食材名
    2. 标记低置信度（confidence < 0.7 → needs_confirm=True）
    3. 同名合并（低置信 dup 合并到高置信）
    """
    seen: dict[str, dict] = {}
    for item in ingredients:
        if not isinstance(item, dict):
            continue
        name = normalize_ingredient_name(item.get("name", ""))
        confidence = item.get("confidence", 0.5)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.5
        weight = item.get("weight_estimate", 0)
        if isinstance(weight, str):
            try:
                weight = float(weight)
            except (ValueError, TypeError):
                weight = 0

        if name in seen:
            existing = seen[name]
            existing["confidence"] = max(existing.get("confidence", 0), confidence)
            existing["weight_estimate"] = existing.get("weight_estimate", 0) + weight
            existing["_merged_from"] = existing.get("_merged_from", []) + [item.get("name", "")]
        else:
            item["name"] = name
            item["_normalized"] = True
            item["needs_confirm"] = confidence < HIGH_CONFIDENCE_THRESHOLD
            item["confidence"] = confidence
            item["weight_estimate"] = weight
            seen[name] = item

    return list(seen.values())


def get_confidence_label(confidence: float) -> str:
    """返回置信度标签。"""
    if confidence >= 0.9:
        return "高置信"
    elif confidence >= HIGH_CONFIDENCE_THRESHOLD:
        return "较高置信"
    else:
        return "待确认"
