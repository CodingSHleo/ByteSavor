# ByteSavor v3 最终复核报告：MySQL 已验证版

日期：2026-06-20  
复核目标：确认 v3 修复是否真实完成，并把 MySQL 测试失败从“代码问题”与“沙箱权限问题”中区分出来。

结论先行：

v3 主体可以认可。之前在普通沙箱中看到的 MySQL 失败，不是业务代码失败，而是沙箱禁止连接本机 `127.0.0.1:3306`。使用允许访问本机 MySQL 的沙箱外命令复跑后，DB 依赖测试集合通过。

当前可确认结果：

| 检查项 | 结果 | 结论 |
|---|---:|---|
| H5 构建 | `DONE Build complete` | 通过 |
| 核心非 DB 测试 | `80 passed` | 通过 |
| DB 依赖测试 | `23 passed` | 通过 |
| Eval quick | `42/42 (100%)` | runner/scorer 骨架通过 |
| 弯引号检查 | 无结构性代码风险 | 通过 |
| 文档同步 | 21/22/23 已同步 | 通过 |

需要保留的边界：

Eval quick 当前仍是 `mock runtime` 模式，证明的是 Eval 框架、case、scorer、report 能跑通，不等同于完整真实 API 黑箱 Eval。后续仍建议补 `--mode api`。

---

## 1. MySQL 问题最终定性

### 1.1 普通沙箱中的失败

在普通工具沙箱内运行 DB 相关测试时，失败信息集中为：

```text
Can't connect to MySQL server on '127.0.0.1' ([Errno 1] Operation not permitted)
```

这说明当前执行环境不允许连接本机 MySQL 端口。这个错误发生在 socket connect 阶段，尚未进入业务 SQL 或断言逻辑。

### 1.2 沙箱外复跑结果

对最早失败的两个文件复跑：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_decision.py \
  tests/test_agent_tools_inventory_favorites.py
```

结果：

```text
7 passed in 0.48s
```

对完整 DB 依赖集合复跑：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_auth.py \
  tests/test_decision.py \
  tests/test_meals_inventory.py \
  tests/test_feedback_memory.py \
  tests/test_inventory_stats.py \
  tests/test_recipe_checker.py \
  tests/test_favorites.py \
  tests/test_community.py \
  tests/test_community_recipe_flow.py \
  tests/test_agent_tools_inventory_favorites.py
```

结果：

```text
23 passed in 3.66s
```

结论：

MySQL 相关失败已排除为代码失败。后续如果在普通沙箱看到同类错误，应按“执行权限限制”处理，不应写成业务回归失败。

---

## 2. 当前复跑证据

### 2.1 核心非 DB 测试

命令：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_agent_evaluator.py \
  tests/test_agent_memory_context.py \
  tests/test_agent_loop_engineering.py \
  tests/test_decision_memory_matching.py \
  tests/test_correction_memory.py \
  tests/test_agent_runtime.py \
  tests/test_langgraph_agent.py \
  tests/test_nutrition_calculator.py \
  tests/test_agent_memory_api.py \
  tests/test_agent_confirmation_prompts.py \
  tests/test_agent.py \
  tests/test_food_guide.py
```

结果：

```text
80 passed in 0.10s
```

说明：

这组测试不依赖本机 MySQL，适合普通沙箱和日常快速回归。

### 2.2 H5 构建

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

结果：

```text
DONE  Build complete.
```

说明：

Sass deprecation warning 仍存在，但不影响当前构建。

### 2.3 Eval quick

命令：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick
```

结果：

```text
Loaded 10 cases from /Users/liwenbin930/Desktop/bytesavor-backend/evals/cases/quick.jsonl
Report written: /Users/liwenbin930/Desktop/bytesavor-backend/evals/reports/latest.json
Report written: /Users/liwenbin930/Desktop/bytesavor-backend/evals/reports/latest.md
Score: 42/42 (100%)
```

说明：

这个结果可复现，但当前 runner 使用 mock decision 工具，不是完整真实 API 黑箱 Eval。它可以作为 Eval P0 工程骨架验收，不应被表述为“真实用户满意度 100%”。

---

## 3. v3 修复完成度判断

### 3.1 可以认可为完成的项

| 项目 | 状态 | 依据 |
|---|---:|---|
| V3-1 测试结论修正 | 完成 | v2 文档已不再无条件写 `82 passed` |
| V3-2 文档同步 | 完成 | 可见目录包含 19/20/21/22/23 |
| V3-3 MemoryContext previous state 测试 | 基本完成 | runtime 层测试通过 |
| V3-4 纠错日志失败可观测 | 完成 | `console.warn('[correction] recordCorrection failed:', e)` |
| V3-5 弯引号说明修正 | 完成 | 文档改为 Unicode 码点口径 |
| V3-6 confirmation prompts 测试 | 完成 | 独立 issue 测试通过 |
| V3-7 CorrectionLogRequest 校验 | 基本完成 | Pydantic 校验测试通过 |
| V3-8 注册昵称回归 | 完成 | DB 集合沙箱外通过 |
| 黑箱 Eval P0 骨架 | 基本完成 | `evals/runner.py --quick` 可生成报告 |

### 3.2 仍需精确表述的项

#### MemoryContext API 级测试

当前 `tests/test_agent_memory_api.py` 主要直接调用 `LangGraphAgent`，严格说是 runtime 级测试，不是完整 `/v1/agent/execute` API 测试。

当前可以写：

```text
MemoryContext previous_state runtime 级回归已覆盖。
```

不要写：

```text
完整 API 级 previous_state 回归已覆盖。
```

后续如要补足，应新增真实 `client.post("/v1/agent/execute")` 测试。

#### CorrectionLogRequest 422 测试

当前主要是 Pydantic schema 校验测试，不是 HTTP 422 接口测试。

当前可以写：

```text
CorrectionLogRequest schema 校验已覆盖。
```

不要写：

```text
CorrectionLog API 422 已完整覆盖。
```

后续如要补足，应增加真实 `/v1/correction-logs` 请求并断言 `status_code == 422`。

#### Eval quick

当前可以写：

```text
Eval P0 mock-runtime 骨架已跑通，10 cases / 42 checks 通过。
```

不要写：

```text
完整黑箱 Eval 已验证真实 Agent 质量 100%。
```

---

## 4. 给后续执行的测试命令标准

### 4.1 快速非 DB 回归

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_agent_evaluator.py \
  tests/test_agent_memory_context.py \
  tests/test_agent_loop_engineering.py \
  tests/test_decision_memory_matching.py \
  tests/test_correction_memory.py \
  tests/test_agent_runtime.py \
  tests/test_langgraph_agent.py \
  tests/test_nutrition_calculator.py \
  tests/test_agent_memory_api.py \
  tests/test_agent_confirmation_prompts.py \
  tests/test_agent.py \
  tests/test_food_guide.py
```

当前结果：

```text
80 passed
```

### 4.2 DB 依赖回归

这个命令需要能访问本机 MySQL/Redis。普通沙箱可能失败，应使用允许本机端口访问的执行环境。

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_auth.py \
  tests/test_decision.py \
  tests/test_meals_inventory.py \
  tests/test_feedback_memory.py \
  tests/test_inventory_stats.py \
  tests/test_recipe_checker.py \
  tests/test_favorites.py \
  tests/test_community.py \
  tests/test_community_recipe_flow.py \
  tests/test_agent_tools_inventory_favorites.py
```

当前结果：

```text
23 passed
```

### 4.3 前端构建

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

当前结果：

```text
DONE Build complete
```

### 4.4 Eval quick

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick
```

当前结果：

```text
42/42 (100%)
```

注意：

这是 mock-runtime Eval，不是真实 API Eval。

---

## 5. 下一步建议

### 5.1 不需要继续纠结 MySQL

MySQL 问题已经通过沙箱外 DB 测试验证。当前不是代码阻塞项。

后续只需要在文档里明确：

```text
DB 测试需要本机 MySQL 访问权限；普通沙箱会因权限报 OperationalError。
```

### 5.2 继续修 Eval 的真实性

下一轮最有价值的工作不是再修 MySQL，而是做：

1. `evals/runner.py --mode api`
2. scorer 默认识别 `TOOL_ERROR` / `evaluation FAIL`
3. Q05/Q10/Q09 case 收紧
4. 报告区分 `mock-runtime` 与 `api`

### 5.3 补两个真实 API 测试

建议后续补：

1. `/v1/agent/execute` 同一 conversation 第二轮带出 previous state。
2. `/v1/correction-logs` 非法 action 返回 422。

这两个不是当前阻塞，但能让 v3 的“API 级”说法更扎实。

---

## 6. 对照原规划：还没做什么

本节按我们最早确定的 ByteSavor Agent 规范化路线核对，不把已经明确舍弃的本地 CNN 降级算作缺口。

### 6.1 已经完成的主线

| 模块 | 当前状态 | 说明 |
|---|---:|---|
| Agent Harness 基础结构 | 已完成基础版 | `LangGraphAgent` + runtime events + phase 已可用 |
| Loop Engineering | 已完成基础版 | 有 `ROUTING / EXECUTING / EVALUATING / FINISHED / CLARIFYING` 语义事件 |
| Hard Evaluator | 已完成基础版 | 非空、核心食材覆盖、低置信、工具错误、用户确认 |
| MemoryContext | 已完成基础版 | conversation/preference/fact/correction 四层结构 |
| memory_used 可解释输出 | 已完成 | 后端返回，前端展示 |
| 前端假进度/骨架屏/events 回放 | 已完成 | 不做真 SSE 也能避免演示白屏 |
| correction_logs 基础闭环 | 已完成 | edit/delete 写日志，失败 console.warn |
| 同义词标准化 | 已完成基础版 | decision/evaluator 复用标准化 |
| 注册昵称写入 | 已完成 | DB 测试通过 |
| Eval P0 骨架 | 已完成 mock-runtime 版 | 10 cases + scorer + report |

### 6.2 必须补的短期项

这些是下一轮最应该做的，不建议继续拖。

#### 1. Eval 从 mock-runtime 升级到 api mode

当前 `evals/runner.py --quick` 使用 mock decision 工具，只证明 Eval 框架能跑。还没证明真实 `/v1/agent/execute` 的端到端输出质量。

要求：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode mock
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode api
```

第一版 api mode 至少 3 条：

1. 文本推荐：检查 `reply / recipes / events / evaluation / termination_reason`。
2. 缺图片识别：检查 `needs_input / ask_user / NEEDS_INPUT`。
3. 同一 conversation 第二轮：检查 `memory_context` 或 `memory_used` 带出上一轮信息。

#### 2. Eval scorer 不能放过内部失败

当前报告里曾出现过 Q05/Q10 内部 `TOOL_ERROR`、`evaluation verdict=FAIL` 但仍 PASS 的问题。

要求：

- `termination_reason == "TOOL_ERROR"` 默认失败。
- `evaluation verdict == "FAIL"` 默认失败。
- `status == "degraded"` 默认失败。
- 除非 case 显式 `allow_failure: true`。

验收：

```bash
rg -n "TOOL_ERROR|evaluation verdict: FAIL" evals/reports/latest.md
```

如果报告写 100%，不应出现这些失败信号。

#### 3. 补真正 API 级测试

当前有些测试名字是 API 级，但实际只测 runtime/schema。

需要补：

```text
tests/test_agent_memory_api.py
```

真实调用：

```python
client.post("/v1/agent/execute", json={...})
```

还需要补：

```text
/v1/correction-logs 非法 action 返回 422
```

真实调用：

```python
resp = await client.post("/v1/correction-logs", headers=headers, json={"action": "drop_table", "source": "sense"})
assert resp.status_code == 422
```

#### 4. 修测试命名和收集问题

`tests/test_auth.py` 里有重复函数名 `test_profile_with_token` 的历史问题，需要确保只保留一个同名函数，另一个改成明确名称。

检查：

```bash
rg -n "async def test_profile_with_token" tests/test_auth.py
```

期望只出现一次。

### 6.3 中期应该做的工程化项

这些不一定阻塞当前答辩，但决定项目是否像“工程系统”。

#### 1. 正式数据库迁移

现在仍主要依赖启动时 `create_all` 和服务内 `ensure_*`。

后续应引入 Alembic：

```text
alembic/
  versions/
```

目标：

- 表结构变化可追踪。
- 新机器部署不用靠运行时隐式补列。
- 答辩时能说明数据层是可维护的。

#### 2. 测试数据库隔离

现在 DB 测试依赖本机 MySQL `bytesavor`，虽然已验证能过，但长期会污染开发库。

建议：

- 单独 `bytesavor_test` 数据库。
- 测试前清表或事务回滚。
- 文档写明 `MYSQL_DB=bytesavor_test`。

#### 3. CI 测试分层

建议分三类：

```text
quick: 非 DB 单元/运行时测试
db: MySQL/Redis 集成测试
eval: 离线 Eval quick
```

以后每次交付必须贴三条命令，而不是只写一个 passed 数字。

#### 4. 前端 Agent smoke

目前前端只验证 build，没有验证页面交互。

建议补 Playwright smoke：

- 首页输入 Agent 文本。
- 看到 skeleton。
- 看到 timeline events。
- 看到推荐或确认卡片。
- 无 console error。

### 6.4 Agent 能力增强项

这些是产品能力，不建议在测试证据没收口前继续加。

#### 1. DeepSeek Judge / 双 Agent 软评估

这个 idea 仍然值得做，但顺序应是：

```text
离线 LLM Judge -> 人工抽样校准 -> 可选运行时 Judge
```

运行时版本必须满足：

- 默认关闭。
- 只评估软维度。
- 超时不阻塞主回复。
- 不能覆盖 Hard Evaluator 的事实结论。

#### 2. 真 SSE

当前前端 events 回放已经够演示。真 SSE 可以放到 P1/P2。

建议只新增：

```text
POST /v1/agent/execute/stream
```

不要重构所有业务接口。

#### 3. MemoryContext 摘要压缩

当前 MemoryContext 是轻量拼装，后续多轮对话变长后需要摘要压缩：

- last ingredients
- last recipes
- user goal
- recent corrections
- preference signals

目标是控制 token 和响应体大小。

#### 4. 图片 hash 缓存 / pHash

当前不是主线阻塞。可以先做 MD5 精确缓存，再考虑 pHash 相似图缓存。

### 6.5 明确暂不做或不承诺的项

这些不要写进近期交付承诺：

| 项目 | 原因 |
|---|---|
| 本地 CNN/ONNX 食材识别降级 | 已明确舍弃，不符合当前主线 |
| 全链路 WebSocket | 当前 SSE 都不是刚需，WebSocket 更重 |
| 真实 LLM Judge 阻断主流程 | 延迟、成本、稳定性风险高 |
| 50 条完整 Eval 一步到位 | 先把 10 条 api mode 跑稳 |
| 生产级微信 code2session | 答辩前不是 Agent 规范化主线，但安全文档要说明当前是演示模式 |

### 6.6 建议下一轮任务顺序

推荐下一轮只做 5 件事：

1. 修 Eval scorer，不放过 `TOOL_ERROR / FAIL verdict`。
2. 给 Eval runner 加 `--mode api`。
3. 补 `/v1/agent/execute` previous_state API 测试。
4. 补 `/v1/correction-logs` 422 API 测试。
5. 写 `24-Eval API Mode 与测试收口修复文档.md` 并同步可见目录。

完成后再考虑 DeepSeek Judge 或 SSE。

---

## 7. 最终结论

v3 可以进入下一阶段。

准确口径是：

> ByteSavor v3 已完成 Agent 规范化主链路、前端演示体验、纠错/记忆基础闭环、文档同步和测试证据修正。核心非 DB 回归 80 条通过，DB 依赖回归在 MySQL 可访问环境下 23 条通过，H5 构建通过。当前 Eval 已跑通 mock-runtime 最小闭环，但还需要升级到真实 API mode，才能称为完整黑箱端到端 Eval。

这个口径既能说明当前成果，也不会过度承诺。
