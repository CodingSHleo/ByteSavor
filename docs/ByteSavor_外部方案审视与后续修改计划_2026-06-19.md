# ByteSavor 外部方案审视与后续修改计划

日期：2026-06-19  
当前项目基准：ByteSavor V3.4，已包含账号、识别、推荐、餐食记录、营养看板、库存、收藏、社区、Agent 工具链和答辩材料  
文档目的：评估外部“工业化多模态 Agent 系统方案”，筛出适合当前项目的部分，拒绝不匹配或过度承诺的部分，并补齐此前尚未修完的问题清单。

## 1. 结论

外部方案的方向有价值：它抓住了“我们不能只像一个 API 调用项目，而要体现 Agent 编排、状态、工具、评估、记忆和降级”的核心问题。

但它也存在三个明显偏差：

1. 它把项目命名为 V2.0，而我们当前实际已经是 V3.4 方向，已有社区、库存、收藏、餐食计划、偏好记忆和 LangGraph Agent。
2. 它假设很多能力尚未实现，例如 Agent 状态、工具时间线、偏好记忆；这些我们已经有了雏形，不应推倒重来。
3. 它提出了一些短期不该承诺的功能，例如本地 CNN/ONNX 食材分类器、完整 SSE/WebSocket 流式链路、双 DeepSeek Agent 裁判闭环。我们当前不采用本地模型路线，后续重点放在 Agent Harness、Loop Engineering、评估层、记忆层和可观测性规范化。

因此，本项目后续策略是：

- 保留当前 V3.4 架构，不重命名回 V2.0。
- 不推翻现有多页面、多接口设计；Agent 是总入口，但独立功能页继续保留。
- 优先加强 Agent 的“可解释执行过程”“硬规则评估”“可选双 Agent 软评估”和“记忆系统”，而不是马上引入本地 CNN 或全链路重构。
- 优先修演示路径上真实会出问题的缺口：识别纠错、营养计量、库存扣减、偏好记忆参与推荐、手机端稳定性、登录安全边界。

## 2. 当前项目真实状态

### 2.1 已经实现或已有雏形

后端已有：

- `/v1/agent/execute` Agent 总入口。
- `app/agent/state.py` 定义 AgentState。
- `app/agent/planner.py` 做基于意图的工具规划。
- `app/agent/langgraph_runtime.py` 使用 LangGraph `StateGraph` 和 `InMemorySaver`。
- `app/agent/runtime.py` 有事件记录、工具调用、错误记录和最大步数限制。
- Agent 工具包括：sense、decision、task、nutrition、quality、guide、inventory、favorites、recipe_check。
- 用户偏好记忆：`PreferenceMemory`、`preference_memories` 表、评分反馈解析、`session_prefs` 会话偏好回路。
- Redis 推荐缓存：`app/core/cache.py` 和 `decision.py` 中的推荐缓存。
- 社区、收藏、库存、餐食计划、菜谱清点等业务表和接口。

前端已有：

- 首页 AI 助手对话 UI。
- Agent 事件时间线展示：`plan`、`tool_start`、`tool_result`、`ask_user`、`final`。
- Agent 推荐菜谱展示和“记录”入口。
- 独立页面：识别、清单导出、菜谱、健康看板、社区、收藏、库存、菜谱清点、探店向导、品质鉴定、文本导入。

### 2.2 还没有实现或实现不足

- 没有完整 SSE 或 WebSocket 流式接口，现在是普通 HTTP 返回后一次性展示 events。
- LangGraph checkpoint 目前是内存级，未落 Redis，服务重启会丢会话。
- 没有外部方案所说的“双 Agent 裁判”。目前只有工具执行和事件记录，没有独立判断 Agent。
- 没有标准化 SkillRegistry 元数据体系，当前是 ToolRegistry + planner 规则。
- 没有 correction_log 纠错表，用户修改识别结果还没有形成可回流的长期识别记忆。
- VLM 超时偏长，`OpenAICompatProvider` 当前 timeout 为 120 秒，不适合现场演示。
- 没有图片 hash/pHash 缓存，重复图片不会直接命中识别结果。
- 不计划引入本地 CNN/ONNX 降级模型；VLM 不可用时采用手动输入和结构化失败兜底。
- OpenID 仍是演示级直传，生产安全边界不足。
- 数据库迁移仍是运行时 `ALTER/CREATE` 混合方式，不够工程化。

## 3. 对外部方案的逐条审视

### 3.1 “唯一对外接口 `/v1/agent/execute`”

判断：部分采纳。

不完全采纳原因：

- 我们已经按角色做了独立页面和独立接口，这对测试和答辩更清楚。
- 识别、营养分析、探店、品质鉴定、库存、收藏、社区这些功能不应全部藏进一个 Agent 接口，否则演示时会变成黑盒。

采纳方式：

- `/v1/agent/execute` 保留为总入口。
- 独立接口继续保留，用于角色测试和稳定演示。
- 答辩表达改为：“Agent 是统一编排入口，独立接口是可验证能力模块。”

### 3.2 “六层架构”

判断：采纳为文档表达，不强行重构代码目录。

可采用的六层表达：

1. 接入交互层：UniApp/H5、多页面入口、AI 助手。
2. Agent 编排层：LangGraphAgent、ToolRegistry、planner。
3. 状态与事件层：AgentState、events、stages、errors。
4. 业务能力层：识别、推荐、营养、品质、探店、库存、收藏、清点。
5. 数据记忆层：MySQL 用户/库存/餐食/偏好/社区，Redis 缓存。
6. 演示与验证层：demo_tests、自动化 tests、答辩文档。

不采纳点：

- 不按外部方案重新拆出复杂 Harness 目录。
- 不把所有代码重命名为 Access/Harness/Core/Infra，这会增加风险。

### 3.2.1 答辩中可以重点讲的 Harness 与 Loop Engineering

判断：作为“架构思想 + 当前实现映射 + 后续增强路线”重点采纳。

这部分不是空泛概念，适合放进答辩 PPT 的技术架构页。我们要讲的是：ByteSavor 的 Agent 不是一次请求里顺序调用几个 API，而是有一个负责“计划、执行、检查、终止、记录”的工程化外壳。这个外壳就可以称为 Harness；循环执行和边界控制就是 Loop Engineering。

#### A. Harness 在我们项目里的含义

Harness 不等于新建一个叫 `harness.py` 的文件。它是 Agent 外层运行框架，负责把用户输入、用户状态、工具调用、错误处理和最终结果组织起来。

当前代码对应：

- `app/routers/agent.py`：Agent 对外入口，负责组装工具、读取用户画像、调用运行时。
- `app/agent/langgraph_runtime.py`：当前最接近 Harness 的核心，负责 LangGraph 节点编排。
- `app/agent/runtime.py`：保留了普通 Runtime 版本，包含事件记录、工具执行、错误合并、结果构造。
- `app/agent/state.py`：定义 AgentState，是 Harness 内部流转的状态容器。
- `app/agent/tools.py`：ToolRegistry，负责把业务能力标准化为可调用工具。
- `app/agent/planner.py`：根据用户意图选择下一步工具。

答辩表达：

> 我们把 Agent 的外层运行框架抽象成 Harness。它不负责具体识别或推荐，而是负责生命周期管理：接收用户输入、恢复上下文、选择工具、记录过程、处理错误、输出可解释结果。这样每个能力模块可以独立测试，Agent 只负责把它们组织成一条可追踪的任务链。

#### B. Loop Engineering 在我们项目里的含义

Loop Engineering 指的是 Agent 每一轮不是“随便调用模型”，而是按固定循环推进：

```text
用户输入
  -> 构造 AgentState
  -> Planner 判断下一步
  -> 调用 Tool
  -> 合并 Tool 输出
  -> 记录 event/stage
  -> 判断是否继续
  -> finish / ask_user / degraded
```

当前代码对应：

- `LangGraphAgent._planner_node()`：判断下一步 action。
- `LangGraphAgent._tool_node()`：执行工具并记录 tool_start/tool_result。
- `LangGraphAgent._ask_user_node()`：信息不足时转为澄清。
- `LangGraphAgent._final_node()`：构造最终回复并结束。
- `AgentRuntime._result()`：统一输出 status、reply、events、errors、degraded。

当前已有的循环边界：

- 最大步骤数：`max_steps=8`。
- 工具错误会写入 `errors`。
- 结果有 `degraded` 标记。
- 前端能展示 `events` 时间线。

还需要补强的循环边界：

- 总耗时 timeout。
- 每个工具独立 timeout。
- retry_count。
- 明确 termination_reason，例如 GOAL_ACHIEVED、TOOL_ERROR、MAX_STEPS、NEEDS_INPUT。
- evaluation 事件，用来说明工具结果是否满足任务目标。

答辩表达：

> Loop Engineering 解决的是 Agent 失控问题。我们给 Agent 设置了最大步数、工具错误记录、降级标记和可视化事件。下一步会加入更细的终止原因、工具级超时和评估事件，让 Agent 不会无限循环，也不会在外部模型失败时无声失败。

#### C. 状态机应该怎么讲

外部方案提出 8 状态状态机。我们不应说“已经完整实现 8 状态状态机”，但可以说当前实现已经有状态机雏形，并且可以映射到工业化状态：

| 工业化状态 | 当前实现映射 | 说明 |
|---|---|---|
| INIT | `new_agent_state()` | 构造 conversation、trace、intent、用户偏好 |
| ROUTING | `_planner_node()` / `plan_next_action()` | 判断下一步调用哪个工具 |
| EXECUTING | `_tool_node()` | 执行 sense、decision、inventory 等工具 |
| CLARIFYING | `_ask_user_node()` | 图片缺失或信息不足时请求用户补充 |
| EVALUATING | 当前未独立成节点，计划新增 hard evaluator | 用硬规则判断结果是否满足目标 |
| FINISHED | `_final_node()` | 生成最终回复 |
| ERROR/DEGRADED | `errors` + `degraded` | 工具失败或超步数后降级返回 |

答辩表达：

> 当前版本采用 LangGraph 实现状态化编排，已经覆盖初始化、路由、执行、澄清、完成和降级。评估节点目前以结果检查和错误标记为主，后续会独立成 EVALUATING 节点，形成更完整的工业状态机。

#### D. 事件发射器和可观测性怎么讲

外部方案里说 EventEmitter 和 SSE。我们当前没有真 SSE，但已经有可观测事件。

当前事件类型：

- `plan`：规划下一步。
- `tool_start`：开始调用工具。
- `tool_result`：工具完成或失败，包含耗时。
- `ask_user`：需要用户补充信息。
- `final`：最终结果。

前端对应：

- `bsapp/src/pages/home/home.vue` 已展示 Agent 时间线。
- 用户能看到 Agent 调用了什么工具、是否成功、耗时多少、最后推荐什么。

答辩表达：

> 我们先选择稳定的一次性事件返回，而不是直接上 SSE。因为手机端演示稳定性优先。虽然当前不是实时流式，但后端已经按事件模型组织，未来只需要把 events 从一次性返回改为 SSE 推送，前端时间线结构不用推翻。

#### E. Harness / Loop Engineering 的 PPT 架构图文案

可以在 PPT 中用这一版：

```text
用户输入/图片
   ↓
Agent Harness 外层框架
   - 会话上下文：user_id / conversation_id / preferences
   - 状态容器：AgentState
   - 工具注册：ToolRegistry
   - 过程记录：events / stages / errors
   ↓
Loop Engineering 循环
   1. ROUTING：Planner 选择下一步
   2. EXECUTING：调用识别/推荐/库存/收藏/营养工具
   3. MERGING：合并工具输出到 AgentState
   4. EVALUATING：硬规则检查结果是否满足目标
   5. TERMINATING：完成、澄清、重试或降级返回
   ↓
可解释输出
   - 推荐菜谱
   - 购物清单
   - 库存清点
   - 营养结果
   - Agent 时间线
```

一句话总结：

> Harness 保证 Agent 有工程边界，Loop Engineering 保证 Agent 能一步步推进、可终止、可解释、可降级。

### 3.3 “8 状态有限状态机”

判断：降级采纳。

当前已有 LangGraph 节点：planner、tool、ask_user、final。它已经能表达“规划、执行、澄清、结束”。

短期不建议直接引入 8 个状态，因为：

- 当前 planner 简单稳定，演示风险低。
- 8 状态完整实现会牵涉接口、测试、前端显示和异常处理。
- 答辩前强重构 Agent 核心容易引入回归。

建议实现方式：

- P0：不改 LangGraph 主结构，只在 events 中增加 `phase` 字段，映射成 INIT、ROUTING、EXECUTING、EVALUATING、FINISHED、ERROR。
- P1：增加合法跳转校验器，但先作为内部 helper，不重写 runtime。
- P2：如果后续时间充足，再抽象正式 StateMachine。

### 3.4 “双 Agent：执行 Agent + 判断 Agent”

判断：方向正确，不否定；但要分层落地，不能让它替代硬规则和用户确认。

原因：

- 让同一个 DeepSeek 既生成又裁判，确实能提升答辩上的 Agent 深度。
- 但完全依赖 LLM 裁判会带来成本、延迟和不稳定。
- 当前演示最需要的是可解释、稳定、低延迟；双 Agent 更适合做“软评估增强”，不适合一开始就控制全部运行时决策。

最终采用“三层裁判体系”：

| 层级 | 名称 | 作用 | 运行时机 | 是否 P0 |
|---|---|---|---|---|
| L1 | Hard Evaluator | 用代码规则检查非空、核心食材覆盖、低置信识别、工具错误 | 每次请求中 | 是 |
| L2 | User Confirmation | 对“好不好吃、是否符合个人口味、是否接受替代食材”等软判断，由用户确认 | 推荐/摄入/导入前 | 是 |
| L3 | DeepSeek Judge | 对步骤清晰度、口味合理性、推荐解释等软维度做结构化评审 | P1/P2 可开关 | 否 |

这里的关键不是“不可行”，而是不能让 LLM 裁判成为唯一事实来源。硬规则负责可程序化判断，用户确认负责主观偏好，DeepSeek Judge 负责增强可解释性和答辩技术深度。

建议路线：

- P0：实现 `EvaluationResult` 硬规则评估，不调用 LLM。
  - 推荐列表为空：FAIL。
  - 识别结果低置信度：PARTIAL，需要用户确认。
  - 推荐菜谱使用用户明确食材低于 50%：CONFLICT。
  - 推荐菜谱完全不使用用户输入食材：FAIL。
  - 库存清点缺失过多：PARTIAL。
- P0：硬规则覆盖不了的软性判断，不让系统自作主张，转为用户确认，例如“是否接受把牛肉留到下一餐”“是否喜欢这道菜”。
- P1：加入可选 DeepSeek Judge，仅在硬规则通过但需要软评估时调用，不阻塞主流程。
- P2：把 Judge 的输出接入重试和澄清，但必须有开关、超时和降级文案。

答辩口径：

> 当前版本采用“硬规则裁判 + 用户确认 + 可扩展 LLM Judge”的混合评估框架。双 Agent 评估不是不可行，而是要放在软评估层，和硬规则、用户确认共同工作，避免把另一个模型变成新的黑盒。

### 3.5 “Skill 体系替代散装 Prompt”

判断：采纳，但不能一次性大改。

当前实际是 ToolRegistry，不是正式 SkillRegistry。外部方案提出的 Skill 元数据值得采用，但应渐进落地。

建议：

- P0：新增轻量 `SkillDescriptor` 文档或代码结构，描述现有工具的输入、输出、完成条件。
- P1：将 planner 的意图关键词与 SkillDescriptor 绑定，减少硬编码。
- P2：把 prompt_template、fallback_skill、completion_criteria 统一配置化。

不建议：

- 现在直接把所有工具重构为 Skill 类体系。

### 3.6 “视觉识别四层优化”

判断：高度采纳，但拆分优先级。

已实现部分：

- 前端已有图片压缩逻辑。
- VLM prompt 已要求 JSON。
- `_parse` 已能处理 Markdown JSON 块和嵌入 JSON。
- 识别后前端已经支持用户删除、修改、合并候选。

应补齐：

- P0：标准化映射：番茄/西红柿、土豆/马铃薯、青菜/小白菜等。
- P0：置信度分级：高置信自动展示，低置信标为“待确认”。
- P0：营养数据挂载：识别后立即显示单项营养和占日目标比例。
- P1：记录用户纠错行为到 `correction_logs`。
- P2：纠错日志离线回流到同义词和识别后处理规则。

暂不承诺：

- EXIF/颜色直方图场景路由，短期收益有限。
- 后端图像增强，需要额外图像处理依赖和测试。

### 3.7 “SSE/异步任务/假进度”

判断：分层采纳。

已实现：

- 前端已有加载状态、Agent 时间线展示。
- 后端已返回 events，能解释执行过程。

未实现：

- 真 SSE。
- task_id 异步任务队列。
- 每个食材逐个流式返回。

建议：

- P0：不用真 SSE，先把普通 HTTP 返回的 events 展示得更像时间线，保证演示稳定。
- P0：请求期间前端必须有 `假进度条 + 骨架屏 + 500ms 逐条回放 events`，避免 3-5 秒白屏；HTTP 返回后按事件顺序模拟流式播放，让评委看到 Agent 在“规划、执行、评估、完成”。
- P1：增加 `/v1/agent/execute/stream` SSE，只服务 Agent 时间线，不改所有业务接口。
- P2：识别接口再做 task_id + 轮询或 SSE。

原因：

- UniApp/H5 和手机端对 EventSource 支持需要测试。
- 现在直接改全链路 SSE 风险高。

### 3.8 “Redis Checkpoint、图片 hash 缓存”

判断：采纳，优先级较高。

当前：

- LangGraph 使用 InMemorySaver。
- Redis 已接入推荐缓存。
- Redis 失败会 debug log，不阻塞主流程。

建议：

- P0：保留 InMemorySaver，不影响演示。
- P1：Agent conversation state 落 Redis，TTL 15 分钟。
- P1：图片 base64 或 URL 做 md5 缓存，缓存 VLM 识别结果 10-30 分钟。
- P2：pHash 相似图缓存，先不做。

### 3.9 “Agent 记忆系统”

判断：重点采纳，作为下一轮 Agent 规范化主线之一。

外部方案提到了会话级 Checkpoint 和用户偏好快照，但没有完全贴合我们当前业务。ByteSavor 的 Agent 记忆不应该只是一段聊天上下文，而应该分成四类：

1. 会话记忆：本轮对话里用户刚说过什么、识别到什么、推荐过什么。
2. 用户偏好记忆：长期喜欢/不喜欢什么口味、食材、做法、目标。
3. 事实状态记忆：当前库存、今日餐食计划、已完成摄入、营养缺口。
4. 纠错记忆：用户把识别结果如何修改、删除、合并，未来用于识别后处理。

#### A. 当前已经有的记忆

- 会话记忆：`conversation_id` + `InMemorySaver` + `_conversation_states`，可以在服务进程内保存上一轮 ingredients、recipes、inventory、favorites。
- 用户偏好记忆：`PreferenceMemory` 表，评分和评论会解析为 liked_tags、avoid_tags、liked_ingredients 等。
- 会话偏好回路：`session_prefs` 已能在反馈后把偏好短期写回推荐。
- 事实状态记忆：库存表、餐食记录表、今日营养看板已经存在。
- 收藏记忆：收藏菜谱能作为显性偏好和后续推荐/清点来源。

#### B. 当前不足

- 会话记忆仍在内存里，服务重启会丢失。
- Agent 每次读取哪些记忆还不够规范，缺少统一 MemoryContext。
- 偏好记忆虽然入库，但推荐排序和解释中还需要更明确地体现。
- 库存/餐食/营养缺口是事实记忆，但 Agent planner 对它们的使用还不够系统。
- 用户纠错没有形成 correction_logs，识别模型后处理无法持续进化。

#### C. 建议实现的 MemoryContext

下一轮建议为 Agent 构造统一上下文：

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

实现方式：

- P0：在 `agent.py` 里组装轻量 MemoryContext，传入 AgentState。
- P0：Agent 返回结果里展示 `memory_used`，说明“本次参考了哪些记忆”，用于答辩说明和用户理解。
- P0：前端时间线或推荐卡片展示 `memory_used` 摘要，例如“参考了您的减脂目标”“读取当前库存 5 项”“避开了不喜欢的香菜”。
- P1：conversation state 落 Redis，TTL 15 分钟。
- P1：推荐服务读取 preference signals，并在推荐理由中标记 `PREF_MATCH`、`MEMORY_MATCH`、`INVENTORY_MATCH`。
- P1：新增 correction_logs 表，记录识别结果修改。
- P2：用 correction_logs 更新同义词和低置信候选处理。

答辩口径：

> 我们把 Agent 记忆拆成四层：会话记忆保证多轮对话不断片，偏好记忆保证越用越懂用户，事实记忆保证推荐基于真实库存和摄入，纠错记忆保证识别结果可以通过用户修正持续改进。这样 Agent 不是一次性问答，而是围绕用户长期状态运行。

### 3.10 “本地轻量 CNN/ONNX 降级”

判断：舍弃，不纳入当前后续路线。

原因：

- 当前项目没有训练数据、模型文件、ONNX Runtime 配置和准确率验证。
- 我们的目标是让 Agent 更规范，而不是引入一个难验证的本地视觉模型。
- 答辩现场承诺“断网后本地识别”风险高，且偏离当前项目重点。

替代方案：

- VLM 不可用时返回结构化失败，不返回 mock。
- 前端引导用户手动输入/文本导入食材。
- 识别结果通过标准化、低置信确认和纠错记忆提升可靠性。

答辩口径：

> 本轮不做本地 CNN 降级。我们的工程重点是把外部 VLM 的结果接入规范 Agent 流程，并通过确认、纠错、缓存、记忆和评估提高可靠性。

## 4. 必须补写/补修的未完成问题

### P0：演示前必须修

1. Agent 推荐食材一致性
   - 问题：用户输入“牛肉南瓜减脂30分钟”，推荐可能用了芹菜而没用南瓜。
   - 修法：推荐后硬规则检查，若核心食材未覆盖，降低该菜谱排序或标记原因。
   - P0 验收：推荐 Top 结果必须覆盖用户明确食材的至少 50%。例如“牛肉、南瓜”至少用 1 个；“牛肉、南瓜、鸡蛋”至少用 2 个。
   - P1 验收：尽可能同时使用全部核心食材；如果做不到，必须在推荐理由中解释，例如“南瓜用于本餐，牛肉建议保留到下一餐补蛋白”。

2. 识别结果营养计量
   - 问题：食材数量、重量决定营养素，不能识别了但营养全 0。
   - 修法：按 `weight_estimate` 或用户输入数量计算单项营养；清单页显示“本次食物营养”和“今日剩余缺口”。
   - 验收：西瓜、鸡蛋、米饭等常见食物有非 0 热量和宏量营养素。

3. 清单确认摄入流程
   - 问题：识别不等于已经吃；导出清单不应自动计入。
   - 当前方向：清单页有确认摄入/加入计划，餐食完成后写入长期记录。
   - 仍需检查：按钮位置、餐时选择、完成后库存扣减和今日看板更新。

4. 低置信识别候选处理
   - 问题：一个西瓜被识别成多个物体时，导出清单和营养重复。
   - 当前已有合并/删除/修订，但需要继续验证。
   - 修法：同名/近义名合并，低置信候选默认待确认，不自动入库。

5. 手机端登录和接口地址
   - 问题：手机访问 localhost 会请求手机自己。
   - 当前已修 H5 localhost -> 127.0.0.1，但手机仍需局域网 IP。
   - 修法：设置页增加 API 地址显示/修改入口，演示前清理旧 `api_base_url`。

6. 文档入口可见性
   - 问题：用户找不到 docs。
   - 当前已新增 `！！！ByteSavor文档_打开这里！！！`，但需把本文件也复制进去。

### P1：答辩前建议修

1. Agent 评估层
   - 增加硬规则 Evaluator。
   - 输出 `evaluation` 字段：verdict、issues、suggestions。
   - 前端时间线显示“规则评估通过/部分通过/冲突”。
   - 明确它是运行时 Evaluator，不等同于离线黑箱 Eval Pipeline。
   - 可选 DeepSeek Judge 只作为软评估增强，不作为 P1 必须项。

2. Agent 状态语义增强
   - 当前 events 有 plan/tool_start/tool_result/final。
   - 增加 phase 映射：ROUTING、EXECUTING、EVALUATING、FINISHED。
   - stages 增加 degraded_to、retry_count、error_code。

3. Redis 会话 checkpoint
   - conversation_id 对应 state 存 Redis。
   - TTL 15 分钟。
   - 服务重启后可恢复最近会话。

4. 图片识别缓存
   - 对 image_url 或 base64 内容 hash。
   - 命中时直接返回识别结果，并在 events 标记 cache_hit。

5. correction_logs 纠错日志
   - 记录用户删除、改名、合并、重量修改。
   - 后续用于同义词和识别后处理优化。

6. VLM/LLM 超时收紧
   - VLM 120 秒过长，演示会卡。
   - 建议 VLM 15-20 秒，LLM 10-15 秒，失败后返回可解释降级。

7. 推荐全表扫描优化
   - 当前菜谱量不大，可以演示。
   - 但应补文档说明短期可接受，后续用食材倒排索引/SQL 预过滤。

### P2：后续增强，不作为当前必修

1. 真 SSE 流式 Agent。
2. task_id 异步识别队列。
3. 可选 DeepSeek Judge / 双 Agent 软评估。
4. 更完整的 MemoryContext 压缩与摘要。
5. 数据库正式迁移工具 Alembic。
6. 生产级微信登录 code2session 或用户名密码体系。
7. 菜谱数据质量字段：human_verified、scraped、llm_generated。
8. 离线黑箱 Eval Pipeline：30-50 条黄金场景、规则评分 + 可选 LLM Judge、版本退化报告。

## 5. 已经修过但仍需写进答辩/文档的问题

1. 不再返回 mock VLM 数据
   - VLM 不可用时应报错或走手动输入兜底，不应假装识别成功。

2. 偏好闭环已经有初步实现
   - 评分和评论进入 PreferenceMemory。
   - session_prefs 提供会话级偏好回路。
   - 推荐时应继续确认偏好信号是否进入排序。

3. 图标缺失已补齐
   - `icon_search.svg`、`icon_leaf.svg`、`icon_calendar.svg` 等缺失问题已作为 UI 层渲染风险处理。

4. 登录/注册请求失败已定位
   - 曾由 8000 端口被其他项目占用和 localhost/IPv6 问题导致。
   - 前端错误提示已更清晰，注册页本地登录态已统一。

5. 社区/收藏/库存不是附属功能
   - 它们是 Agent 个性化推荐的数据来源：收藏代表显性偏好，库存代表可执行约束，社区代表用户生成菜谱来源。

## 6. 建议下一轮实施顺序

### 6.0 P0/P1/P2 总表

| 优先级 | 要解决的问题 | 主要交付 | 不做什么 |
|---|---|---|---|
| P0 | 演示稳定、推荐不跑偏、过程可解释 | Hard Evaluator、核心食材 50% 覆盖、`phase`、`termination_reason`、`memory_used`、前端假进度/骨架屏/events 回放 | 不做真 SSE，不做本地 CNN，不做 LLM 裁判闭环 |
| P1 | Agent 更规范、记忆更可信 | Redis checkpoint、图片 hash 缓存、correction_logs、偏好/库存进入推荐理由、可选 DeepSeek Judge 软评估 | 不让 LLM Judge 阻塞主流程 |
| P2 | 工程化质量评估和长期扩展 | 离线黑箱 Eval、SSE、任务队列、MemoryContext 摘要、Alembic | 不承诺现场断网本地识别 |

### 6.1 运行时 Evaluator 与离线黑箱 Eval 的区别

外部方案最重要的提醒是：单元测试通过不代表用户满意。因此这里必须区分两种“评估”，不能混为一谈。

| 类型 | 目的 | 方式 | 时机 | ByteSavor 落地 |
|---|---|---|---|---|
| 运行时 Hard Evaluator | 防止当前请求出现明显错误 | 代码规则 + 少量用户确认 | 每次 Agent 请求中 | P0/P1 做在 `app/agent/evaluator.py` |
| 离线黑箱 Eval Pipeline | 衡量版本质量是否变好 | 黄金用例 + 规则 scorer + 可选 LLM Judge | 发版前/回归时 | P2 或下一轮任务做在 `evals/` |

运行时 Evaluator 只回答“这次输出有没有明显冲突”。离线黑箱 Eval 才回答“用户整体会不会满意、这次迭代有没有退步”。

冷启动阶段没有真实用户日志，离线 Eval 用例由团队手工构造 30-50 条黄金场景，覆盖纯识别、纯推荐、多约束推荐、状态依赖、信息不足澄清、冲突约束处理。先做 10 条 quick set 跑通框架，再扩充到 full set。

### 6.2 答辩技术架构陈述口径

Harness / Loop Engineering 不应只放在“外部方案审视”里，它是答辩时的核心架构表达。建议 PPT 或讲稿中单独这样讲：

```text
前端体验层
  - 拍照识别、清单确认、推荐、社区、收藏、健康看板
  - 等待期间使用假进度、骨架屏和事件回放减少黑盒感

Agent Harness 层
  - 组装 user_id、conversation_id、MemoryContext
  - 维护 AgentState、ToolRegistry、events、errors
  - 统一输出 reply、recipes、evaluation、memory_used

Loop Engineering 层
  - ROUTING：Planner 选择工具
  - EXECUTING：调用识别/推荐/库存/营养等工具
  - EVALUATING：Hard Evaluator 检查结果
  - CLARIFYING：硬规则判断不了时让用户确认
  - FINISHED/DEGRADED：带 termination_reason 结束

业务能力层
  - sense / decision / nutrition / guide / quality / inventory / favorites / recipe_check

数据记忆层
  - 用户、库存、餐食、偏好、收藏、社区、纠错日志

质量评估层
  - 单元测试保证代码不崩
  - 运行时 Evaluator 拦截明显错误
  - 离线黑箱 Eval 衡量用户满意度
```

### 6.3 第一批：低风险、高收益

1. 新增 Agent hard evaluator。
2. Agent events 增加 evaluation 事件。
3. 推荐结果检查核心食材覆盖。
4. 识别后处理增加同义词标准化和低置信标记。
5. 清单页再次检查营养非 0、数量/重量可编辑、确认摄入位置。

### 6.4 第二批：中等风险

1. Redis conversation checkpoint。
2. VLM 图片 hash 缓存。
3. correction_logs 表和接口。
4. VLM/LLM timeout 收紧，并补明确降级文案。
5. 可选 DeepSeek Judge，只处理硬规则无法覆盖的软评估，不默认阻塞主流程。

### 6.5 第三批：高风险或后续研究

1. 真 SSE。
2. DeepSeek Judge 接入自动重试/澄清。
3. 多轮 MemoryContext 摘要压缩。
4. 大规模推荐索引重构。

## 7. 答辩表达建议

不要说：

> 我们已经实现了完整工业级双 Agent、SSE、本地模型降级。

应该说：

> 我们当前版本已经实现了 Agent 工具编排、状态事件追踪、用户库存/收藏/偏好记忆接入和多角色功能闭环。下一步重点不是引入本地模型，而是规范 Agent Harness、Loop Engineering、MemoryContext、硬规则评估和可观测事件。

可以强调：

- 不是单纯 API 调用：因为 Agent 会读取用户状态、选择工具、记录事件、合并结果，并把结果写回可操作模块。
- 不是一次性推荐：因为库存、餐食完成、评分反馈和偏好记忆会影响后续推荐。
- 不是黑盒模型：因为前端能展示工具调用时间线、耗时、错误和降级状态。
- 不是过度设计：因为独立页面保证演示稳定，Agent 总入口展示系统智能编排。

## 8. 本文档对应的实际代码证据

- Agent 状态：`app/agent/state.py`
- Agent 规划：`app/agent/planner.py`
- Agent runtime：`app/agent/runtime.py`
- LangGraph runtime：`app/agent/langgraph_runtime.py`
- Agent 路由：`app/routers/agent.py`
- 偏好记忆：`app/services/feedback.py`
- Redis 缓存：`app/core/cache.py`
- VLM Provider：`app/services/vlm/openai.py`
- VLM Prompt：`app/services/vlm/prompts.py`
- 首页 Agent UI：`bsapp/src/pages/home/home.vue`
- 前端 API：`bsapp/src/api/index.js`
