# 修改文档 01：新增 Hard Evaluator + events 增加 phase/termination_reason

## 修改日期

2026-06-19

## 修改目标

对应方案文档 Section 3.3（状态语义增强）、Section 3.4（三层裁判体系 L1 Hard Evaluator）、Section 4 P1.1/P1.2。

## 文件变更

### 1. 新增 `app/agent/evaluator.py`

**原代码**：不存在此文件。

**新增内容**：
- `EvaluationResult` dataclass：包含 `verdict`（PASS/PARTIAL/CONFLICT/FAIL）、`issues`、`suggestions`
- `evaluate_hard(state)` 函数，执行以下硬规则检查：
  1. 推荐工具完成但列表为空 → FAIL
  2. 推荐完全不使用用户输入食材 → FAIL
  3. 核心食材覆盖率低于 50% → CONFLICT
  4. 库存缺失超过 5 项 → PARTIAL
  5. 存在工具错误 → PARTIAL
- `_count_core_ingredient_coverage()` 辅助函数
- `_worse()` 优先级合并辅助函数

### 2. 修改 `app/agent/langgraph_runtime.py`

**原有架构**（修改前）：
```
START → planner → [tool → planner 循环] / ask_user / final
```

**新增 evaluator 节点后**（修改后）：
```
START → planner → [tool → planner 循环] / ask_user / evaluator → final
```

具体变更：

1. **新增 `_evaluator_node`**（第 169-188 行）：
   - 执行 `evaluate_hard()` 生成 evaluation 事件
   - evaluation events 包含 verdict/issues/suggestions
   - FAIL 时将 issues 写入 errors

2. **events 增加 `phase` 字段**：
   - plan 事件 → `phase: "ROUTING"`
   - tool_start 事件 → `phase: "EXECUTING"`
   - tool_result 事件 → `phase: "EXECUTING"`
   - evaluation 事件 → `phase: "EVALUATING"`（新事件类型）
   - ask_user 事件 → `phase: "CLARIFYING"`
   - final 事件 → `phase: "FINISHED"`

3. **events 增加 `retry_count` 字段**（tool_result 事件，默认 0）

4. **GraphState 增加 `termination_reason` 字段**（第 17 行）

5. **返回值增加 `termination_reason`**（第 94 行）：
   - GOAL_ACHIEVED：正常完成
   - TOOL_ERROR：工具执行出错
   - MAX_STEPS：超过最大步数
   - NEEDS_INPUT：需要用户补充信息

6. **路由调整**：finish/max_steps 不再直接到 final，改为先进入 evaluator 再进 final

### 3. 影响 `app/routers/agent.py` 中的 `_events_to_stages`

stages 现在可以从 events 中读取 `phase` 和 `retry_count`（已有字段）。
