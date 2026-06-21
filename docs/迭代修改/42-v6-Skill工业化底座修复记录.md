# v6-01 Skill 工业化底座修复记录

日期：2026-06-21

## 修改文件清单

- `app/agent/skill_descriptor.py`
- `app/agent/tools.py`
- `app/agent/runtime.py`
- `app/agent/langgraph_runtime.py`
- `app/routers/agent.py`
- `tests/test_skill_registry.py`
- `tests/test_agent_loop_engineering.py`
- `tests/test_agent.py`
- `docs/迭代修改/42-v6-Skill工业化底座修复记录.md`
- `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/42-v6-Skill工业化底座修复记录.md`

## 修改点

### 1. SkillDescriptor 执行配置

修改前问题：
- `SkillDescriptor` 只描述输入输出和意图关键词，缺少执行超时、重试、错误降级和分类信息。

修改后逻辑：
- 增加 `timeout_ms`、`max_retries`、`retryable_errors`、`degrade_on_error`、`category`。
- 为 `sense`、`decision`、`task`、`nutrition`、`quality`、`guide`、`inventory`、`favorites`、`recipe_check` 配置默认执行参数。
- 增加 `to_dict()`，供 registry、planner 和前端统一消费 descriptor 元数据。

### 2. ToolRegistry 绑定 descriptor

修改前问题：
- `ToolRegistry.register(name, tool)` 可以注册任意名称，无法保证工具和 descriptor 一致。

修改后逻辑：
- 注册未知 skill 时抛出 `ValueError("Unknown skill descriptor: <name>")`。
- `get(name)` 保持旧兼容，仍返回可调用 tool。
- 新增 `descriptor(name)`、`describe()`、`has(name)`。
- `describe()` 返回已注册工具的纯 dict descriptor，包含前端和 planner 所需字段。

### 3. 统一 Skill 执行 wrapper

修改前问题：
- `AgentRuntime` 和 `LangGraphAgent` 各自手写工具执行、耗时统计和异常事件，错误码不稳定。

修改后逻辑：
- 新增 `SkillExecutionResult` 和 `execute_tool()`。
- 统一使用 `asyncio.wait_for(tool(state), timeout=descriptor.timeout_ms / 1000)`。
- 统一归一化错误码：`TimeoutError`、`VLM_NOT_CONFIGURED`、`VLM_UNAVAILABLE`、`ValueError` 消息和其他异常类名。
- 按 descriptor 的 `max_retries` 与 `retryable_errors` 执行最多一次 retry。

### 4. Runtime / LangGraph 事件统一

修改前问题：
- 两条 runtime 路径的 `tool_result` 字段不一致，API 实际走 LangGraph，容易漏改。

修改后逻辑：
- `AgentRuntime` 和 `LangGraphAgent` 都调用 `execute_tool()`。
- `plan` event 增加 `available_skills`。
- `tool_start` 和 `tool_result` event 增加稳定 `skill` 摘要。
- `tool_result` 稳定返回 `status`、`latency_ms`、`retry_count`、`error_code`、`summary`、`step`。

事件示例：

```json
{
  "type": "tool_result",
  "phase": "EXECUTING",
  "tool": "sense",
  "skill": {
    "name": "sense",
    "category": "perception",
    "timeout_ms": 12000
  },
  "status": "error",
  "latency_ms": 1,
  "retry_count": 0,
  "error_code": "VLM_NOT_CONFIGURED",
  "summary": {
    "ingredient_count": 0
  },
  "step": 0,
  "message": "VLM_NOT_CONFIGURED"
}
```

`plan` event 示例：

```json
{
  "type": "plan",
  "phase": "ROUTING",
  "tool": "decision",
  "reason": "根据食材和约束生成推荐",
  "available_skills": ["decision", "favorites", "guide", "inventory", "nutrition", "quality", "recipe_check", "sense", "task"],
  "step": 0
}
```

### 5. sense 始终注册

修改前问题：
- `settings.vlm_api_url` 为空时，`sense` 不注册；图片识别请求可能表现为工具不存在，而不是明确降级。

修改后逻辑：
- `sense` 始终注册。
- 无图片时抛 `ValueError("NO_IMAGE")`。
- 未配置 VLM 时抛 `RuntimeError("VLM_NOT_CONFIGURED")`。
- VLM 无结果时抛 `RuntimeError("VLM_UNAVAILABLE")`。
- wrapper 将这些错误转成稳定事件，API 返回 `status="degraded"`。

### 6. 主 agent 复审补丁：Skill 错误后停止继续规划

复审发现的问题：
- `LangGraphAgent` 在 `sense` 等 skill 失败后，会把失败工具加入 `completed_tools`，然后回到 planner。
- 对于“识别图片里的食材并推荐菜谱”这类请求，如果 VLM 未配置，旧逻辑可能先记录 `sense` 失败，再继续执行 `decision`，产生“感知失败但仍然推荐”的误导结果。

修改后逻辑：
- `plan_next_action()` 在 `state["errors"]` 非空时直接 `finish`。
- `AgentRuntime` 的错误路径也统一进入 `_finish_run()`，保证错误场景仍有 `evaluation` 与 `final` 事件。
- 新增回归测试 `test_langgraph_stops_after_skill_error_instead_of_continuing_to_decision`，确认 `sense` 失败后不会继续调用 `decision`。

## 测试命令和结果

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_skill_registry.py tests/test_agent_loop_engineering.py tests/test_agent.py tests/test_agent_runtime.py
```

结果：主 agent 复审后重新运行，`30 passed`（拆分验证为 `23 passed + 7 passed`）。

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_agent.py tests/test_agent_runtime.py tests/test_agent_evaluator.py tests/test_decision_memory_matching.py tests/test_feedback_memory.py tests/test_agent_memory_context.py
```

结果：`38 passed in 3.95s`

主 agent 复审后重新运行：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_agent.py tests/test_agent_runtime.py tests/test_agent_evaluator.py tests/test_decision_memory_matching.py tests/test_feedback_memory.py tests/test_agent_memory_context.py
```

结果：`38 passed in 3.49s`

用户实测相关回归：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_decision.py tests/test_community.py tests/test_favorites.py tests/test_community_recipe_flow.py
```

结果：`20 passed in 2.71s`

```bash
node scripts/verify_frontend_regressions.mjs
```

结果：通过，输出 `frontend regressions ok`。存在 Node `MODULE_TYPELESS_PACKAGE_JSON` warning，为既有模块类型提示。

```bash
cd bsapp
npm run build:h5
```

结果：通过，输出 `DONE  Build complete.`。存在 uni-app 新版本提示和 Sass deprecation warning。

主 agent 复审后重新运行：

```bash
cd bsapp
npm run build:h5
```

结果：通过，输出 `DONE  Build complete.`。仍有既有 uni-app 新版本提示和 Sass deprecation warning。

## 未完成项

- LLM Planner 不在本任务内，未实现。
- LLM Judge 不在本任务内，未实现。
- VL cache 不在本任务内，未修改。
- 前端展示不在本任务内，未改页面展示逻辑。
