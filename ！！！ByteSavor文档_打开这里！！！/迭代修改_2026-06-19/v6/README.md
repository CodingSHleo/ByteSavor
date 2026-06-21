# ByteSavor v6 任务包

这个文件夹是给 subagent 的 v6 执行入口。

v6 的核心目标不是继续堆功能，而是把 ByteSavor 的创新点打出来：

> ByteSavor 是一个可审查、可降级、可评估、可观测的多模态饮食 Agent 工业化框架。

当前系统已经能跑，但创新点还不够突出。v6 要围绕以下 6 个必须完成的工业化短板推进：

1. `SkillDescriptor` 不能只做元数据，必须约束 ToolRegistry 和 planner。
2. planner 不能只是硬编码关键词，要有 descriptor 候选工具生成，并预留 DeepSeek planner。
3. Skill 必须有统一输入校验、超时、重试、错误码。
4. Skill 事件必须更可观测，能展示 latency、cache、model、retry、degraded。
5. `sense` 不能因为没配 `vlm_api_url` 就彻底消失，至少要能注册并返回明确 unavailable/needs_config。
6. DeepSeek 不能只在 assistant/chat 使用，要成为可选 planner/rerank/judge，但不能绕过数据库和硬规则。

---

## 执行顺序

### 第 1 步：Skill 工业化底座

任务书：

- `01-v6-Skill工业化底座任务书_给Subagent.md`

先做这一份。它是后面所有创新点的底座。

重点：

- ToolRegistry 绑定 SkillDescriptor。
- Skill 统一 wrapper。
- 事件增加 descriptor 信息、latency、error_code。
- `sense` 始终注册。

### 第 2 步：LLM Planner / Judge 边界

任务书：

- `02-v6-LLMPlanner与Judge任务书_给Subagent.md`

重点：

- DeepSeek 只能在候选工具里选下一步。
- LLM planner 失败必须回退规则 planner。
- Judge 只做软性评估，不阻断主流程。

### 第 3 步：VL 速度优化

任务书：

- `03-v6-VL速度与缓存任务书_给Subagent.md`

重点：

- 后端 VL 缓存 key 加模型和 prompt 版本。
- 返回 `cache_hit/latency_ms/model/cache_key/image_fingerprint`。
- 前端识别页展示压缩、缓存、耗时。

### 第 4 步：前端创新点展示与验收

任务书：

- `04-v6-前端可解释展示与验收任务书_给Subagent.md`

重点：

- 推荐卡展示已有食材、补买建议、偏好命中。
- Agent 时间线展示 planner/skill/evaluator。
- 写真实手工验收清单。

---

## 执行规则

1. 不要四份任务同时改。
2. 每完成一份必须写修复记录，并同步到：
   - `docs/迭代修改/`
   - `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/`
3. 每份修复记录必须包含：
   - 修改文件；
   - 修改前问题；
   - 修改后逻辑；
   - 验证命令；
   - 验证结果；
   - 未完成项。
4. 不允许写“全部完成”但不给命令。
5. 不允许把 mock Eval 说成完整黑箱 Eval。
6. 不允许让 DeepSeek 编造数据库不存在的菜谱。
7. 不允许新增本地 CNN/ONNX 降级模型。
8. 不允许引入 WebSocket，除非主 agent 明确要求。
9. 不要破坏当前已通过的用户实测修复：
   - `牛肉韭黄` 不首推 `芹菜炒牛肉`；
   - `韭黄炒蛋` 能搜到 `韭黄炒鸡蛋`；
   - 刷新推荐传 `refresh=true`；
   - 社区点赞/收藏 toggle；
   - 菜谱库收藏 toggle；
   - 偏好参与推荐和搜索。

---

## 当前验证基线

这些命令在 v6 开始前已通过：

```bash
node scripts/verify_frontend_regressions.mjs
```

```text
frontend regressions ok
```

```bash
cd bsapp
npm run build:h5
```

```text
DONE Build complete.
```

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_decision.py tests/test_community.py tests/test_favorites.py tests/test_community_recipe_flow.py
```

```text
20 passed
```

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_agent.py tests/test_agent_runtime.py tests/test_agent_evaluator.py \
  tests/test_decision_memory_matching.py tests/test_feedback_memory.py tests/test_agent_memory_context.py
```

```text
37 passed
```

---

## v6 最终答辩口径

v6 做完后，答辩不要说“我们只是调了 DeepSeek 和千问”。

应该说：

> 我们把饮食推荐拆成了感知、决策、执行、评估四类 Skill，每个 Skill 都有描述、输入输出、超时、事件、评估和降级。DeepSeek 不是直接乱生成结果，而是在数据库候选和规则约束之上做规划、重排和软评审；千问 VL 负责感知，并通过压缩、缓存和阶段反馈降低用户感知等待。ByteSavor 的创新点是把通用大模型封装进一个可审查、可恢复、可评估的工业化 Agent 框架。

