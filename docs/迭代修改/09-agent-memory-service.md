# 修改文档 09：提取 agent_memory.py 独立服务 + memory_used 格式修正

## 修改日期

2026-06-19

## 修改原因

对手册 Section 5 进行对齐：
- 将 MemoryContext 组装逻辑从 router 提取到独立服务文件
- memory_used 格式从 `{layer, text}` 修正为 `{type, key, summary}`
- AgentState 增加 `memory_used` 字段

## 文件变更

### 1. 新增 `app/services/agent_memory.py`

**函数 `build_memory_context(db, user_id, previous_state, goal) -> dict`**：
- 从 `app/routers/agent.py` 提取出的独立服务
- 即使未登录也返回安全空结构（四个 key 都存在，数组为空）
- 支持从 previous_state 继承会话记忆
- 组装 preference_memory（来自 feedback）、fact_memory（来自 inventory/meal_memory）、correction_memory（来自 correction_logs）

**函数 `build_memory_used(memory_context) -> list[dict]`**：
```python
# 修改前格式
{"layer": "preference", "text": "偏好口味: high_protein, light"}

# 修改后格式（手册规范）
{"type": "preference", "key": "liked_tags", "summary": "偏好口味: high_protein, light"}
```

**type 枚举**：conversation | preference | fact | correction
**key 枚举**：last_ingredients | health_goal | liked_tags | avoid_tags | liked_ingredients | available_items | nutrition_gap | recent_aliases

### 2. 修改 `app/routers/agent.py`

- 移除内联的 `_build_memory_context` 和 `_build_memory_used` 函数
- 改为从 `app.services.agent_memory` import，简化 router 代码
- memory_used 现在使用 `build_memory_used(memory_context)` 生成

### 3. 修改 `app/agent/state.py`

AgentState 新增字段：
```python
memory_used: list[dict[str, Any]]  # 本次参考的记忆摘要
```
