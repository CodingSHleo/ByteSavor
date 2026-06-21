# 43-v6-LLMPlanner 与 Judge 修复记录

日期：2026-06-21

## 修复范围

- 新增 descriptor 候选动作生成：`build_candidate_actions(state, ToolRegistry.describe())`。
- 新增受控 LLM Planner：仅允许从候选工具中选择下一步。
- 新增 Soft LLM Judge：仅产出 `soft_judge` 评审事件。
- Runtime 与 LangGraph 路径同步 `planner_source`、`candidate_tools`、`llm_reason`。
- 新增默认关闭配置：`agent_llm_planner_enabled=False`、`agent_llm_judge_enabled=False`。

## LLM Planner 什么时候启用

只有同时满足以下条件才会尝试 LLM planner：

1. `settings.agent_llm_planner_enabled=True`
2. `settings.llm_api_key` 非空
3. `settings.llm_api_url` 非空
4. descriptor 候选动作非空，且工具依赖的关键输入已存在

默认配置保持安全关闭。无 key 或无 url 时直接返回 `None`，不会联网，也不会报错。

## LLM Planner 失败如何回退

LLM planner 失败时统一回退到现有规则 planner：

- 候选动作为空：`planner_source="rule"`
- LLM 未启用：`planner_source="rule"`
- LLM 未配置、超时、HTTP 失败、JSON 解析失败：`planner_source="rule_fallback"`
- LLM 选择了候选外工具：记录 warning，并 `planner_source="rule_fallback"`

`ask_user` 和 `finish` 仍由规则 planner 兜底生成。

## 如何防止 DeepSeek 编造工具或菜谱

- 候选动作只来自 `ToolRegistry.describe()`，不会手写开放工具列表。
- 对图文混合请求增加“感知优先”约束：如果用户要求识别图片并推荐，候选动作第一步只暴露 `sense`；如果是营养/品质/向导图片任务，则第一步只暴露对应 perception skill。LLM 不能跳过感知直接选择 `decision`。
- Planner prompt 明确禁止发明工具、禁止生成 `recipe_id`。
- `choose_action_with_llm()` 校验 `selected_tool` 必须存在于候选工具。
- `select_next_action()` 在合并层再次校验候选工具，防止内部替换或异常结构越权。
- LLM planner 只返回工具选择，不写入 `state["recipes"]`。
- 菜谱仍只能由 `decision` 工具通过 `decision.py` 数据库召回写入，planner/judge/rerank 都不能新增 DB 候选外 `recipe_id`。

## LLM Judge 为什么不阻断主流程

Soft Judge 在硬规则 `evaluation` 之后、`final` 之前追加 `soft_judge` event。

它只评价当前结果：

- 不改变 `status`
- 不改变 `termination_reason`
- 不向 `state["errors"]` 写入硬错误
- 不调用外部 DB
- 异常时只追加 `verdict="SKIPPED"` 的软事件，主流程继续

无配置或开关关闭时不产出 judge event。

## 测试命令和结果

已运行：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_llm_planner.py tests/test_agent_judge.py tests/test_agent_runtime.py tests/test_agent_loop_engineering.py
```

结果：`24 passed in 0.05s`

主 agent 复审后新增两条感知优先回归：

- `test_image_identify_recommend_candidates_force_sense_before_decision`
- `test_llm_cannot_skip_required_sense_for_image_recommendation`

复审后重新运行：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_llm_planner.py -vv
```

结果：`8 passed in 0.01s`

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_agent_judge.py tests/test_agent.py tests/test_agent_runtime.py
```

结果：`18 passed in 0.05s`

```bash
JWT_SECRET=test-review-secret venv/bin/python evals/runner.py --quick --mode mock
```

结果：`Score: 72/72 (100%)`

```bash
node scripts/verify_frontend_regressions.mjs
```

结果：通过，输出 `frontend regressions ok`。存在既有 Node `MODULE_TYPELESS_PACKAGE_JSON` warning。
