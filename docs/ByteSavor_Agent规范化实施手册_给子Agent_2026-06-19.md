# ByteSavor Agent 规范化实施手册

日期：2026-06-19  
目标读者：不了解本项目的新工程师 / 子 Agent / 后续代码实现者  
当前基准：ByteSavor V3.4  
核心目标：不要重做项目，不要引入本地 CNN，不要炫技式推翻架构；在现有功能基础上，把 Agent 的 Harness、Loop Engineering、记忆、评估和可观测性做规范。

---

## 0. 给子 Agent 的硬性要求

你接手的不是空项目。当前项目已经有大量可运行代码，任何修改必须遵守：

1. 不要推翻现有后端和前端结构。
2. 不要删除已有功能页面。
3. 不要把所有功能强行塞进 `/v1/agent/execute`。
4. 不要引入本地 CNN、ONNX、MobileNet 等本地视觉模型。
5. 不要返回 mock 识别数据。
6. 不要改动后端底层数据库连接方式，除非任务明确要求。
7. 每个模块先补测试，再改实现。
8. 每次修改后必须跑对应测试；跑不了要写明原因。
9. 任何前端 UI 改动不能破坏底部 TabBar 和已有页面入口。
10. 最终交付必须说明改了什么、为什么改、如何验证、剩余风险。
11. 双 Agent / DeepSeek Judge 可以作为 P1/P2 软评估增强设计，但 P0 不得让它阻塞主流程。
12. 运行时 Hard Evaluator 和离线黑箱 Eval Pipeline 是两件事，不要混在业务接口里实现。

如果你发现外部方案与当前代码不一致，以当前代码为准。

---

## 1. 项目背景：ByteSavor 到底是什么

ByteSavor 是一个围绕“饮食全链路”的多模态 Agent 系统。它不是只做图片识别，也不是只做菜谱推荐，而是把这些步骤串起来：

```text
注册/登录
  -> 用户画像、目标、偏好
  -> 拍照识别食材或餐食
  -> 用户修正识别结果
  -> 形成清单或库存
  -> 推荐菜谱或手动选择菜谱
  -> 清点已有/缺少食材
  -> 加入今日餐食计划
  -> 完成这一餐
  -> 写入营养摄入和偏好记忆
  -> 下一次 Agent 推荐读取库存、收藏、偏好和营养缺口
```

项目的答辩重点不是“我们调用了某个大模型”，而是：

- Agent 有状态，不是单次问答。
- Agent 有工具，不是只调一个模型。
- Agent 有记忆，不是每次都从零开始。
- Agent 有评估，不是模型说什么就信什么。
- Agent 有可观测过程，老师能看到执行时间线。
- Agent 与业务闭环相连：库存、餐食、营养、偏好、社区、收藏都会影响后续结果。

---

## 2. 当前代码结构

项目根目录：

```text
/Users/liwenbin930/Desktop/bytesavor-backend
```

主要目录：

| 目录 | 用途 |
|---|---|
| `app/` | FastAPI 后端 |
| `app/agent/` | Agent 状态、规划、运行时、工具注册 |
| `app/routers/` | 后端 API 路由 |
| `app/services/` | 业务服务 |
| `app/models/` | SQLAlchemy 数据模型 |
| `bsapp/` | 当前主前端 UniApp/H5 |
| `bsapp/src/pages/` | 前端页面 |
| `tests/` | 后端自动化测试 |
| `docs/` | 正式文档 |
| `！！！ByteSavor文档_打开这里！！！/` | 显眼文档副本入口 |

当前 Agent 相关代码：

| 文件 | 当前职责 |
|---|---|
| `app/routers/agent.py` | `/v1/agent/execute` 入口，组装工具，读取用户画像 |
| `app/agent/state.py` | AgentState 和基础意图解析 |
| `app/agent/planner.py` | 根据用户输入和当前状态选择下一步工具 |
| `app/agent/langgraph_runtime.py` | LangGraph 状态图运行时 |
| `app/agent/runtime.py` | 普通 AgentRuntime，提供合并工具输出、构造结果等通用逻辑 |
| `app/agent/tools.py` | ToolRegistry |

当前 Agent 可用工具：

| 工具名 | 后端服务 | 用途 |
|---|---|---|
| `sense` | `app.services.vlm.analyze_food` | 图片食材识别 |
| `decision` | `app.services.decision.recommend` | 菜谱推荐 |
| `task` | `app.services.shopping.merge_shopping_list` | 购物清单合并 |
| `nutrition` | `app.services.nutrition_analyzer.analyze_meal` | 一餐营养分析 |
| `quality` | `app.services.quality.assess` | 食材品质鉴定 |
| `guide` | `app.services.food_guide.guide` | 探店/菜品讲解 |
| `inventory` | `app.services.inventory.current_inventory` | 读取用户库存 |
| `favorites` | `app.services.favorites.list_favorites` | 读取收藏菜谱 |
| `recipe_check` | `app.services.recipe_checker.check_recipe` | 检查某菜谱已有/缺少食材 |

前端 Agent UI：

| 文件 | 职责 |
|---|---|
| `bsapp/src/pages/home/home.vue` | 首页、AI 助手、Agent 时间线、推荐结果展示 |
| `bsapp/src/api/index.js` | `ApiService.agentExecute()` 和其他接口封装 |

当前测试：

| 文件 | 覆盖方向 |
|---|---|
| `tests/test_agent_runtime.py` | 普通 Runtime 工具循环 |
| `tests/test_langgraph_agent.py` | LangGraph 条件循环、缺图澄清、同会话复用 |
| `tests/test_agent_tools_inventory_favorites.py` | Agent 调用库存/收藏/清点 |
| `tests/test_feedback_memory.py` | 偏好记忆 |
| `tests/test_decision.py` | 推荐服务 |
| `tests/test_meals_inventory.py` | 餐食和库存流程 |

---

## 3. 当前已实现与缺口

### 3.1 已实现

- `/v1/agent/execute` Agent 总入口。
- LangGraph 状态图：planner -> tool -> planner -> final / ask_user。
- 工具事件：`plan`、`tool_start`、`tool_result`、`ask_user`、`final`。
- `conversation_id` 同会话记忆雏形。
- 前端 Agent 时间线展示。
- 用户偏好记忆 `PreferenceMemory`。
- 库存、收藏、餐食计划、社区等业务数据。
- 推荐缓存 Redis 基础能力。
- VLM 不可用时不应返回 mock 数据。

### 3.2 主要缺口

1. Agent 记忆不够统一
   - 会话记忆、偏好记忆、库存事实、餐食事实、纠错记忆散落在不同服务里。
   - AgentState 没有统一 `memory_context` 字段。

2. Agent 评估层缺失
   - 没有 `EvaluationResult`。
   - 推荐结果是否覆盖用户核心食材，当前没有硬规则检查。
   - 识别低置信候选是否需要用户确认，Agent 没有统一表达。

3. Loop Engineering 不够显式
   - 有最大步数，但缺少 `termination_reason`。
   - events 没有统一 `phase`。
   - 没有 retry_count、degraded_to 等字段。

4. 识别纠错记忆缺失
   - 用户删除、改名、合并候选没有写入 correction_logs。

5. 演示路径上仍需修
   - “牛肉南瓜减脂30分钟”推荐可能不使用南瓜。
   - 某些识别结果营养值可能为 0。
   - 手机端 API 地址容易配置错。

---

## 4. 总体架构目标

下一轮不是做新模型，而是规范 Agent。

目标架构：

```text
用户输入/图片
  ↓
Agent Harness
  - 构造 AgentState
  - 读取 MemoryContext
  - 注册 ToolRegistry
  - 维护 events/errors/stages
  ↓
Loop Engineering
  1. ROUTING：Planner 选择下一步
  2. EXECUTING：Tool 执行
  3. MERGING：合并工具输出到 AgentState
  4. EVALUATING：硬规则检查结果
  5. TERMINATING：完成/澄清/重试/降级
  ↓
业务工具
  sense / decision / task / nutrition / quality / guide / inventory / favorites / recipe_check
  ↓
记忆系统
  conversation_memory / preference_memory / fact_memory / correction_memory
  ↓
前端可解释输出
  reply / recipes / shopping_list / events / evaluation / memory_used
```

评估体系采用三层，不要只写一个“模型裁判”：

| 层级 | 名称 | 子 Agent 实现要求 |
|---|---|---|
| L1 | Hard Evaluator | P0 必做，纯代码规则，低延迟，写入 events |
| L2 | User Confirmation | P0 必做，硬规则判断不了的主观问题必须让用户确认 |
| L3 | DeepSeek Judge | P1/P2 可选，软评估增强，必须可关闭、可超时、可降级 |
 

---

## 5. 模块一：MemoryContext 统一记忆上下文

### 5.1 目标

让 Agent 每次运行时明确知道“我参考了哪些记忆”，并把这些记忆用于推荐和解释。

### 5.2 记忆分类

```json
{
  "conversation_memory": {
    "last_ingredients": ["牛肉", "南瓜"],
    "last_recipes": ["南瓜牛肉饭"],
    "last_user_goal": "fat_loss"
  },
  "preference_memory": {
    "liked_tags": ["high_protein", "light"],
    "avoid_tags": ["oily"],
    "liked_ingredients": ["牛肉"],
    "avoid_ingredients": []
  },
  "fact_memory": {
    "inventory": [{"name": "南瓜", "amount": 300, "unit": "g"}],
    "today_nutrition_gap": {"protein": 45, "calories": 800},
    "planned_meals": []
  },
  "correction_memory": {
    "recent_aliases": [{"from": "西红柿", "to": "番茄"}]
  }
}
```

### 5.3 子 Agent 任务

**创建文件：**

- `app/services/agent_memory.py`

**修改文件：**

- `app/agent/state.py`
- `app/routers/agent.py`
- `app/agent/runtime.py`
- `app/agent/langgraph_runtime.py`

**新增测试：**

- `tests/test_agent_memory_context.py`

### 5.4 实现要求

`agent_memory.py` 至少提供：

```python
async def build_memory_context(db, user_id: str | None, previous_state: dict | None = None) -> dict:
    ...
```

返回结构必须包含四个 key：

- `conversation_memory`
- `preference_memory`
- `fact_memory`
- `correction_memory`

即使没有登录，也要返回空结构，不能返回 `None`。

`AgentState` 增加：

```python
memory_context: dict[str, Any]
memory_used: list[dict[str, Any]]
```

Agent 输出结果增加：

```json
{
  "memory_used": [
    {"type": "preference", "summary": "参考了 high_protein 偏好"},
    {"type": "inventory", "summary": "读取当前库存 3 项"}
  ]
}
```

`memory_used` 不是装饰字段，必须真实来自本次 Agent 读取到的上下文。允许为空数组，但不能写死假数据。推荐卡片或时间线里的解释必须能追溯到 `memory_used`：

```json
{
  "memory_used": [
    {"type": "preference", "key": "health_goal", "summary": "参考了减脂目标"},
    {"type": "inventory", "key": "available_items", "summary": "读取当前库存 5 项"},
    {"type": "conversation", "key": "last_ingredients", "summary": "沿用了上一轮识别到的牛肉、南瓜"}
  ]
}
```

### 5.5 验收标准

- 未登录调用 Agent 不报错，`memory_context` 为空结构。
- 登录用户调用 Agent，会读取偏好、库存、收藏等已有数据。
- 同一 conversation 第二轮能看到上一轮 ingredients 或 recipes。
- 前端可以展示“本次参考：偏好/库存/收藏/上轮对话”。

---

## 6. 模块二：Hard Evaluator 硬规则评估层

### 6.1 目标

让 Agent 不盲信工具输出。每轮工具完成后，做低成本硬规则检查，并把检查结果写入 events。

### 6.2 子 Agent 任务

**创建文件：**

- `app/agent/evaluator.py`

**修改文件：**

- `app/agent/runtime.py`
- `app/agent/langgraph_runtime.py`
- `app/agent/state.py`

**新增测试：**

- `tests/test_agent_evaluator.py`

### 6.3 数据结构

建议：

```python
from typing import Literal, TypedDict

class EvaluationResult(TypedDict):
    verdict: Literal["PASS", "PARTIAL", "FAIL", "CONFLICT"]
    issues: list[dict]
    suggestions: list[str]
```

### 6.4 评估规则

P0 必须实现：

1. `decision` 结果为空
   - verdict: `FAIL`
   - issue: `NO_RECIPE`

2. 用户输入有核心食材，但推荐 Top 结果覆盖率低于 50%
   - verdict: `CONFLICT`
   - issue: `CORE_INGREDIENT_MISSED`
   - 规则：从用户明确输入或识别确认的食材中抽取核心食材，Top 推荐至少覆盖 50%。2 个食材至少覆盖 1 个，3 个食材至少覆盖 2 个。
   - P1 增强：如果不能覆盖全部核心食材，推荐理由必须解释为什么，例如某个食材建议留到下一餐。

3. `sense` 识别结果里存在 confidence < 0.5
   - verdict: `PARTIAL`
   - issue: `LOW_CONFIDENCE_INGREDIENT`

4. 工具异常
   - verdict: `FAIL`
   - issue: `TOOL_ERROR`

5. 硬规则无法判断的软性问题
   - verdict: `PARTIAL`
   - issue: `NEEDS_USER_CONFIRMATION`
   - 例子：用户是否喜欢这道菜、是否接受替代食材、是否愿意把牛肉留到晚餐。
   - 处理：不要让系统直接决定，返回可操作选项让用户确认。

P1/P2 可选 DeepSeek Judge：

- 只在硬规则 PASS/PARTIAL 但需要软评估时调用。
- 必须有开关，例如 `ENABLE_AGENT_JUDGE=false` 时完全跳过。
- 必须有短 timeout，失败时不影响主结果，只追加 `judge_skipped` 或 `judge_timeout` event。
- 输出只能作为 `suggestions` 或 `soft_score`，不能直接覆盖数据库事实。

### 6.5 events 格式

工具结果后追加：

```json
{
  "type": "evaluation",
  "phase": "EVALUATING",
  "tool": "decision",
  "verdict": "CONFLICT",
  "issues": [{"code": "CORE_INGREDIENT_MISSED", "message": "推荐未覆盖南瓜"}],
  "suggestions": ["降低该菜谱排序或重新推荐"],
  "step": 1
}
```

### 6.6 验收标准

- `tests/test_agent_evaluator.py` 覆盖 PASS、PARTIAL、FAIL、CONFLICT。
- 首页 Agent 时间线能显示“评估通过/部分通过/存在冲突”。
- 对“牛肉南瓜减脂30分钟”这类输入，Top 推荐至少覆盖 50% 核心食材；若未覆盖，必须有 evaluation 事件指出。
- 对“牛肉南瓜鸡蛋减脂30分钟”这类输入，Top 推荐至少覆盖 2 个核心食材；若只覆盖 1 个，必须 CONFLICT。
- 对口味是否满意等硬规则判断不了的问题，必须走用户确认，不能静默写入餐食或库存。

---

## 7. 模块三：Loop Engineering 规范化

### 7.1 目标

把当前隐性的循环过程显式化，让答辩时可以讲清楚：

- 现在处于什么 phase。
- 为什么继续或结束。
- 是否降级。
- 是否需要用户补充。

### 7.2 子 Agent 任务

**修改文件：**

- `app/agent/runtime.py`
- `app/agent/langgraph_runtime.py`
- `app/routers/agent.py`
- `bsapp/src/pages/home/home.vue`

**新增测试：**

- `tests/test_agent_loop_engineering.py`

### 7.3 phase 规范

统一 phase：

- `INIT`
- `ROUTING`
- `EXECUTING`
- `EVALUATING`
- `CLARIFYING`
- `FINISHED`
- `ERROR`

events 必须有 phase：

```json
{"type": "plan", "phase": "ROUTING", ...}
{"type": "tool_start", "phase": "EXECUTING", ...}
{"type": "tool_result", "phase": "EXECUTING", ...}
{"type": "evaluation", "phase": "EVALUATING", ...}
{"type": "final", "phase": "FINISHED", ...}
```

### 7.4 termination_reason

Agent 结果增加：

```json
{
  "termination_reason": "GOAL_ACHIEVED"
}
```

取值：

- `GOAL_ACHIEVED`
- `NEEDS_INPUT`
- `TOOL_ERROR`
- `MAX_STEPS`
- `PARTIAL_SUCCESS`

### 7.5 验收标准

- 所有 Agent events 都有 phase。
- 正常推荐结束为 `GOAL_ACHIEVED`。
- 缺图澄清为 `NEEDS_INPUT`。
- 工具报错为 `TOOL_ERROR` 或 `PARTIAL_SUCCESS`。
- 超过 max_steps 为 `MAX_STEPS`。

---

## 8. 模块四：推荐一致性与记忆解释

### 8.1 目标

修复“用户说了牛肉南瓜，推荐结果却没有南瓜”的问题，并让推荐理由能体现库存、偏好、记忆。

### 8.2 子 Agent 任务

**修改文件：**

- `app/services/decision.py`
- `app/routers/agent.py`
- `app/agent/evaluator.py`
- `bsapp/src/pages/home/home.vue`

**新增测试：**

- `tests/test_decision_memory_matching.py`

### 8.3 规则

1. 用户输入明确食材时，推荐排序必须提高包含这些食材的菜。
2. 如果 Top 推荐不包含核心食材，evaluation 必须标记 `CORE_INGREDIENT_MISSED`。
3. 如果推荐命中偏好，返回 reason：`PREF_MATCH`。
4. 如果推荐命中库存，返回 reason：`INVENTORY_MATCH`。
5. 如果推荐命中上一轮对话食材，返回 reason：`CONVERSATION_MEMORY_MATCH`。

### 8.4 验收标准

输入：

```text
牛肉南瓜减脂30分钟
```

期望：

- 推荐结果至少优先使用牛肉或南瓜。
- 如果没有南瓜菜谱，也要在 evaluation 或 reply 中说明“没有找到同时覆盖牛肉和南瓜的菜，优先推荐牛肉相关菜谱”。
- 不允许静默推荐完全无关菜谱。

---

## 9. 模块五：识别纠错记忆

### 9.1 目标

用户改过的识别结果要沉淀为系统记忆，后续用于标准化和答辩说明“用户纠错会回流”。

### 9.2 子 Agent 任务

**新增模型或表：**

- `CorrectionLog`

**修改文件：**

- `app/models/__init__.py`
- `app/routers/sense.py` 或新增 `app/routers/corrections.py`
- `app/services/intent_keywords.py` 或新增 `app/services/ingredient_normalizer.py`
- `bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue`

**新增测试：**

- `tests/test_correction_memory.py`

### 9.3 表字段建议

```text
id
user_id
source
original_name
corrected_name
action       # rename/delete/merge/weight_adjust
confidence
meta
created_at
```

### 9.4 最小实现

P0 不需要做离线训练，只需要：

- 用户改名时写入 correction log。
- 用户删除低置信候选时写入 correction log。
- `ingredient_normalizer` 使用静态同义词表。
- 后续可人工把高频 correction 加到同义词表。

### 9.5 验收标准

- 用户把“西红柿”改成“番茄”，后端有记录。
- 用户删除一个错误候选，后端有记录。
- 不影响原识别流程。

---

## 10. 模块六：前端展示要求

### 10.1 首页 Agent 时间线

文件：

- `bsapp/src/pages/home/home.vue`

必须展示：

- phase 名称。
- 工具名。
- 耗时。
- evaluation verdict。
- memory_used 简述。
- degraded / error 信息。

展示口径：

```text
规划 ROUTING：选择推荐工具
执行 EXECUTING：调用 decision，耗时 320ms
评估 EVALUATING：命中偏好 high_protein，核心食材覆盖 PASS
完成 FINISHED：生成 3 道菜谱
```

### 10.1.1 HTTP 返回期间的演示稳定方案

P0 不要求真 SSE，但不能让页面长时间空白等待。前端必须做到：

1. 用户点击发送后立即进入 loading。
2. 0-500ms 内显示骨架屏或“正在规划”状态。
3. 请求未返回时显示假进度，最多到 85%-90%，不要假装完成。
4. HTTP 返回后，把后端 `events` 按顺序每 500ms 回放一条，模拟 Agent 正在执行。
5. 回放完成后再显示最终推荐、清单、nutrition、memory_used。
6. 请求失败时显示明确错误和手动输入/重试入口。

这不是伪造 Agent 过程，而是把后端一次性返回的结构化 events 以更适合演示的节奏展示出来。后续如果做 SSE，前端时间线组件可以复用。

### 10.2 不要做的前端改动

- 不要删底部导航。
- 不要把所有页面合并成一页。
- 不要移除社区、收藏、库存、菜谱清点入口。
- 不要把 Agent 时间线隐藏到控制台，必须在 UI 上可见。

---

## 11. 测试命令

后端常用：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_agent_runtime.py tests/test_langgraph_agent.py
```

新增模块后建议跑：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_agent_memory_context.py tests/test_agent_evaluator.py tests/test_agent_loop_engineering.py tests/test_decision_memory_matching.py tests/test_correction_memory.py
```

全量核心回归：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_auth.py tests/test_decision.py tests/test_meals_inventory.py tests/test_feedback_memory.py tests/test_food_guide.py tests/test_inventory_stats.py tests/test_recipe_checker.py tests/test_favorites.py tests/test_community.py tests/test_community_recipe_flow.py tests/test_agent_tools_inventory_favorites.py tests/test_agent.py tests/test_agent_runtime.py tests/test_langgraph_agent.py
```

前端构建：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

注意：如果 pytest 因沙箱无法访问 MySQL 报 `Operation not permitted`，不要把它当业务失败。需要用已启动后端接口或获得数据库权限后再验证。

---

## 12. 我后续 review 子 Agent 代码时会重点查什么

### 12.1 必查

- 是否保留现有页面和接口。
- 是否没有引入本地 CNN/ONNX。
- 是否新增测试。
- events 是否都有 phase。
- Agent 输出是否有 termination_reason。
- memory_context 是否空用户也能返回安全结构。
- evaluation 是否覆盖推荐空、核心食材缺失、低置信识别、工具错误。
- 推荐是否不再静默忽略用户核心食材。
- correction_logs 是否不影响原识别流程。

### 12.2 会打回的情况

- 只写文档不写测试。
- 直接改大段 Agent runtime 但没有测试。
- 把未实现能力写成已实现。
- 用 mock 数据假装 VLM 成功。
- 改前端导致 TabBar 或已有页面消失。
- 为了做 SSE 重构全部接口。
- 为了“工业化”引入过多新依赖。

---

## 13. 推荐实施顺序

第一轮，Agent 输出规范：

1. phase 字段。
2. termination_reason。
3. evaluation 事件。
4. memory_used 字段。
5. 前端时间线展示 evaluation 和 memory_used。
6. 前端 HTTP loading 期间的假进度、骨架屏、events 回放。

第二轮，Agent 记忆：

1. MemoryContext。
2. memory_used。
3. 偏好、库存、收藏、上轮对话进入 AgentState。
4. 推荐理由显示 memory match。

第三轮，业务质量：

1. 推荐核心食材一致性。
2. 识别同义词标准化。
3. 低置信候选确认。
4. 用户确认承担硬规则无法判断的软裁判。
5. correction_logs。

第四轮，稳定性：

1. Redis conversation checkpoint。
2. VLM image hash cache。
3. VLM/LLM timeout 收紧。
4. 手机端 API 地址显示和清理。
5. 可选 DeepSeek Judge 软评估，默认关闭，验证后再开启。

---

## 14. 答辩可用总结

可以这样讲：

> ByteSavor 的 Agent 不是把用户输入直接丢给大模型，而是有一套 Harness 和 Loop Engineering。Harness 负责管理用户上下文、记忆、工具和事件；Loop 负责规划、执行、评估和终止。我们把记忆拆成会话记忆、偏好记忆、事实记忆和纠错记忆，让系统能围绕用户长期状态运行。下一步优化重点不是引入难验证的本地模型，而是让 Agent 的状态、评估、记忆和可观测性更加规范。
