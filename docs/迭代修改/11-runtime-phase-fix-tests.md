# 修改文档 11：AgentRuntime phase/termination 补齐 + 测试文件 + 覆盖率修复

## 修改日期

2026-06-20

## 文件变更

### 1. 修改 `app/agent/runtime.py`

**AgentRuntime.run()** 中所有 events 增加 `phase` 字段：
- plan → phase: ROUTING
- tool_start/tool_result → phase: EXECUTING  
- ask_user → phase: CLARIFYING
- final → phase: FINISHED
- tool_result 增加 `retry_count: 0`

新增 `_finish_run()` 方法：统一处理完成流程（生成 final 事件 → 硬规则评估 → 返回结果）。

`_result()` 方法：
- 新增第 4 参数 `termination_reason`
- 结果中新增 `outcome`、`termination_reason`、`next_action`（兼容旧字段）

### 2. 修改 `app/agent/evaluator.py`

**`_count_core_ingredient_coverage()`** 修复：
- 除了检查 `ingredients` 字段，也检查 `title` 字段
- 避免菜谱标题如"牛肉南瓜饭"明明覆盖了食材却因缺少 ingredients 字段被判为未覆盖

### 3. 新增 5 个测试文件

| 文件 | 测试数 | 覆盖内容 |
|------|--------|---------|
| `tests/test_agent_evaluator.py` | 8 | PASS/PARTIAL/FAIL/CONFLICT 四种 verdict，NO_RECIPE/CORE_INGREDIENT_MISSED/LOW_CONFIDENCE_INGREDIENT/TOOL_ERROR/NEEDS_USER_CONFIRMATION 五种 issue code |
| `tests/test_agent_memory_context.py` | 7 | memory_used 格式（type/key/summary），空上下文，会话/偏好/库存/纠错各层 |
| `tests/test_agent_loop_engineering.py` | 6 | events phase 字段，termination_reason，max_steps 边界，ask_user，evaluation 事件 |
| `tests/test_decision_memory_matching.py` | 7 | 推荐理由码，核心食材覆盖率全/部分/零覆盖，50% 规则（2 食材和 3 食材场景） |
| `tests/test_correction_memory.py` | 11 | 同义词映射，同名合并，低置信标记，置信度标签，字符串解析，肉类分类 |

### 4. 修改已有测试

`tests/test_agent_runtime.py`：
- 更新事件类型断言，增加 evaluation 事件检查

### 测试结果

全部 48 个测试通过（39 个新增 + 9 个已有回归测试）。
