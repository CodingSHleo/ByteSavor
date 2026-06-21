# ByteSavor v4 复审建议与 Eval 修正要求

日期：2026-06-20  
复审对象：
- v3 完成报告
- `docs/迭代修改/21-黑箱Eval最小闭环实现记录.md`
- `evals/runner.py`
- `evals/scorer.py`
- `evals/cases/quick.jsonl`
- v3 新增测试文件

结论先行：

v3 确实继续推进了质量闭环：文档同步完成，H5 构建通过，弯引号检查通过，新增了 Eval 骨架、scorer、10 条 quick cases、MemoryContext/confirmation/correction/auth 相关测试。

但 v3 的完成口径仍然过满。最重要的问题是：现在的 `evals/runner.py` 使用的是 `LangGraphAgent + mock decision 工具`，不是完整调用真实 `/v1/agent/execute` 或真实推荐服务。因此它只能算“离线 Eval P0 骨架跑通”，不能宣称已经完成真正的“黑箱端到端 Eval”。

另外，当前 Eval 报告里 Q05/Q10 出现了 `termination_reason=TOOL_ERROR`、`evaluation verdict=FAIL`，但仍被 scorer 统计为 PASS，导致 `42/42 (100%)` 虚高。这个必须修。

---

## 1. 本轮复审实际结果

### 1.1 H5 构建

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

结果：

```text
DONE  Build complete.
```

结论：通过。只有 Sass deprecation warnings，不影响构建。

### 1.2 弯引号检查

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
rg -n "[“”‘’]" bsapp/src app tests
```

结果：

```text
bsapp/src/pages/text-import/text-import.vue: 中文文案
app/seed/recipes.json: seed 菜谱标题
```

结论：没有发现会破坏 Vue/JS/Python 语法结构的弯引号。剩余均为文案或 seed 数据，可接受。

### 1.3 核心新增测试复跑

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
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
  tests/test_agent_confirmation_prompts.py
```

结果：

```text
71 passed in 0.07s
```

结论：我能复现的是 71 条核心非 DB 测试通过，不是 v3 完成报告里的 `89 passed`。

这不一定说明 89 是假的，但报告没有给出精确 pytest 命令，所以无法复现。后续所有测试结论必须附完整命令。

### 1.4 更宽 Agent 相关测试集合

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
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
  tests/test_agent_tools_inventory_favorites.py \
  tests/test_food_guide.py
```

结果：

```text
80 passed, 1 failed
```

失败：

```text
tests/test_agent_tools_inventory_favorites.py::test_agent_uses_inventory_favorites_and_checker_tools
```

失败原因：

```text
Can't connect to MySQL server on '127.0.0.1' ([Errno 1] Operation not permitted)
```

结论：这个失败属于当前沙箱 DB 连接限制，不是本轮 Agent 逻辑直接失败。但它再次说明测试集合必须明确区分：

- 不依赖 DB 的单元/运行时测试
- 依赖 MySQL/Redis 的集成测试

### 1.5 Eval quick 复跑

命令：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick
```

结果：

```text
Loaded 10 cases from /Users/liwenbin930/Desktop/bytesavor-backend/evals/cases/quick.jsonl
Report written: /Users/liwenbin930/Desktop/bytesavor-backend/evals/reports/latest.json
Report written: /Users/liwenbin930/Desktop/bytesavor-backend/evals/reports/latest.md
Score: 42/42 (100%)
```

结论：`42/42` 可复现，但该分数不能代表真实 Agent 端到端质量。原因见后文 V4-1 和 V4-2。

---

## 2. v3 完成得好的部分

### 2.1 文档同步已完成

`docs/迭代修改` 和 `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19` 均包含：

- `19-v2审查修复记录.md`
- `20-v3复审建议与剩余规划.md`
- `21-黑箱Eval最小闭环实现记录.md`
- `v2修复文档.md`

这解决了 v3 之前“内部文档和可见目录不一致”的问题。

### 2.2 v2 测试结论已从绝对表述改为条件表述

检查文件：

- `docs/迭代修改/v2修复文档.md`
- `docs/迭代修改/19-v2审查修复记录.md`

现在已经写明：

- 核心 Agent 非 DB 测试：58 passed
- 当前沙箱宽范围测试：77 passed / 5 failed
- 失败集中在 MySQL 连接限制
- DB 依赖测试需 MySQL + Redis 环境复核

这比之前直接写 `82 passed` 严谨。

### 2.3 前端纠错日志失败可观测已补

检查文件：`bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue`

现在 `recordCorrection()` 失败会：

```js
console.warn('[correction] recordCorrection failed:', e)
```

这符合 v3 要求：不阻塞用户，但开发期能看到纠错闭环是否写入失败。

### 2.4 新增测试覆盖了不少关键逻辑

新增或增强文件：

- `tests/test_agent_memory_api.py`
- `tests/test_agent_confirmation_prompts.py`
- `tests/test_correction_memory.py`
- `tests/test_auth.py`

这些测试覆盖了：

- previous state 被 runtime 保存和读取
- `confirmation_prompts` 独立 issue 生成
- `CorrectionLogRequest` Pydantic 校验
- 注册昵称返回/保存逻辑

方向正确。

---

## 3. v4 必改问题

### V4-1：Eval 不能再称为完整黑箱端到端 Eval

严重度：高  
涉及文件：

- `docs/迭代修改/21-黑箱Eval最小闭环实现记录.md`
- `evals/runner.py`
- `evals/reports/latest.md`
- 后续答辩/说明文档

问题：

`evals/runner.py` 当前核心逻辑是：

```python
tools = ToolRegistry()

async def decision(state):
    ingredients = state.get("ingredients", [])
    ...
    return {"recipes": recipes}

tools.register("decision", decision)
agent = LangGraphAgent(tools=tools, max_steps=4)
result = await agent.run(...)
```

也就是说：

- 没有调用 `/v1/agent/execute`
- 没有走 `app/routers/agent.py`
- 没有真实读取用户画像、库存、收藏、纠错记忆
- 没有真实调用 `app/services/decision.py`
- 没有真实数据库推荐
- 没有真实 MemoryContext 构造

这不是完整黑箱 Eval。它是“mock 工具下的 Agent Runtime Eval 骨架”。

修改要求：

1. 所有文档中把当前 Eval 定性改为：

```text
离线 Eval P0 骨架 / mock runtime eval
```

不要写成：

```text
完整黑箱端到端 Eval
```

2. `21-黑箱Eval最小闭环实现记录.md` 增加边界声明：

```text
当前 quick Eval 使用 mock decision 工具，目标是验证 case 格式、runner、scorer、report 是否跑通，不代表真实推荐质量。真实黑箱 Eval 需要新增真实 API 模式。
```

3. `evals/reports/latest.md` 顶部增加：

```text
Mode: mock-runtime
注意：本报告未调用真实 /v1/agent/execute，不可作为真实用户满意度结论。
```

检查方式：

```bash
rg -n "完整黑箱|端到端|mock|Mode|/v1/agent/execute" docs/迭代修改/21-黑箱Eval最小闭环实现记录.md evals/reports/latest.md evals/runner.py
```

期望：

- 文档明确写出 mock 边界。
- 不再把当前 `42/42` 描述成真实端到端质量全通过。

---

### V4-2：Eval scorer 不能让 TOOL_ERROR / FAIL verdict 仍然 PASS

严重度：高  
涉及文件：

- `evals/scorer.py`
- `evals/cases/quick.jsonl`
- `evals/reports/latest.md`

问题：

当前报告中：

```text
Q05: termination_reason: TOOL_ERROR, evaluation verdict: FAIL — PASS
Q10: termination_reason: TOOL_ERROR, evaluation verdict: FAIL — PASS
```

这是严重评分漏洞。

原因是用例的 `expected_checks` 只检查：

```json
{"has_evaluation": true, "has_termination_reason": true, "events_non_empty": true}
```

只要有 termination_reason 就算通过，即使 reason 是 `TOOL_ERROR`。

修改要求：

1. 在 scorer 增加默认安全规则：

如果 case 没有显式允许失败，则以下情况必须算失败：

```text
termination_reason == "TOOL_ERROR"
status == "degraded"
evaluation verdict == "FAIL"
result.error 非空
```

2. JSONL 用例增加字段：

```json
"allow_failure": false
```

或默认 false。

3. 只有专门测试错误/降级的 case 才允许：

```json
"allow_failure": true
```

4. 对 Q05/Q10 二选一：

方案 A：修 mock 工具和用例，让它们不再产生 `TOOL_ERROR`。

方案 B：如果它们本来就是测试失败路径，expected_checks 必须明确写：

```json
"status": "degraded",
"termination_reason": "TOOL_ERROR"
```

并且 case 名称要改成“降级路径测试”，不能叫普通购物清单/多轮对话通过。

推荐方案 A。quick set 应主要证明正常路径稳定，不要混入伪通过的失败路径。

检查方式：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick
```

然后检查：

```bash
rg -n "TOOL_ERROR|evaluation verdict: FAIL|FAIL" evals/reports/latest.md
```

期望：

- 如果报告是 100%，不应出现 `TOOL_ERROR` 或 `evaluation verdict: FAIL`。
- 如果出现，必须在 failed cases 中体现。

---

### V4-3：补真实 API Eval 模式

严重度：高  
涉及文件：

- `evals/runner.py`
- `evals/cases/quick.jsonl`
- `evals/scorer.py`
- 可能新增 `evals/api_runner.py`

问题：

当前 Eval 没有走真实 API，因此无法回答“用户最终会不会满意”。

修改要求：

保留现有 mock 模式，但新增 `api` 模式。

建议命令：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode mock
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode api
```

`--mode api` 的 P0 实现可以不启动真实 HTTP 服务，直接用 FastAPI ASGI client 调 `/v1/agent/execute`：

```python
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)
async with AsyncClient(transport=transport, base_url="http://test") as client:
    resp = await client.post("/v1/agent/execute", json={...})
```

API 模式要求：

- 走 `app/routers/agent.py`
- 走真实 `build_memory_context()`
- 走真实 response schema
- 可以通过 monkeypatch 替换外部 VLM/LLM，但不要替换整个 Agent 工具链
- 对 DB 依赖做清晰处理：无 DB 环境时跳过 DB case，不要伪装通过

验收标准：

```text
mock mode: 验证 runner/scorer/report 框架
api mode: 验证真实 /v1/agent/execute 合同、events、memory_used、evaluation、confirmation_prompts
```

第一版 api quick set 可以只有 3 条：

1. 文本推荐：检查 recipes、reply、events、evaluation。
2. 缺图片识别：检查 needs_input、ask_user。
3. 同一 conversation 第二轮：检查 memory_used 或 conversation memory。

---

### V4-4：`MemoryContext API 级测试` 名称不准确

严重度：中  
涉及文件：

- `tests/test_agent_memory_api.py`

问题：

文件名和注释写的是：

```text
MemoryContext previous_state API级回归测试
```

但测试实际直接调用：

```python
agent = LangGraphAgent(...)
result = await agent.run(...)
```

没有调用 `/v1/agent/execute`，也没有经过 `app/routers/agent.py`。

所以它是 runtime 级测试，不是 API 级测试。

修改要求：

二选一：

方案 A：改名和注释，承认它是 runtime 级：

```text
tests/test_agent_memory_runtime.py
```

方案 B：补真正 API 级测试：

```python
resp = await client.post("/v1/agent/execute", json={...})
```

推荐方案 B。因为 v3 要证明的是路由层 previous_state 接入，这必须测 API。

检查方式：

```bash
rg -n "client.post\\(\"/v1/agent/execute\"|LangGraphAgent" tests/test_agent_memory_api.py
```

期望：

- 如果文件继续叫 `api`，必须出现 `client.post("/v1/agent/execute"`。
- 如果只调 `LangGraphAgent`，文件名和文档都要改成 runtime。

---

### V4-5：`CorrectionLogRequest 422 测试` 实际不是 API 422

严重度：中  
涉及文件：

- `tests/test_correction_memory.py`

问题：

v3 完成报告写：

```text
CorrectionLogRequest 422 测试 ✅ 6 tests
```

但当前测试是：

```python
with pytest.raises(ValidationError):
    CorrectionLogRequest(action="drop_table", source="sense")
```

这是 Pydantic schema 单测，不是 API 422 测试。

修改要求：

二选一：

方案 A：改报告口径为：

```text
CorrectionLogRequest Pydantic 校验测试
```

方案 B：补真正 API 422：

```python
resp = await client.post(
    "/v1/correction-logs",
    headers=headers,
    json={"action": "drop_table", "source": "sense"}
)
assert resp.status_code == 422
```

推荐方案 B，但要避免依赖真实 DB。因为 422 发生在 FastAPI body validation 阶段，理论上可以在进入 DB dependency 前返回。如果当前 auth dependency 先要求 token，可以构造合法 token 或 override auth。

检查方式：

```bash
rg -n "422|/v1/correction-logs|ValidationError" tests/test_correction_memory.py tests
```

期望：

- 如果报告写 API 422，测试里必须有真实 HTTP 请求和 `assert resp.status_code == 422`。

---

### V4-6：`tests/test_auth.py` 有重复测试函数名

严重度：中  
涉及文件：

- `tests/test_auth.py`

问题：

文件中出现了两个同名函数：

```python
async def test_profile_with_token(client):
    ...

async def test_profile_with_token(client):
    ...
```

Python 后定义会覆盖前定义，前一个测试不会被 pytest 收集。

修改要求：

把后一个改名，例如：

```python
async def test_profile_update_with_custom_targets(client):
```

检查方式：

```bash
rg -n "async def test_profile_with_token" tests/test_auth.py
```

期望：

只出现一次。

补充检查：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest --collect-only -q tests/test_auth.py
```

确认两个测试都被收集。

---

### V4-7：测试结果必须给精确命令，不能只报数字

严重度：中  
涉及文件：

- v3 完成报告
- `docs/迭代修改/21-黑箱Eval最小闭环实现记录.md`
- 后续所有修复记录

问题：

v3 完成报告写：

```text
核心非 DB 测试 89 passed
```

但没有给出精确命令。我复跑 v3 文档中最相关的核心集合得到：

```text
71 passed
```

更宽集合得到：

```text
80 passed, 1 failed
```

因此 `89 passed` 目前不可复现。

修改要求：

后续所有测试结论统一格式：

```text
命令：
<完整命令>

结果：
<pytest summary 原文>

说明：
<是否依赖 MySQL/Redis/外部 API>
```

不要只写：

```text
89 passed
```

检查方式：

```bash
rg -n "passed|Build complete|42/42|100%" docs/迭代修改
```

每个结论附近都应能看到对应命令或明确引用。

---

## 4. v4 建议补强项

### V4-8：Eval case 需要记录真实输入上下文

当前 `quick.jsonl` 主要是：

```json
{"input":"牛肉南瓜减脂30分钟","conversation_id":"eval_q01","expected_checks":...}
```

这还不是我们之前定义的完整 Eval case。后续应逐步扩展为：

```json
{
  "case_id": "Q01",
  "name": "老用户减脂晚餐推荐",
  "context": {
    "user_id": "eval_user_001",
    "preference_memory": {
      "avoid_ingredients": ["香菜"],
      "health_goal": "fat_loss"
    },
    "inventory": [
      {"name": "牛肉", "quantity": 200, "unit": "g"},
      {"name": "南瓜", "quantity": 1, "unit": "块"}
    ],
    "conversation_history": []
  },
  "current_input": {
    "text": "牛肉南瓜减脂30分钟",
    "image": null
  },
  "expected_checks": {...}
}
```

P0 可以兼容旧格式，但新格式要开始支持，否则后续很难升级到真正黑箱 Eval。

### V4-9：Eval report 要区分框架分和质量分

当前 scorer 只检查结构字段：

- 有 recipes
- reply 非空
- 有 evaluation
- 有 termination_reason
- 有 phase

这些是“框架分”，不是“用户满意度质量分”。

建议报告分两栏：

```text
framework_score: events / termination / schema / no tool error
quality_score: ingredient coverage / preference obey / nutrition / actionability
```

mock mode 可以只给 framework_score。api mode 才逐步给 quality_score。

### V4-10：Q09 空输入不应轻易 PASS

当前 Q09：

```json
"input": "",
"expected_checks": {"has_evaluation": true, "has_termination_reason": true}
```

空输入如果返回 `GOAL_ACHIEVED` 也会 PASS。更合理的期望是：

- `status == "needs_input"`，或
- 有 `ask_user` event，或
- termination_reason 是 `NEEDS_INPUT`

修改建议：

```json
"expected_checks": {
  "status": "needs_input",
  "has_ask_user_event": true,
  "has_termination_reason_needs_input": true
}
```

如果当前 planner 还不能处理空输入，应记录为待修，而不是让 Eval 放水。

---

## 5. v4 给子 Agent 的明确修改任务

### Task 1：修 Eval scorer 的失败默认规则

必须完成：

- `TOOL_ERROR` 默认失败。
- `evaluation verdict == FAIL` 默认失败。
- `status == degraded` 默认失败，除非 case 显式 `allow_failure: true`。
- `result.error` 非空默认失败。

验收：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick
rg -n "TOOL_ERROR|evaluation verdict: FAIL" evals/reports/latest.md
```

如果报告仍显示 100%，不应出现 `TOOL_ERROR` 或 `evaluation verdict: FAIL`。

### Task 2：修 Q05/Q10/Q09 用例

必须完成：

- Q05 不得普通 PASS 但内部 `TOOL_ERROR`。
- Q10 不得普通 PASS 但内部 `TOOL_ERROR`。
- Q09 空输入不能只检查有 termination_reason。

验收：

```bash
cat evals/reports/latest.md
```

人工确认：

- Q05 正常成功，或明确标为降级路径。
- Q10 真正验证多轮，或改名为当前能验证的场景。
- Q09 触发澄清或被列为失败。

### Task 3：增加 Eval mode

必须完成：

```bash
evals/runner.py --quick --mode mock
evals/runner.py --quick --mode api
```

P0 的 api mode 可以只跑 3 条 case，但必须走 `/v1/agent/execute`。

验收：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode api
```

报告必须写：

```text
Mode: api
```

### Task 4：修测试命名和 API 级测试口径

必须完成：

- `tests/test_agent_memory_api.py` 要么真的调 API，要么改名为 runtime。
- `CorrectionLogRequest 422` 要么真的测 API 422，要么报告改成 Pydantic 校验。
- `tests/test_auth.py` 重复 `test_profile_with_token` 改名。

验收：

```bash
rg -n "async def test_profile_with_token" tests/test_auth.py
rg -n "client.post\\(\"/v1/agent/execute\"" tests/test_agent_memory_api.py
rg -n "status_code == 422|/v1/correction-logs" tests
```

### Task 5：补 v4 修复文档

新增：

```text
docs/迭代修改/23-v4修复文档.md
```

并同步到：

```text
！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/23-v4修复文档.md
```

文档必须包含：

- 每个 V4 item 的修复说明。
- 精确测试命令。
- 精确测试结果。
- Eval mock/api 两种模式的区别。
- 如果某项未做，写明原因和下一步。

---

## 6. 当前规划状态更新

### 已经比较稳的部分

- Agent runtime 事件模型。
- Hard Evaluator 基础规则。
- MemoryContext 基础结构。
- memory_used 返回和前端展示。
- 前端假进度和 events 回放。
- 文档同步机制。
- Eval runner/scorer/report 的最小骨架。

### 仍然不稳的部分

- Eval 分数不能识别内部 `TOOL_ERROR`。
- Eval 仍是 mock runtime，不是真实 API 黑箱。
- 测试报告数字缺少精确命令。
- 部分“API 级测试”实际是 runtime/schema 测试。
- DB 依赖测试在当前环境仍未可复现。

### 下一步真正要达成的状态

```text
mock Eval 证明框架稳定
api Eval 证明接口合同稳定
DB integration tests 证明真实数据链路稳定
后续 LLM Judge 证明软质量评估可用
```

现在只完成了第一步的一半：mock Eval 框架跑通，但 scorer 还需要修正。

---

## 7. 最终判断

v3 的方向是对的，但不要急着把它包装成“完整黑箱 Eval 已完成”。当前更准确的说法是：

> ByteSavor 已经具备离线 Eval 的最小工程骨架，可以加载 case、执行 mock runtime、打分并生成报告。下一步需要修正 scorer 对失败路径的识别，并新增真实 API mode，才能逐步接近真正的黑箱端到端 Eval。

双 Agent / DeepSeek Judge 仍然建议保留，但必须排在这两件事之后：

1. deterministic scorer 不再放过 `TOOL_ERROR`。
2. API mode 能真实调用 `/v1/agent/execute`。

否则 LLM Judge 会建立在不稳的评估底座上，分数看起来更高级，但可信度更差。
