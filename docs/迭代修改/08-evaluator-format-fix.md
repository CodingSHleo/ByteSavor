# 修改文档 08：evaluator 数据格式修正 + 补充缺失规则

## 修改日期

2026-06-19

## 修改原因

对手册 Section 6 的精确规范进行调整：
- issues 格式从 `list[str]` 改为 `list[{code, message, tool?}]`
- 补充 LOW_CONFIDENCE_INGREDIENT 规则（confidence < 0.5）
- 补充 NEEDS_USER_CONFIRMATION 规则（硬规则无法判断的软性判断）
- evaluation event 增加 `tool` 字段

## 文件变更

### 1. 重写 `app/agent/evaluator.py`

**issues 格式变更**：
```python
# 修改前
issues: list[str] = ["推荐工具执行完成但未返回任何菜谱"]

# 修改后
issues: list[dict] = [
    {"code": "NO_RECIPE", "message": "推荐工具执行完成但未返回任何菜谱", "tool": "decision"}
]
```

**新增规则**：

| 规则 | 条件 | verdict | issue code |
|------|------|---------|------------|
| 推荐为空 | decision 完成但 recipes=[] | FAIL | NO_RECIPE |
| 核心食材未覆盖 | 覆盖率 0% | FAIL | CORE_INGREDIENT_MISSED |
| 核心食材不足 | 覆盖率 < 50% | CONFLICT | CORE_INGREDIENT_MISSED |
| 低置信识别 | sense 结果有 confidence < 0.5 | PARTIAL | LOW_CONFIDENCE_INGREDIENT |
| 工具异常 | errors 非空（MAX_STEPS 除外） | FAIL | TOOL_ERROR |
| 需用户确认 | 有推荐结果且无硬错误 | PARTIAL | NEEDS_USER_CONFIRMATION |

### 2. 修改 `app/agent/state.py`

新增字段：
```python
memory_used: list[dict[str, Any]]  # 本次参考的记忆摘要
sense_result: dict | None          # sense 工具的原始返回（含置信度）
```

### 3. 修改 `app/agent/runtime.py`

`_merge_tool_output()` 中 sense 分支新增：
```python
state["sense_result"] = output  # 保存完整 VLM 结果供 evaluator 检查置信度
```

### 4. 修改 `app/agent/langgraph_runtime.py`

`_evaluator_node()` 中 evaluation event 新增 `tool` 字段，error 使用 issue.code 而非固定 "EVAL_FAIL"。
