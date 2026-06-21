# ByteSavor v5 基础工程化任务书（给 Subagent）

日期：2026-06-20  
执行对象：subagent  
审查人：主 agent / 项目负责人  
任务性质：基础工程化收口，不做新业务功能  

---

## 0. 当前基线

在开始 v5 前，当前项目已完成以下基线：

| 项目 | 当前结果 |
|---|---:|
| 核心非 DB 测试 | `84 passed, 1 skipped` |
| DB 依赖测试 | `24 passed` |
| Eval mock | `72/72 (100%)` |
| Eval api | `72/72 (100%)` |
| H5 构建 | `DONE Build complete` |
| 文档同步 | `docs/迭代修改` 与可见目录已同步到 24 |

重要说明：

1. 普通沙箱不能直接连接本机 MySQL，DB 测试需要使用允许访问本机 MySQL 的执行环境。
2. `Eval --mode api` 必须确认 8000 端口运行的是当前代码。如果端口上是旧后端进程，Eval 会出现缺少 `phase / evaluation / termination_reason` 的假失败。
3. 当前 Eval 已有 mock/api 两种模式，但仍是 quick set，不等于完整 30-50 条黄金用例体系。

---

## 1. v5 总目标

v5 不做新业务功能，不新增页面，不改推荐算法主逻辑。

v5 只做四件基础工程化工作：

1. **测试命令标准化**：把非 DB、DB、Eval、H5 的验证命令固化成脚本，避免每轮靠人工复制长命令。
2. **pytest 分层标记**：给 DB 依赖测试加明确 marker，让 quick 测试和 DB 测试边界清楚。
3. **Eval API 运行守卫**：避免 subagent 再拿旧后端进程跑出错误结论。
4. **文档索引和交接说明**：更新 README/索引，让后来的人知道看到哪篇、跑哪些命令、哪些不该做。

验收标准：

```text
./scripts/verify_quick.sh        -> 通过，输出核心非 DB 测试 + Eval mock + H5 build
./scripts/verify_eval_api.sh     -> 启动/检查当前 API 后 Eval api 72/72
./scripts/verify_db.sh           -> 在 MySQL 可访问环境下 DB 测试通过
pytest --collect-only            -> 不出现重复测试名问题
docs/迭代修改/README.md           -> 包含 v5 后的阅读顺序和验证命令
```

---

## 2. 严禁事项

subagent 必须遵守：

1. 不要再改业务页面 UI。
2. 不要新增 CNN/ONNX 本地模型。
3. 不要引入 WebSocket。
4. 不要让 LLM Judge 阻断主流程。
5. 不要把 mock Eval 说成完整黑箱 Eval。
6. 不要写“全部通过”但不给完整命令。
7. 不要用 `rm -rf`、`git reset --hard`、`git checkout --`。
8. 不要修改用户未要求的旧文档大段内容，只补索引和必要状态。
9. 不要在测试里为了拿 token 访问 MySQL，除非该测试本身就是 DB 集成测试。
10. 不要留下正在运行的后端进程占用 8000。

---

## 3. 文件责任图

本轮建议新增/修改以下文件：

| 文件 | 操作 | 责任 |
|---|---|---|
| `pytest.ini` | 新增或修改 | 定义 pytest markers：`db`, `eval`, `frontend` |
| `scripts/verify_quick.sh` | 新增 | 跑核心非 DB 测试、Eval mock、H5 build |
| `scripts/verify_db.sh` | 新增 | 跑 DB 依赖测试集合 |
| `scripts/verify_eval_api.sh` | 新增 | 检查/提示 8000 后端，跑 Eval api |
| `docs/迭代修改/README.md` | 修改 | 更新阅读顺序、验证命令、当前状态 |
| `docs/迭代修改/26-v5基础工程化修复记录.md` | 新增 | 记录本轮实际修改和结果 |
| `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/26-v5基础工程化修复记录.md` | 新增同步 | 可见目录副本 |

如果已有 `pytest.ini`，只追加 markers，不要覆盖其他配置。

---

## 4. Task 1：添加 pytest markers

### 目标

让测试分层清楚：

- quick：普通沙箱可跑，不依赖 MySQL。
- db：需要 MySQL/Redis 或真实 DB。
- eval：Eval runner 相关。

### 文件

- 新增或修改：`pytest.ini`
- 修改测试文件：
  - `tests/test_auth.py`
  - `tests/test_decision.py`
  - `tests/test_meals_inventory.py`
  - `tests/test_feedback_memory.py`
  - `tests/test_inventory_stats.py`
  - `tests/test_recipe_checker.py`
  - `tests/test_favorites.py`
  - `tests/test_community.py`
  - `tests/test_community_recipe_flow.py`
  - `tests/test_agent_tools_inventory_favorites.py`

### 具体要求

如果没有 `pytest.ini`，创建：

```ini
[pytest]
markers =
    db: tests that require MySQL/Redis or persistent database access
    eval: offline evaluation runner tests or eval-related checks
    frontend: frontend smoke/build checks
asyncio_mode = auto
```

如果已有 `pytest.ini`，保留原内容，只加入缺失 marker。

给 DB 依赖测试文件加：

```python
pytestmark = pytest.mark.asyncio(loop_scope="session")
pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]
```

如果文件已有 `pytestmark = pytest.mark.asyncio(...)`，改成 list。不要删除原 async mark。

### 检查命令

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest --collect-only -q
```

期望：

- 能正常 collect。
- 没有 unknown marker warning。
- `tests/test_auth.py` 不再出现重复函数覆盖问题。

---

## 5. Task 2：新增 quick 验证脚本

### 目标

把最常跑的验证命令固化为一个脚本。

### 文件

- 新增：`scripts/verify_quick.sh`

### 脚本内容

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor quick verification =="
echo "ROOT=$ROOT"

echo
echo "== 1. Core non-DB tests =="
"$PY" -m pytest -q \
  "$ROOT/tests/test_agent_evaluator.py" \
  "$ROOT/tests/test_agent_memory_context.py" \
  "$ROOT/tests/test_agent_loop_engineering.py" \
  "$ROOT/tests/test_decision_memory_matching.py" \
  "$ROOT/tests/test_correction_memory.py" \
  "$ROOT/tests/test_agent_runtime.py" \
  "$ROOT/tests/test_langgraph_agent.py" \
  "$ROOT/tests/test_nutrition_calculator.py" \
  "$ROOT/tests/test_agent_memory_api.py" \
  "$ROOT/tests/test_agent_confirmation_prompts.py" \
  "$ROOT/tests/test_agent.py" \
  "$ROOT/tests/test_food_guide.py"

echo
echo "== 2. Eval mock =="
"$PY" "$ROOT/evals/runner.py" --quick --mode mock

echo
echo "== 3. H5 build =="
(
  cd "$ROOT/bsapp"
  npm run build:h5
)

echo
echo "== quick verification passed =="
```

### 权限

执行：

```bash
chmod +x scripts/verify_quick.sh
```

### 检查命令

```bash
./scripts/verify_quick.sh
```

期望：

```text
核心非 DB 测试通过
Eval mock 72/72
H5 DONE Build complete
== quick verification passed ==
```

---

## 6. Task 3：新增 DB 验证脚本

### 目标

DB 测试需要 MySQL/Redis 环境，单独脚本执行，避免混进 quick。

### 文件

- 新增：`scripts/verify_db.sh`

### 脚本内容

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor DB verification =="
echo "This requires local MySQL/Redis access."
echo "If this fails with Operation not permitted on 127.0.0.1:3306, rerun in an environment allowed to access local MySQL."

"$PY" -m pytest -q \
  "$ROOT/tests/test_auth.py" \
  "$ROOT/tests/test_decision.py" \
  "$ROOT/tests/test_meals_inventory.py" \
  "$ROOT/tests/test_feedback_memory.py" \
  "$ROOT/tests/test_inventory_stats.py" \
  "$ROOT/tests/test_recipe_checker.py" \
  "$ROOT/tests/test_favorites.py" \
  "$ROOT/tests/test_community.py" \
  "$ROOT/tests/test_community_recipe_flow.py" \
  "$ROOT/tests/test_agent_tools_inventory_favorites.py"

echo
echo "== DB verification passed =="
```

### 权限

```bash
chmod +x scripts/verify_db.sh
```

### 检查命令

```bash
./scripts/verify_db.sh
```

期望：

```text
24 passed
== DB verification passed ==
```

如果普通沙箱报 `Operation not permitted`，不能写成代码失败。必须写：

```text
DB verification requires local MySQL access; rerun with approved execution.
```

---

## 7. Task 4：新增 Eval API 验证脚本

### 目标

避免再次用旧后端进程跑 API Eval。

### 文件

- 新增：`scripts/verify_eval_api.sh`

### 脚本内容

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor Eval API verification =="
echo "API_BASE=$API_BASE"

echo
echo "== 1. Check API health by calling /v1/agent/execute =="
probe="$(
  curl -s -X POST "$API_BASE/v1/agent/execute" \
    -H 'Content-Type: application/json' \
    -d '{"input":"牛肉南瓜减脂30分钟","conversation_id":"eval_api_probe"}'
)"

echo "$probe" | "$PY" -c '
import json, sys
body = json.load(sys.stdin)
data = body.get("data", body)
events = data.get("events", [])
if not events:
    raise SystemExit("API probe failed: no events returned")
if not any(e.get("phase") for e in events):
    raise SystemExit("API probe failed: events have no phase; backend may be old")
if "termination_reason" not in data:
    raise SystemExit("API probe failed: missing termination_reason; backend may be old")
print("API probe passed")
'

echo
echo "== 2. Run Eval API mode =="
"$PY" "$ROOT/evals/runner.py" --quick --mode api --api-base "$API_BASE" --prefix latest-api

echo
echo "== Eval API verification passed =="
```

### 权限

```bash
chmod +x scripts/verify_eval_api.sh
```

### 使用方式

先启动当前代码后端：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

然后运行：

```bash
./scripts/verify_eval_api.sh
```

期望：

```text
API probe passed
Score: 72/72 (100%)
== Eval API verification passed ==
```

如果失败并提示 `events have no phase` 或 `missing termination_reason`：

1. 检查 8000 端口旧进程：

```bash
lsof -iTCP:8000 -sTCP:LISTEN -n -P
```

2. 停止旧进程。
3. 用当前代码重启后端。
4. 重跑脚本。

---

## 8. Task 5：更新迭代 README

### 目标

让后来的人不用读 20 多篇文档也知道当前状态和从哪开始。

### 文件

- 修改：`docs/迭代修改/README.md`

### 必须包含的内容

在 README 顶部加入：

```markdown
## 当前推荐阅读顺序

1. `23-v3最终复核报告_MySQL已验证.md`：当前 v3 基线、已完成项、剩余规划。
2. `24-Eval_API_Mode_与测试收口修复文档.md`：Eval mock/api、测试收口和最终验证结果。
3. `25-v5基础工程化任务书_给Subagent.md`：下一轮基础工程化任务。

## 当前验证命令

快速验证：

```bash
./scripts/verify_quick.sh
```

DB 验证：

```bash
./scripts/verify_db.sh
```

Eval API 验证：

```bash
./scripts/verify_eval_api.sh
```

## 当前边界

- Eval mock/api quick 已通过，但还不是完整 30-50 条黄金用例体系。
- DeepSeek Judge 尚未接入。
- Alembic 尚未接入。
- Playwright 前端 smoke 尚未接入。
- 本地 CNN/ONNX 降级已明确不做。
```

注意 Markdown 代码块嵌套，实际写入时不要破坏 README 格式。

---

## 9. Task 6：写 v5 修复记录

### 目标

每轮修改都必须有记录，方便审查。

### 文件

- 新增：`docs/迭代修改/26-v5基础工程化修复记录.md`
- 同步：`！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/26-v5基础工程化修复记录.md`

### 内容模板

```markdown
# ByteSavor v5 基础工程化修复记录

日期：2026-06-20
依据：`25-v5基础工程化任务书_给Subagent.md`

## 修改摘要

| 任务 | 状态 | 文件 |
|---|---:|---|
| pytest markers |  |  |
| verify_quick.sh |  |  |
| verify_db.sh |  |  |
| verify_eval_api.sh |  |  |
| README 更新 |  |  |

## 验证结果

### quick

命令：

```bash
./scripts/verify_quick.sh
```

结果：

```text
<粘贴最终 summary>
```

### DB

命令：

```bash
./scripts/verify_db.sh
```

结果：

```text
<粘贴最终 summary，或说明普通沙箱限制并给出沙箱外结果>
```

### Eval API

命令：

```bash
./scripts/verify_eval_api.sh
```

结果：

```text
<粘贴最终 summary>
```

## 剩余问题

- 如果没有，写“无阻塞问题”。
- 如果有，必须写清楚复现命令和下一步。
```

---

## 10. 最终验收标准

subagent 完成后必须贴以下内容：

```text
1. ./scripts/verify_quick.sh 的完整结果
2. ./scripts/verify_db.sh 的完整结果，或说明需要授权访问 MySQL 并给出沙箱外结果
3. ./scripts/verify_eval_api.sh 的完整结果
4. docs/迭代修改 与 可见目录 的文件列表 tail
5. git diff --stat
```

主 agent 审查时会复跑：

```bash
./scripts/verify_quick.sh
./scripts/verify_eval_api.sh
```

DB 脚本会在可访问 MySQL 的环境下复跑。

---

## 11. 后续不在 v5 基础包内的任务

这些不要在本轮做：

1. Alembic 迁移。
2. Playwright 前端 smoke。
3. 30-50 条 Eval 黄金用例。
4. DeepSeek Judge / 双 Agent 软评估。
5. SSE `/v1/agent/execute/stream`。
6. 微信 `code2session` 生产鉴权。

这些应在 v5 基础工程化通过后，分别写单独任务书。

---

## 12. 交接说明

当前工作交接给 subagent 时，必须告诉它：

1. 不要相信旧测试数字，所有结果以本任务书命令为准。
2. 如果 `Eval api` 失败，先检查 8000 是否旧进程，不要直接改 scorer。
3. 如果 DB 测试失败且错误是 `Operation not permitted`，这是沙箱权限问题，不是代码失败。
4. 如果 `verify_quick.sh` 失败，必须先修到普通沙箱可过。
5. 每个脚本都要 `set -euo pipefail`，失败即停止。
6. 文档必须同步到 `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/`。

---

## 13. 当前主线判断

v5 的价值不是“新增功能”，而是让项目进入可交接、可复验状态。

完成 v5 后，任何人接手项目都应该能用三条命令判断系统是否健康：

```bash
./scripts/verify_quick.sh
./scripts/verify_db.sh
./scripts/verify_eval_api.sh
```

这就是本轮基础工作的完成标准。
