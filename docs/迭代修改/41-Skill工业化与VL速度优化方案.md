# ByteSavor Skill 工业化与 VL 速度优化方案

日期：2026-06-21

目标：把现有“规则状态机 + 工具型 Agent”继续推进到更规范的工业化 Agent，同时优化 VL 识别速度和用户感知等待。

---

## 1. 当前真实状态

### 已具备

- Agent runtime / LangGraph runtime。
- Skill 工具注册：
  - `sense`
  - `decision`
  - `task`
  - `nutrition`
  - `quality`
  - `guide`
  - `inventory`
  - `favorites`
  - `recipe_check`
- `SkillDescriptor` 元数据。
- 事件流：
  - `plan`
  - `tool_start`
  - `tool_result`
  - `evaluation`
  - `final`
- 运行时硬规则 evaluator。
- VL 后端 hash 缓存。
- 前端 H5 图片压缩雏形。

### 还不足

1. `SkillDescriptor` 还没有真正约束 `ToolRegistry`。
2. planner 仍是规则式关键词路由，不是 descriptor 驱动。
3. Skill 没有统一 timeout、retry、错误码策略。
4. VL 缓存没有模型/Prompt 维度版本，缓存命中不够可观测。
5. VL 前端体验还没有完整阶段反馈。
6. 识别结果没有把 `cache_hit/latency/model` 显示给用户或答辩时间线。

---

## 2. P0：基础工业化修复

### 2.1 ToolRegistry 绑定 SkillDescriptor

要求：

- 注册工具时校验 descriptor 是否存在。
- `ToolRegistry.describe()` 返回已注册工具的 descriptor。
- `ToolRegistry.names()` 和 descriptor 名称保持一致。

验收：

- 注册未知 tool 抛错。
- 所有当前注册 tool 都有 descriptor。

### 2.2 VL 识别可观测元数据

要求：

`analyze_food()` 返回：

- `cache_hit`
- `cache_key`
- `latency_ms`
- `model`
- `image_fingerprint`

缓存 key 必须包含：

- 图片 hash
- 模型名
- prompt 版本

验收：

- 第一次识别 `cache_hit=false`。
- 第二次同图识别 `cache_hit=true`。
- 返回数据包含 `latency_ms/model/cache_key`。

---

## 3. P1：速度与用户感知

### 3.1 前端压缩更明确

要求：

- H5 图片最长边压到 720px。
- JPEG quality 使用 0.68。
- 记录压缩前后字节大小。
- `recognitionStatus` 显示：
  - 正在压缩图片
  - 已压缩到 xxx KB
  - 正在调用视觉模型
  - 缓存命中/识别完成

### 3.2 前端展示 VL 元数据

要求：

- 识别完成后显示：
  - 是否缓存命中；
  - 识别耗时；
  - 模型名。

---

## 4. P2：更智能的 Planner

### 4.1 Descriptor 驱动候选工具

要求：

- planner 不再完全硬编码。
- 先用 descriptor 的 intent_keywords、requires_image、requires_user 生成候选工具。
- 规则 planner 仍作为 fallback。

### 4.2 可选 LLM Planner

要求：

- DeepSeek 只能从候选工具中选择下一步。
- 不允许直接发明 tool。
- LLM planner 超时或失败时回落规则 planner。

---

## 5. 后续验收命令

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_agent_loop_engineering.py tests/test_sense.py
```

```bash
node scripts/verify_frontend_regressions.mjs
```

```bash
cd bsapp && npm run build:h5
```

