# ByteSavor v6-01：Skill 工业化底座任务书（给 Subagent）

日期：2026-06-21  
执行对象：subagent  
审查人：主 agent / 项目负责人  
任务性质：Agent 底座工程化，不做业务 UI，不做 LLM Planner  

---

## 0. 本任务目标

把现有 Agent 的 Skill 从“函数注册表”升级成“可描述、可校验、可观测、可降级”的工业化执行单元。

完成后必须能准确答辩：

> ByteSavor 的每个 Skill 都不是随手注册的函数，而是带有 SkillDescriptor、输入输出契约、超时/重试、错误码、事件摘要和降级状态的受控执行单元。Planner 和前端时间线看到的是同一套 descriptor 元数据。

---

## 1. 当前问题

当前代码证据：

| 文件 | 当前状态 | 问题 |
|---|---|---|
| `app/agent/skill_descriptor.py` | 已定义 `SkillDescriptor` 和 `SKILL_DESCRIPTORS` | 主要是元数据，没有约束注册和执行 |
| `app/agent/tools.py` | `ToolRegistry.register(name, tool)` | 任意 name 都能注册，没有 descriptor 校验 |
| `app/agent/runtime.py` | runtime 手写工具执行事件 | 没有统一 wrapper，异常码不稳定 |
| `app/agent/langgraph_runtime.py` | API 实际主要走 LangGraph | 也手写工具执行逻辑，容易与 runtime 分叉 |
| `app/routers/agent.py` | `sense` 只有 `settings.vlm_api_url` 存在才注册 | 没配置 VLM 时 planner 可能选到不存在工具，工业化边界不清楚 |

---

## 2. 严禁事项

1. 不要实现 LLM Planner。那是 v6-02。
2. 不要接 DeepSeek 新调用。那是 v6-02。
3. 不要改推荐排序业务规则，尤其不能破坏 `牛肉韭黄` 的修复。
4. 不要新增本地 CNN/ONNX/VLM 降级模型。
5. 不要引入 WebSocket/SSE。
6. 不要把运行时硬规则 Evaluator 改成 LLM Judge。
7. 不要只改 `AgentRuntime`，必须同步 `LangGraphAgent`，因为 `/v1/agent/execute` 走的是 `LangGraphAgent`。
8. 不要写“全部完成”但不给测试命令和结果。

---

## 3. 必改文件

| 文件 | 操作 | 要求 |
|---|---|---|
| `app/agent/skill_descriptor.py` | 修改 | `SkillDescriptor` 增加执行配置字段 |
| `app/agent/tools.py` | 重构 | ToolRegistry 必须绑定 descriptor，并提供 describe/list |
| `app/agent/runtime.py` | 修改 | 使用统一 skill executor，事件带 descriptor/latency/error_code |
| `app/agent/langgraph_runtime.py` | 修改 | 与 runtime 保持同样事件结构 |
| `app/routers/agent.py` | 修改 | `sense` 始终注册，未配置时返回明确错误 |
| `tests/test_skill_registry.py` | 新增 | 覆盖 registry 契约 |
| `tests/test_agent_loop_engineering.py` | 修改或新增 | 覆盖 skill 事件、错误、sense 未配置 |

如果已有同名测试文件，追加测试，不要删除旧测试。

---

## 4. 具体实现要求

### 4.1 SkillDescriptor 增加执行配置

在 `SkillDescriptor` 中增加字段：

```python
timeout_ms: int = 8000
max_retries: int = 0
retryable_errors: list[str] = field(default_factory=list)
degrade_on_error: bool = True
category: str = "domain"
```

字段含义：

| 字段 | 用途 |
|---|---|
| `timeout_ms` | 单个 skill 最大执行时间，先用于事件和 `asyncio.wait_for` |
| `max_retries` | 当前允许 0 或 1，默认 0 |
| `retryable_errors` | 错误码在该列表内才允许 retry |
| `degrade_on_error` | 出错后是否降级返回，而不是崩掉整个 API |
| `category` | `perception / decision / task / memory / evaluation / domain` |

建议默认配置：

| skill | category | timeout_ms | max_retries | retryable_errors |
|---|---|---:|---:|---|
| `sense` | `perception` | 12000 | 1 | `["VLM_UNAVAILABLE", "TimeoutError"]` |
| `decision` | `decision` | 10000 | 0 | `[]` |
| `task` | `task` | 6000 | 0 | `[]` |
| `nutrition` | `perception` | 12000 | 1 | `["VLM_UNAVAILABLE", "TimeoutError"]` |
| `quality` | `perception` | 12000 | 1 | `["VLM_UNAVAILABLE", "TimeoutError"]` |
| `guide` | `perception` | 12000 | 1 | `["VLM_UNAVAILABLE", "TimeoutError"]` |
| `inventory` | `memory` | 5000 | 0 | `[]` |
| `favorites` | `memory` | 5000 | 0 | `[]` |
| `recipe_check` | `decision` | 7000 | 0 | `[]` |

### 4.2 ToolRegistry 绑定 descriptor

`ToolRegistry` 必须做到：

1. `register(name, tool)` 时，`name` 必须存在于 `SKILL_DESCRIPTORS`。
2. 注册未知工具时抛 `ValueError("Unknown skill descriptor: <name>")`。
3. `get(name)` 仍返回可调用 tool，保持旧代码兼容。
4. 新增：

```python
def descriptor(self, name: str) -> SkillDescriptor: ...
def describe(self) -> list[dict]: ...
def has(self, name: str) -> bool: ...
```

`describe()` 返回前端和 planner 可用的纯 dict，至少包含：

```python
{
  "name": "decision",
  "description": "...",
  "category": "decision",
  "requires_image": False,
  "requires_user": False,
  "input_fields": [...],
  "output_fields": [...],
  "intent_keywords": [...],
  "completion_criteria": "...",
  "timeout_ms": 10000,
  "max_retries": 0,
}
```

### 4.3 统一 Skill 执行 wrapper

在 `app/agent/tools.py` 中新增或封装一个统一执行函数，建议：

```python
async def execute_tool(registry: ToolRegistry, name: str, state: AgentState) -> SkillExecutionResult:
    ...
```

可以用 dataclass：

```python
@dataclass
class SkillExecutionResult:
    output: dict
    status: str
    latency_ms: int
    retry_count: int
    error_code: str | None = None
    message: str = ""
    descriptor: dict | None = None
```

要求：

1. 使用 `asyncio.wait_for(tool(state), timeout=descriptor.timeout_ms / 1000)`。
2. 捕获异常并归一化：
   - `TimeoutError`
   - `VLM_NOT_CONFIGURED`
   - `VLM_UNAVAILABLE`
   - `ValueError`
   - 其他异常用异常类名
3. 如果错误可重试，最多按 descriptor `max_retries` 重试。
4. 成功返回 `status="success"`。
5. 失败返回 `status="error"`，不要在 wrapper 内吞掉全部上下文。

### 4.4 Runtime / LangGraph 事件统一

`tool_result` 事件必须新增：

```python
{
  "type": "tool_result",
  "phase": "EXECUTING",
  "tool": "sense",
  "skill": {
    "name": "sense",
    "category": "perception",
    "timeout_ms": 12000
  },
  "status": "success" | "error",
  "latency_ms": 1234,
  "retry_count": 0,
  "error_code": null,
  "summary": {...},
  "step": 0
}
```

`plan` 事件必须新增：

```python
"available_skills": ["sense", "decision", ...]
```

先只放 skill name 列表，不要把完整 descriptor 塞进每个 plan event，避免事件过大。

### 4.5 sense 始终注册

当前 `app/routers/agent.py` 里：

```python
if settings.vlm_api_url:
    tools.register("sense", sense_tool)
```

必须改为始终注册 `sense`。

`sense_tool` 逻辑：

```python
async def sense_tool(state):
    if not state.get("image_url"):
        raise ValueError("NO_IMAGE")
    if not settings.vlm_api_url:
        raise RuntimeError("VLM_NOT_CONFIGURED")
    result = await analyze_food(state["image_url"])
    if result is None:
        raise RuntimeError("VLM_UNAVAILABLE")
    return result
```

验收：没配 `vlm_api_url` 时，请求图片识别不应因为工具未注册崩溃，而应返回 `status=degraded`、事件里有 `error_code=RuntimeError` 或归一化后的 `VLM_NOT_CONFIGURED`。优先做归一化为 `VLM_NOT_CONFIGURED`。

---

## 5. 必须新增测试

### 5.1 Registry 测试

文件：`tests/test_skill_registry.py`

必须覆盖：

1. 注册已知 skill 成功。
2. 注册未知 skill 抛 `ValueError`。
3. `describe()` 返回 `decision` 的 descriptor 字段。
4. `descriptor("sense").requires_image is True`。

### 5.2 Wrapper 测试

可以放在 `tests/test_skill_registry.py` 或 `tests/test_agent_loop_engineering.py`。

必须覆盖：

1. 成功 tool 返回 `status=success`、`latency_ms >= 0`。
2. timeout tool 返回 `status=error`、`error_code="TimeoutError"`。
3. 可重试错误会 retry 一次，并记录 `retry_count=1`。

### 5.3 API / LangGraph 测试

文件：`tests/test_agent_loop_engineering.py` 或 `tests/test_agent.py`

必须覆盖：

1. `/v1/agent/execute` 返回的 `tool_result` event 包含 `skill.category`。
2. `sense` 在 VLM 未配置时仍然注册，图片识别请求返回明确降级事件。
3. `plan` event 包含 `available_skills`。

---

## 6. 验证命令

必须至少运行：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_skill_registry.py \
  tests/test_agent_loop_engineering.py \
  tests/test_agent.py \
  tests/test_agent_runtime.py
```

回归：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_agent.py tests/test_agent_runtime.py tests/test_agent_evaluator.py \
  tests/test_decision_memory_matching.py tests/test_feedback_memory.py tests/test_agent_memory_context.py
```

前端快速回归：

```bash
node scripts/verify_frontend_regressions.mjs
```

H5 构建：

```bash
cd bsapp
npm run build:h5
```

如果没有改前端，仍要跑 `node scripts/verify_frontend_regressions.mjs`，因为 Agent API 返回结构变化可能影响前端时间线。

---

## 7. 修复记录要求

完成后新增：

- `docs/迭代修改/42-v6-Skill工业化底座修复记录.md`
- `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/42-v6-Skill工业化底座修复记录.md`

修复记录必须包含：

1. 修改文件清单。
2. 每个修改点的“修改前问题 / 修改后逻辑”。
3. 新增事件结构示例。
4. 完整测试命令和结果。
5. 未完成项：明确写 LLM Planner / Judge / VL cache / 前端展示不在本任务内。

---

## 8. 审查重点

主 agent 会重点检查：

1. 是否只改了 `AgentRuntime`，漏了 `LangGraphAgent`。
2. ToolRegistry 是否真的拒绝未知工具。
3. `sense` 是否真的始终注册。
4. 事件字段是否稳定，不会让前端因为 `undefined` 报错。
5. 测试是否真实覆盖 API 路径，而不是只测 mock runtime。
6. 是否破坏此前用户实测修复。

