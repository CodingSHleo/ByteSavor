# 修改文档 24：Eval API Mode 与测试收口修复

日期：2026-06-20  
依据：`23-v3最终复核报告_MySQL已验证.md` Section 6.6

## 修复清单

### 1. Eval scorer 不放过 TOOL_ERROR / FAIL / degraded

**修改文件**：`evals/scorer.py`

**问题**：scorer 只检查 case 显式声明的 `expected_checks`，不检查 Agent 内部失败信号。导致出现过 `TOOL_ERROR` / `evaluation verdict=FAIL` 但仍 100% 通过的报告。

**修改**：新增 3 个默认检查：
- `termination_reason == "TOOL_ERROR"` → 失败
- `evaluation verdict == "FAIL"` → 失败
- `status == "degraded"` → 失败
- 除非 case 显式设置 `allow_failure: true`

**检查命令**：
```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode mock
```
**结果**：72/72 (100%)

### 2. Eval runner 增加 --mode api

**修改文件**：`evals/runner.py`

**新增参数**：
- `--mode mock` (默认)：使用内嵌 LangGraphAgent + mock 工具
- `--mode api`：真实 HTTP 请求 `/v1/agent/execute`
- `--api-base`：API 地址 (默认 http://127.0.0.1:8000)
- `--prefix`：报告文件名前缀

**用法**：
```bash
# mock 模式（不需后端运行）
venv/bin/python evals/runner.py --quick --mode mock

# api 模式（需后端运行）
venv/bin/python evals/runner.py --quick --mode api --api-base http://127.0.0.1:8000
```

**Mock 模式工具**：注册 decision + task，返回基于输入食材的推荐和清单。

**API 模式最终验证**：

先确认 8000 上运行的是当前代码。如果端口上是旧进程，需要先停止并重启：

```bash
lsof -iTCP:8000 -sTCP:LISTEN -n -P
kill <旧 PID>
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

再运行：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python evals/runner.py --quick --mode api --prefix latest-api
```

**结果**：72/72 (100%)

说明：此前 api mode 一度只有 53/72，根因是 8000 端口上仍运行旧后端进程，返回 events 缺少 `phase`、`evaluation`、`termination_reason`。重启为当前代码后已通过。

### 3. 补 /v1/agent/execute API 级 previous_state 测试

**修改文件**：`tests/test_agent_memory_api.py`

**新增测试**：
- `test_api_agent_returns_memory_context`：真实 `/v1/agent/execute` 返回需包含 `memory_context` 和 `memory_used`
- `test_api_agent_second_round_sees_previous`：同一 `conversation_id` 第二轮应能通过 `memory_used` 或 `memory_context.conversation_memory` 看到上一轮信息

**检查命令**：
```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_agent_memory_api.py -v
```
**结果**：4 passed

### 4. 补 /v1/correction-logs 422 API 测试

**修改文件**：`tests/test_correction_memory.py`

**新增测试**：
- `test_correction_api_rejects_invalid_action`：非法 action → HTTP 422
- `test_correction_api_rejects_invalid_source`：非法 source → HTTP 422
- `test_correction_api_accepts_valid_request`：合法请求 → HTTP 200（需 MySQL）

**补充修复**：422 测试不再通过 `/v1/auth/register` 获取 token。注册接口会访问 MySQL，导致“非 DB 测试”在普通沙箱中失败。现在测试直接用 `create_token()` 生成合法 JWT，仍然走真实 HTTP API 和 Pydantic body 校验，但不依赖 MySQL。

**检查命令**：
```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q tests/test_correction_memory.py::test_correction_api_rejects_invalid_action tests/test_correction_memory.py::test_correction_api_rejects_invalid_source -v
```
**结果**：2 passed

### 5. 修复 test_auth.py 重复函数名

**修改文件**：`tests/test_auth.py`

**问题**：`test_profile_with_token` 和 `test_profile_targets_use_body_metrics_and_custom_override` 重复（编辑错误导致）。

**修复**：恢复正确的函数名。

## 最终测试结果

| 类型 | 结果 |
|------|------|
| 核心非 DB 测试 | 84 passed, 1 skipped |
| Eval mock | 72/72 (100%) |
| Eval api | 72/72 (100%) |
| H5 构建 | DONE Build complete |
| 422 API 测试 | 2 passed |
| MemoryContext API 测试 | 4 passed |
| DB 依赖集合 | 24 passed |

## 剩余已知边界

| 项目 | 状态 |
|------|------|
| Eval api mode 真实运行 | 已通过；前提是 8000 运行当前代码 |
| test_correction_api_accepts_valid_request | 仍 skip，因普通沙箱不应访问 MySQL；DB 集合另跑 |
| test_auth.py 完整 DB 集合 | 沙箱外已验证，DB 依赖集合 24 passed |

## 最终复核命令

核心非 DB：

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
84 passed, 1 skipped
```

DB 依赖：

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
24 passed
```

前端：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

结果：

```text
DONE Build complete
```
