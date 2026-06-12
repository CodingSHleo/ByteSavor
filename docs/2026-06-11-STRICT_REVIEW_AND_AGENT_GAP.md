# ByteSavor V3.0 严格复核与 Agent 差距报告

> 复核日期：2026-06-11  
> 依据：当前代码、最近修复提交、`CORE_TECH.md`、`REVIEW_FIXES.md`、pytest 实际结果。

## 结论

本报告初始复核时，ByteSavor 只有固定多模型工作流。2026-06-11 本轮已经完成第一阶段 Agent 升级：

- `/v1/agent/execute` 已切换到真实 LangGraph `StateGraph`。
- 已实现显式 AgentState、Tool Registry、条件边、工具调用循环、结果回写后重新规划。
- 已支持 Sense、Decision、Task、Nutrition、Quality、Guide 动态工具选择。
- 已支持缺图追问、最大步骤终止、工具错误事件和同一 conversation 的跨轮菜谱上下文。
- 前端已展示 `plan/tool_start/tool_result/ask_user/final` 真实事件。

当前准确表述可以升级为：

> 基于 LangGraph 的状态化饮食 Agent：能够按意图动态选择工具，在工具结果回写后重新规划，并保持同一会话的跨轮任务上下文。

但仍不应声称：

- 已实现完整 ReAct 自主推理。
- LLM 已完全接管 Planner。
- 会话状态已持久化到 Redis/数据库。
- E→B 评分反馈闭环已经修复。

## 当前测试基线

```text
36 passed, 2 warnings
```

VLM 不可用契约已经统一为 `status=error / VLM_UNAVAILABLE`，不返回伪造食材。

## 对原审查问题的复核

| ID | 原问题 | 当前真实状态 | 证据与结论 |
|---|---|---|---|
| A1 | B-Y-T-E 不是真闭环 | **未修复** | `feedback.py` 以 `user_id` 写会话偏好；`agent.py` 以新建 `trace_id` 读取。读取还发生在推荐之后，`all_prefs` 未使用。 |
| A2 | Provider 假抽象 | **部分修复** | Sense/Decision/Task 有 Protocol 注入；Intent 默认 Provider 仍在 `_get_intent()` 内 import，未形成统一 Provider 类型和可观测降级结果。 |
| A3 | Service 层数据库边界矛盾 | **未修复/文档错误** | 多个 Service 直接接收 `AsyncSession`。这本身可接受，但 `CORE_TECH.md` 的“不操作数据库连接”承诺不真实。 |
| R1 | 推荐全表扫描 | **部分修复** | 有 `cook_time` SQL 条件；无时间条件/探索模式仍全表读取，食材和标签没有候选召回。 |
| R2 | 权重无评估依据 | **未修复** | 仍为 0.5/0.3/0.2，双向覆盖率已改，但没有离线标注集、NDCG、Hit Rate 或参数实验。 |
| R3 | Fallback 语义不透明 | **基本修复** | 每条菜谱有 `fallback`；尚缺响应顶层 fallback 元信息和放宽了哪些约束。 |
| G1 | Stage 错误语义不足 | **部分修复** | 已加 `error_code/retry_count`，但没有 `degraded_to`、provider、attempts；部分状态不符合 schema。 |
| G2 | 正则食材硬编码 | **部分修复** | 从 `agent.py` 移到 Python 常量文件，不是配置热加载，也不是从菜谱库动态构建。 |
| G3 | mode 语义不清 | **部分修复** | 路由有简单开关，但无显式执行矩阵；`plan` 仍返回三个 stage，`recommend` 禁用图片感知，行为容易误解。 |
| S1 | JWT 弱密钥 | **未修复** | 仅拒绝空值和两个占位值，没有长度/随机性要求；应用启动只 warning，首次签发 token 才失败。 |
| S2 | openid 前端直传 | **未修复** | 只增加注释，客户端仍可传任意 openid 注册/登录。生产环境存在账户冒用风险。 |
| S3 | Redis 策略不足 | **未修复** | 只有统一 600 秒 TTL 和 MD5 key；无分类 TTL、失效规则、击穿保护，且 `setex` 已产生弃用警告。 |
| S4 | 服务端图片大小校验 | **未修复** | 校验 `len(image_url)` 只限制字符串长度，不检查远程图片或 data URL 解码后的字节数；也存在 SSRF 风险。 |
| T1 | 异常/边界测试不足 | **未修复** | 当前 pytest 主要覆盖正向流程；缺 VLM 非标准 JSON、fallback、JWT 篡改/过期、竞态、Agent 分支测试。 |
| D1 | LLM 菜谱质量标注 | **部分修复** | 有 `source` 字段，但没有 `data_quality`、人工审核状态、营养置信度；source 不能替代质量等级。 |

## 新发现的问题

### P0：所谓 E→B 会话闭环完全不生效

位置：

- `app/services/agent.py:42` 每次请求生成新 `trace_id`
- `app/services/agent.py:76` 推荐时固定传入空偏好 `[]`
- `app/services/agent.py:110-113` 推荐结束后才读取会话偏好，且结果未使用
- `app/services/feedback.py:38` 使用 `user_id` 写入缓存

影响：反馈无法影响同会话后续推荐，文档中的“即时闭环”是错误声明。

### P0：图片安全修复检查了错误对象

位置：`app/routers/sense.py:15-17`

证据：`len(req.image_url)` 只是 URL/Base64 字符串长度，不是实际图片大小。

影响：

- 一个很短的 URL 可以指向超大文件。
- 服务端/模型 Provider 可能访问内网地址，形成 SSRF。
- quality、nutrition、guide、agent 图片入口没有统一验证。

### P0：openid 风险只被记录，没有被修复

位置：`app/routers/auth.py:9-31`

影响：知道其他用户 openid 的调用者可以直接登录该账户。注释不构成安全控制。

### P1：Agent 模式只是固定流水线（已修复核心部分）

位置：

- `app/services/agent.py:46-103` 固定 Sense → Decision → Task
- `app/routers/agent.py:24-32` mode 只是禁用函数
- `app/services/langgraph_agent.py:34-50` 明确写着“当前实现：顺序调用”

当前修复：

- 新增 `app/agent/state.py`、`planner.py`、`tools.py`、`runtime.py`、`langgraph_runtime.py`。
- 生产路由实际调用编译后的 `StateGraph`。
- 条件边可路由到工具、追问或结束。
- 工具结果回写 state 后重新进入 Planner。
- 同一 `conversation_id` 可复用上一轮菜谱继续生成购物清单。

剩余：Planner 当前以确定性规则为主，尚未接入 schema 约束的 LLM action planner；会话状态目前为单进程内存，尚未使用 Redis checkpointer。

### P1：用户持久化偏好也没有传给 Agent 推荐（已修复）

Agent 路由现在使用 `get_optional_user` 加载用户画像偏好，并通过 AgentState 传给 Decision Tool。

### P1：文档与代码持续漂移

示例：

- `CORE_TECH.md` 写服务层不操作数据库，实际 Service 持有 Session。
- 文档仍写 `_retrieve() SELECT *`、18 种食材等旧实现。
- `REVIEW_FIXES.md` 把注释、错位缓存、URL 字符串长度检查标成“全部完成”。

## 什么才算本项目的最小 Agent

不以“是否安装 LangGraph”判断，而以行为判断。ByteSavor 至少需要：

1. **稳定会话标识**：客户端传 `conversation_id`，同一对话不因请求生成新身份。
2. **显式状态**：用户目标、图片、已识别食材、候选菜谱、选择结果、清单、偏好、错误和重试次数。
3. **工具注册表**：Sense、Decision、Task、Nutrition、Quality、Guide、Feedback 都以统一 Tool 接口暴露。
4. **动态规划/路由**：根据用户意图和当前状态选择工具，而不是固定执行全部步骤。
5. **条件分支**：识别失败时追问或重试；推荐为空时放宽约束；用户只问文化故事时不生成购物清单。
6. **中间结果驱动下一步**：每个 Tool 的结构化结果进入状态，Planner 再决定下一动作。
7. **终止条件**：达到用户目标、需要用户补充信息、超过最大步骤或发生不可恢复错误。
8. **跨轮记忆**：会话偏好立即生效，持久化画像在后续会话生效。
9. **可观测性**：每次 Tool 调用记录 provider、attempt、错误码、降级目标、耗时和输入摘要。

LangGraph 很适合承载第 2、4、5、6、7、8 项，但它只是状态图运行时，不会自动让系统变成 Agent。

## 修复优先级

### 第一阶段：纠正伪修复和安全边界

1. 统一 VLM 不可用的错误契约，让现有失败测试通过。
2. 引入统一图片输入验证，限制 scheme、host、Content-Type、Content-Length 和实际下载字节数。
3. 区分 `demo` 与 `wechat` 认证模式；生产模式只接受微信 code，由后端换取 openid。
4. 强制 JWT 密钥在启动时校验，至少 32 字节，并限制生产 CORS。
5. 修正文档状态，不再声称 11 项全部完成。

### 第二阶段：建立真正会话闭环

1. Agent 请求增加 `conversation_id`。
2. Agent 路由加载持久化用户偏好，并与会话偏好合并后传给 Decision。
3. Feedback 接收/关联 `conversation_id`，更新同一会话状态。
4. 使用 Redis 替代进程内全局字典并设置 TTL。
5. 增加“反馈后同会话排序改变”的端到端测试。

### 第三阶段：从 Workflow 升级为 Agent

1. 定义 `AgentState`、`ToolResult`、`AgentAction` 和 Tool Registry。
2. 实现确定性的 Router/Planner，先证明条件分支和状态循环正确。
3. 接入 LangGraph `StateGraph` 和 checkpointer。
4. 再让 LLM 只负责生成受 schema 约束的下一动作，工具白名单由后端控制。
5. 前端展示真实的 plan/tool/result/ask-user 过程，而不只是固定三阶段。

### 第四阶段：推荐质量与工程化

1. 建立 50-100 条人工标注查询集。
2. 计算 HitRate@K、NDCG@K，比较权重和候选召回方案。
3. 食材倒排索引或关系表做候选召回。
4. 增加 `data_quality`、`nutrition_confidence`、`human_verified_at`。
5. 明确缓存 key、TTL、失效和击穿策略。

## 答辩口径

当前版本建议表述：

> 我们已经实现了多模型驱动的 BYTE 确定性编排和完整业务链路，并完成了 Agent 状态、工具和可观测性的接口基础。当前正把固定流程升级为具备条件分支、跨轮记忆和动态工具选择的状态图 Agent。

在第三阶段完成前，不建议声称：

- 已实现 ReAct 自主规划。
- 已接入真实 LangGraph。
- E→B 会话反馈已经即时闭环。
- 图片大小和 openid 安全问题已修复。
