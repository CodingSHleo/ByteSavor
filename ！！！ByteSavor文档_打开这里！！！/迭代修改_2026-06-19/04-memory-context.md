# 修改文档 04：MemoryContext 组装 + memory_used 返回

## 修改日期

2026-06-19

## 修改目标

对应方案文档 Section 3.9（Agent 记忆系统）。在 Agent 请求中组装四层 MemoryContext，并在返回结果中展示 memory_used。

## 文件变更

### 1. 修改 `app/agent/state.py`

**修改位置**：`AgentState` TypedDict（第 10-29 行）和 `new_agent_state()` 函数（第 54-81 行）

**修改前**：
- AgentState 无 `memory_context` 字段
- `new_agent_state()` 无 `memory_context` 参数

**修改后**：
- 新增字段 `memory_context: dict[str, Any]`（第 30 行）
- `new_agent_state()` 新增参数 `memory_context: dict | None = None`
- 初始化为空 dict

### 2. 修改 `app/routers/agent.py`

**新增函数** `_build_memory_context()`（第 23-87 行）：
组装四层记忆：
| 层级 | 数据来源 | 内容 |
|------|---------|------|
| conversation_memory | 当前请求 | last_ingredients, last_recipes, last_user_goal |
| preference_memory | feedback.get_preference_signals | liked/avoid tags & ingredients（各取 8 条） |
| fact_memory | inventory + meal_memory | 库存（前 10 项）、今日餐食（前 5 条）、营养缺口 |
| correction_memory | 预留 | recent_aliases（空，待 P1 correction_logs 填充） |

**新增函数** `_build_memory_used()`（第 90-131 行）：
- 从 memory_context 生成 `memory_used` 列表
- 每条包含 `layer` 和 `text`，例如：
  - `{"layer": "preference", "text": "偏好口味: high_protein, light"}`
  - `{"layer": "fact", "text": "读取当前库存 5 项"}`

**修改** `agent_entry()`：
- 在调用 runtime 前组装 `memory_context`
- 将 `memory_context` 传入 `runtime.run()`
- 将偏好记忆中的 avoid_tags/avoid_ingredients 传入 decision_tool
- 返回结果新增 `memory_context` 和 `memory_used` 字段

**新增 import**：`feedback_svc`, `meal_memory`

### 3. 修改 `app/agent/langgraph_runtime.py`

**修改位置**：`LangGraphAgent.run()` 方法签名（第 50-57 行）

**修改前**：
```python
async def run(self, user_input, conversation_id, image_url=None, preferences=None):
    state = new_agent_state(user_input, conversation_id, image_url, preferences)
```

**修改后**：
```python
async def run(self, user_input, conversation_id, image_url=None, preferences=None, memory_context=None):
    state = new_agent_state(user_input, conversation_id, image_url, preferences, memory_context)
```

### 4. 修改 `app/agent/runtime.py`

**修改位置**：`AgentRuntime.run()` 方法签名（第 34-42 行）

同上，新增 `memory_context` 参数传递。
