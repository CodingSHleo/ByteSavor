# 修改文档 12：识别结果营养计量

## 修改日期
2026-06-20

## 文件变更

### 1. 新增 `app/services/nutrition_calculator.py`
- `FOOD_NUTRITION` 字典：50+ 常见食物的每 100g 营养素（热量/蛋白/碳/脂/纤维）
- `get_nutrition(name)`：按食材名查营养素，支持模糊匹配
- `calculate_per_ingredient(ingredient)`：单食材按 weight_estimate 计算营养素
- `calculate_total(ingredients)`：批量计算总营养
- `calculate_daily_gap(total, targets)`：计算摄入后今日剩余缺口

### 2. 修改 `app/services/vlm/__init__.py`
VLM 后处理新增营养挂载：
```python
"nutrition": {
    "per_item": [...],   # 每个食材的营养素
    "total": {...},      # 总热量/蛋白/碳/脂/纤维
    "has_unknown": false # 是否含未知食材
}
```

### 3. 新增 `tests/test_nutrition_calculator.py` — 11 个测试
