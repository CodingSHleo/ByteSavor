# 修改文档 02：推荐引擎 - 新增推荐理由码 + 核心食材覆盖

## 修改日期

2026-06-19

## 文件变更

### 1. 修改 `app/services/decision.py`

**修改位置**：第 108-119 行 `REASON_TEMPLATES` 字典

**修改前**：
```python
REASON_TEMPLATES = {
    "ING_MATCH": "已有食材: {ingredient}",
    "TASTE_MATCH": "口味匹配: {taste}",
    ...
    "PREF_MATCH": "符合偏好: {pref}",
    ...
}
```

**修改后**：新增两个推荐理由码：
```python
REASON_TEMPLATES = {
    ...
    "MEMORY_MATCH": "基于历史偏好推荐",
    "INVENTORY_MATCH": "库存可做: {item}",
    ...
}
```

**说明**：
- `MEMORY_MATCH`：标记基于用户长期偏好记忆（PreferenceMemory）的推荐
- `INVENTORY_MATCH`：标记推荐菜谱的食材在用户当前库存中已有
- 这两个标记在后续 P1 中由推荐服务实际使用，当前先预留模板

### 2. 已有保护（来自 01-Hard-Evaluator）

`app/agent/evaluator.py` 中的 `evaluate_hard()` 已实现：
- 核心食材覆盖率 < 50% → CONFLICT
- 核心食材覆盖率 = 0% → FAIL
- 推荐结果将通过 evaluator 节点在每次请求中自动检查
