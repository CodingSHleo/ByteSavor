# ByteSavor Agent 规范化迭代修改总览

日期：2026-06-19 ~ 2026-06-21 (v1-v5)  
最新基线：v5 复审后基线（账号/社区已修复，Eval API 与社区 API 冒烟已验证）

## 当前推荐阅读顺序

1. `23-v3最终复核报告_MySQL已验证.md`：v3 基线、已完成项、剩余规划。
2. `24-Eval_API_Mode_与测试收口修复文档.md`：Eval mock/api、测试收口和最终验证结果。
3. `v5/README.md`：v5 任务包入口和执行规则。
4. `v5/01-v5基础工程化任务书_给Subagent.md`：当前轮工程化任务。
5. `v5/03-v5账号登录与用户数据库完善任务书_给Subagent.md`：账号密码登录。
6. `v5/02-v5社区模块完善任务书_给Subagent.md`：社区完善。
7. `31-v5复审修复记录.md`：复审 subagent v5 后实际修复的问题。
8. `32-v5继续复核_EvalAPI与社区冒烟.md`：Eval API 与社区真实 API 冒烟验证。

## 当前验证命令

快速验证（非DB测试 + Eval mock + H5构建）：
```bash
./scripts/verify_quick.sh
```

DB验证（需MySQL/Redis）：
```bash
./scripts/verify_db.sh
```

Eval API验证（需后端运行在8000）：
```bash
./scripts/verify_eval_api.sh
```

## 当前基线

| 项目 | 结果 |
|------|------|
| 核心非 DB 测试 | 84 passed, 1 skipped |
| DB 依赖测试 | 39 passed |
| Eval mock | 72/72 (100%) |
| Eval api | 72/72 (100%) |
| H5 构建 | DONE Build complete |
| 社区 API 冒烟 | ok: true |

## 当前边界

- Eval mock/api quick 已通过，但还不是完整 30-50 条黄金用例体系
- DeepSeek Judge 尚未接入
- Alembic 尚未接入
- Browser/Playwright 页面点击级 smoke 尚未完成；已完成 H5 dev server 可达 + 社区真实 API 冒烟
- 本地 CNN/ONNX 降级已明确不做

---

## 修改总量（原始记录）

| 类型 | 数量 |
|------|------|
| 新增文件 | 10 个（5 源码 + 5 测试） |
| 修改文件 | 11 个 |
| 修改文档 | 11 篇 |
| 测试通过 | 48 个（39 新增 + 9 已有回归） |

---

## 一、模块一：MemoryContext 统一记忆上下文

**新增文件**：
- `app/services/agent_memory.py` — `build_memory_context()` / `build_memory_used()`
- `tests/test_agent_memory_context.py` — 7 个测试

**修改文件**：
- `app/agent/state.py` — AgentState 增加 `memory_context` / `memory_used` / `sense_result` 字段
- `app/routers/agent.py` — 使用 agent_memory 服务组装记忆，返回 memory_used
- `app/agent/runtime.py` — run() 接收 memory_context 参数
- `app/agent/langgraph_runtime.py` — run() 接收 memory_context 参数

**效果**：Agent 每次请求自动读取偏好/库存/餐食/纠错四层记忆，返回 `memory_used` 说明参考了哪些记忆。
格式：`[{type, key, summary}]`

**详细文档**：`04-memory-context.md`, `09-agent-memory-service.md`

---

## 二、模块二：Hard Evaluator 硬规则评估层

**新增文件**：
- `app/agent/evaluator.py` — `evaluate_hard()` / `EvaluationResult`
- `tests/test_agent_evaluator.py` — 8 个测试

**修改文件**：
- `app/agent/langgraph_runtime.py` — 新增 `evaluator_node`，图结构增加评估节点
- `app/agent/runtime.py` — `_finish_run()` 中调用 evaluator

**实现规则**：

| 条件 | verdict | issue code |
|------|---------|------------|
| 推荐列表为空 | FAIL | NO_RECIPE |
| 核心食材覆盖率 0% | FAIL | CORE_INGREDIENT_MISSED |
| 核心食材覆盖率 < 50% | CONFLICT | CORE_INGREDIENT_MISSED |
| 识别置信度 < 0.5 | PARTIAL | LOW_CONFIDENCE_INGREDIENT |
| 工具异常 | FAIL | TOOL_ERROR |
| 需用户确认（口味等） | PARTIAL | NEEDS_USER_CONFIRMATION |

**evaluation event 格式**：
```json
{"type": "evaluation", "phase": "EVALUATING", "tool": "decision",
 "verdict": "PASS", "issues": [{"code": "...", "message": "..."}], "suggestions": [...]}
```

**详细文档**：`01-hard-evaluator-phase-termination.md`, `08-evaluator-format-fix.md`

---

## 三、模块三：Loop Engineering 规范化

**新增测试**：
- `tests/test_agent_loop_engineering.py` — 6 个测试

**修改文件**：
- `app/agent/langgraph_runtime.py` — events 全部增加 phase，返回 termination_reason
- `app/agent/runtime.py` — events 全部增加 phase，返回 termination_reason

**phase 枚举**：INIT / ROUTING / EXECUTING / EVALUATING / CLARIFYING / FINISHED / ERROR

**termination_reason 枚举**：
- `GOAL_ACHIEVED` — 正常完成
- `NEEDS_INPUT` — 需要用户补充
- `TOOL_ERROR` — 工具错误
- `MAX_STEPS` — 超过最大步数
- `PARTIAL_SUCCESS` — 部分成功

**LangGraph 图结构更新**：
```
START → planner → [tool → planner 循环] / ask_user / evaluator → final → END
```

**详细文档**：`01-hard-evaluator-phase-termination.md`, `11-runtime-phase-fix-tests.md`

---

## 四、模块四：推荐一致性与记忆解释

**新增测试**：
- `tests/test_decision_memory_matching.py` — 7 个测试

**修改文件**：
- `app/services/decision.py` — 新增 `MEMORY_MATCH`、`INVENTORY_MATCH` 推荐理由码
- `app/agent/evaluator.py` — 核心食材覆盖率检查（50% 规则）

**50% 规则**：
- 2 个食材 → 至少覆盖 1 个
- 3 个食材 → 至少覆盖 2 个

**详细文档**：`02-decision-reason-codes.md`

---

## 五、模块五：识别纠错记忆

**新增文件**：
- `app/services/food_synonyms.py` — 60+ 组同义词映射 + 置信度分级
- `app/services/correction_logs.py` — 纠错日志服务
- `app/routers/correction_logs.py` — 纠错日志 API
- `tests/test_correction_memory.py` — 11 个测试

**修改文件**：
- `app/models/__init__.py` — 新增 `CorrectionLog` 模型
- `app/services/vlm/__init__.py` — VLM 后处理管线
- `app/main.py` — 注册 correction_logs 路由

**CorrectionLog 表字段**：id, user_id, source, original_name, corrected_name, action, confidence, meta, created_at

**API**：
- `POST /v1/correction-logs` — 记录纠错
- `GET /v1/correction-logs` — 查询纠错历史

**详细文档**：`03-food-synonyms-confidence.md`, `07-correction-logs.md`, `10-correction-logs-field-alignment.md`

---

## 六、稳定性改进

**VLM/LLM 超时**：
- `app/core/config.py` — 新增 `vlm_timeout_sec=20`, `llm_timeout_sec=15`
- `app/services/vlm/openai.py` — timeout 120s → 20s
- `app/services/feedback.py` — timeout 60s → 15s

**图片缓存**：
- `app/services/vlm/__init__.py` — md5 hash + Redis 30min 缓存

**详细文档**：`05-vlm-llm-timeout.md`, `06-image-hash-cache.md`

---

## 七、修改文件清单

### 新增文件（10个）

| 文件 | 类型 |
|------|------|
| `app/agent/evaluator.py` | 源码 |
| `app/services/agent_memory.py` | 源码 |
| `app/services/food_synonyms.py` | 源码 |
| `app/services/correction_logs.py` | 源码 |
| `app/routers/correction_logs.py` | 源码 |
| `tests/test_agent_evaluator.py` | 测试 |
| `tests/test_agent_memory_context.py` | 测试 |
| `tests/test_agent_loop_engineering.py` | 测试 |
| `tests/test_decision_memory_matching.py` | 测试 |
| `tests/test_correction_memory.py` | 测试 |

### 修改文件（11个）

| 文件 | 关键变更 |
|------|---------|
| `app/agent/state.py` | +memory_context, +memory_used, +sense_result |
| `app/agent/langgraph_runtime.py` | +evaluator_node, events+phase, +termination_reason |
| `app/agent/runtime.py` | +_finish_run, events+phase, evaluator集成 |
| `app/routers/agent.py` | 使用agent_memory服务, decision传入avoid信号 |
| `app/services/vlm/__init__.py` | 同义词后处理 + 图片缓存 |
| `app/services/vlm/openai.py` | timeout 120s→20s |
| `app/services/decision.py` | +MEMORY_MATCH, +INVENTORY_MATCH |
| `app/services/feedback.py` | timeout 60s→15s |
| `app/core/config.py` | +vlm_timeout_sec, +llm_timeout_sec |
| `app/models/__init__.py` | +CorrectionLog 模型 |
| `app/main.py` | +correction_logs 路由注册 |

---

## 八、测试命令

```bash
# 全部新增测试
JWT_SECRET=test-secret python -m pytest -q \
  tests/test_agent_evaluator.py \
  tests/test_agent_memory_context.py \
  tests/test_agent_loop_engineering.py \
  tests/test_decision_memory_matching.py \
  tests/test_correction_memory.py

# 已有回归测试
JWT_SECRET=test-secret python -m pytest -q \
  tests/test_agent_runtime.py \
  tests/test_langgraph_agent.py \
  tests/test_agent_tools_inventory_favorites.py
```
