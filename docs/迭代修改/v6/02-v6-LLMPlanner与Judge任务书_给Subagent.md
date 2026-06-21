# ByteSavor v6-02：LLM Planner 与 Judge 任务书（给 Subagent）

日期：2026-06-21  
执行对象：subagent  
审查人：主 agent / 项目负责人  
前置依赖：必须先完成 v6-01 Skill 工业化底座  

---

## 0. 本任务目标

让 DeepSeek 成为 ByteSavor Agent 的“受控推理层”，而不是绕过业务规则的自由生成器。

完成后必须能准确答辩：

> ByteSavor 的 LLM Planner 不直接创造工具、不直接生成数据库外菜谱。它只能在 SkillDescriptor 生成的候选动作中选择下一步；失败时回退规则 planner。LLM Judge 只做软性评审和解释，不阻断硬规则主流程。

---

## 1. 当前问题

当前系统中 DeepSeek 使用位置分散：

| 位置 | 当前用途 | 问题 |
|---|---|---|
| `app/services/assistant.py` | AI 助手回复 | 不等于主 Agent planner |
| `app/services/llm_rerank.py` | 推荐候选重排 | 已有边界，但不是 planner |
| `app/services/llm_deepseek.py` | 意图解析 | 标注为大脑，但主链路 planner 仍是规则 |
| `app/agent/planner.py` | 主 planner | 关键词硬编码 |
| `app/agent/evaluator.py` | 硬规则评估 | 没有软性 Judge |

---

## 2. 严禁事项

1. 不允许 LLM 输出任意工具名，只能选择候选动作。
2. 不允许 LLM 直接生成数据库不存在的 recipe_id。
3. 不允许 LLM Judge 阻断主流程；阻断只由现有硬规则 Evaluator 决定。
4. 不允许把 LLM 未配置视为错误；未配置时必须回退规则 planner。
5. 不允许为追求“智能”破坏 `牛肉韭黄`、`韭黄炒蛋` 等用户实测修复。
6. 不允许把 mock eval 说成完整黑箱 eval。

---

## 3. 必改文件

| 文件 | 操作 | 要求 |
|---|---|---|
| `app/agent/planner.py` | 修改 | 增加 descriptor 候选动作生成 |
| `app/agent/llm_planner.py` | 新增 | DeepSeek 受控 planner |
| `app/agent/llm_judge.py` | 新增 | 软性评审 |
| `app/agent/runtime.py` | 修改 | 允许 planner event 展示 planner_source |
| `app/agent/langgraph_runtime.py` | 修改 | API 路径同步 planner_source / judge event |
| `app/core/config.py` | 可能修改 | 增加开关，默认安全关闭或自动降级 |
| `tests/test_llm_planner.py` | 新增 | 候选工具约束与 fallback |
| `tests/test_agent_judge.py` | 新增 | Judge 只产事件不阻断 |

---

## 4. 具体实现要求

### 4.1 Descriptor 候选动作生成

在 `app/agent/planner.py` 增加：

```python
def build_candidate_actions(state: AgentState, skill_descriptors: list[dict]) -> list[dict]:
    ...
```

候选动作格式：

```python
{
  "kind": "tool",
  "tool": "decision",
  "reason": "用户请求推荐菜谱，decision 可根据食材和偏好推荐",
  "requires_image": False,
  "category": "decision"
}
```

要求：

1. 候选动作来自 `ToolRegistry.describe()`，不是手写全量工具列表。
2. 根据 descriptor 的 `requires_image/requires_user/intent_keywords/input_fields` 做基础过滤。
3. 必须保留现有规则 planner 作为 fallback。
4. `ask_user` 和 `finish` 仍由规则 planner 兜底生成。

### 4.2 LLM Planner 只能选择候选动作

新增 `app/agent/llm_planner.py`。

接口建议：

```python
async def choose_action_with_llm(
    state: AgentState,
    candidates: list[dict],
) -> dict | None:
    ...
```

LLM 返回只允许：

```json
{"selected_tool": "decision", "reason": "用户要求用牛肉韭黄推荐菜谱"}
```

校验要求：

1. `selected_tool` 必须存在于 candidates。
2. JSON 解析失败返回 `None`。
3. LLM 超时返回 `None`。
4. LLM 选择了不存在工具返回 `None` 并记录 warning。
5. `settings.llm_api_key` 或 `settings.llm_api_url` 未配置时直接返回 `None`。

Planner 合并逻辑：

```text
候选动作为空 -> 规则 planner
LLM 成功选择候选 -> 用 LLM action, planner_source="llm"
LLM 失败/未配置/越权 -> 用规则 planner, planner_source="rule_fallback"
```

### 4.3 Planner 事件

`plan` event 增加：

```python
{
  "planner_source": "rule" | "llm" | "rule_fallback",
  "candidate_tools": ["sense", "decision"],
  "llm_reason": "...",
}
```

没有 LLM 时，`planner_source` 至少是 `"rule"`。

### 4.4 Soft LLM Judge

新增 `app/agent/llm_judge.py`。

接口建议：

```python
async def judge_agent_result(state: AgentState) -> dict | None:
    ...
```

输出：

```python
{
  "verdict": "PASS" | "WARN",
  "scores": {
    "instruction_following": 4.0,
    "ingredient_relevance": 4.5,
    "preference_alignment": 4.0,
    "actionability": 3.5
  },
  "issues": [...],
  "suggestions": [...]
}
```

要求：

1. Judge 只在 final 前后新增 `soft_judge` event。
2. Judge 不改变 `status`、`termination_reason`。
3. Judge 不调用外部 DB。
4. LLM 未配置时不产 Judge event，或产 `skipped` event，二选一但测试固定。
5. Prompt 必须明确：只能评价现有结果，不能新增菜谱。

### 4.5 配置开关

建议在 `app/core/config.py` 增加：

```python
agent_llm_planner_enabled: bool = False
agent_llm_judge_enabled: bool = False
```

默认 False，避免测试环境和演示环境因为无 key 不稳定。

---

## 5. 必须新增测试

### 5.1 Planner 候选约束

`tests/test_llm_planner.py`：

1. LLM 返回不存在工具名 -> fallback 到规则 planner。
2. LLM 返回候选工具 -> action 使用该工具。
3. 无 API key -> 不调用网络，走规则 planner。
4. 候选工具来自 registry descriptor。

### 5.2 Judge 不阻断

`tests/test_agent_judge.py`：

1. fake judge 返回 WARN，最终 API `status` 仍按硬规则决定。
2. `soft_judge` event 出现在 `evaluation` 与 `final` 附近。
3. judge 返回异常时不影响主流程，只记录事件或 warning。

### 5.3 不越权生成菜谱

必须增加测试：LLM rerank/planner/judge 都不能让最终结果出现 DB 候选之外的 `recipe_id`。

---

## 6. 验证命令

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_llm_planner.py \
  tests/test_agent_judge.py \
  tests/test_agent.py \
  tests/test_agent_runtime.py
```

推荐与偏好回归：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_decision.py \
  tests/test_decision_memory_matching.py \
  tests/test_feedback_memory.py
```

Eval mock：

```bash
JWT_SECRET=test-review-secret venv/bin/python evals/runner.py --quick --mode mock
```

前端快速回归：

```bash
node scripts/verify_frontend_regressions.mjs
```

---

## 7. 修复记录要求

完成后新增：

- `docs/迭代修改/43-v6-LLMPlanner与Judge修复记录.md`
- `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/43-v6-LLMPlanner与Judge修复记录.md`

必须写清：

1. LLM Planner 什么时候启用。
2. LLM Planner 失败如何回退。
3. LLM Judge 为什么不阻断主流程。
4. 如何防止 DeepSeek 编造菜谱或工具。
5. 测试命令和结果。

