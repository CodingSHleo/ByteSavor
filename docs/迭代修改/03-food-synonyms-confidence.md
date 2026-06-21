# 修改文档 03：识别后处理 - 同义词标准化 + 低置信分级

## 修改日期

2026-06-19

## 文件变更

### 1. 新增 `app/services/food_synonyms.py`

**原代码**：不存在此文件。

**新增内容**：
- `SYNONYM_MAP`：60+ 组食材同义词映射（番茄→西红柿、土豆→马铃薯、青菜→小白菜 等），涵盖茄类、薯类、蔬菜、豆类、肉类、蛋奶、主食、调料、水产
- `normalize_ingredient_name(name)`：单名标准化
- `normalize_ingredients(ingredients)`：VLM 结果后处理，包含：
  1. 标准化食材名
  2. 低置信标记（confidence < 0.7 → `needs_confirm: true`）
  3. 同名合并（识别重复时合并 confidence 和 weight）
- `get_confidence_label(confidence)`：返回置信度标签（高置信/较高置信/待确认）
- `HIGH_CONFIDENCE_THRESHOLD = 0.7` 置信度阈值

### 2. 修改 `app/services/vlm/__init__.py`

**修改前**（第 8-9 行）：
```python
async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    return await _provider.analyze_food(image_url, prompt)
```

**修改后**：在 `analyze_food()` 中加入后处理管线：
```python
async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    raw = await _provider.analyze_food(image_url, prompt)
    if raw is None:
        return None
    # 后处理：同义词标准化 + 低置信标记 + 同名合并
    normalized = normalize_ingredients(raw.get("ingredients", []))
    return {
        "ingredients": normalized,
        "portion_estimation": raw.get("portion_estimation", {}),
        "confidence_summary": {
            "total": len(normalized),
            "high_confidence": high_conf_count,
            "needs_confirm": low_conf_count,
        },
    }
```

**效果**：
- VLM 返回的 ingredients 自动标准化名称
- 低置信食材标记 `needs_confirm: true`，前端可据此展示"待确认"
- 同名食材自动合并，解决"一个西瓜识别成多个物体"的问题
- 新增 `confidence_summary` 汇总置信度分布
