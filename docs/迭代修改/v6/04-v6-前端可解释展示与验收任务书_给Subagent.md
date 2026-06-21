# ByteSavor v6-04：前端可解释展示与验收任务书（给 Subagent）

日期：2026-06-21  
执行对象：subagent  
审查人：主 agent / 项目负责人  
前置依赖：建议先完成 v6-01/v6-02/v6-03  

---

## 0. 本任务目标

把 v6 后端工业化能力展示给用户和评委看：推荐不是黑盒，Agent 执行不是黑盒，VLM 慢也不是白屏。

完成后必须能准确答辩：

> ByteSavor 不只是给一个答案，而是展示“为什么推荐、用了哪些记忆、命中了哪些食材、还需要补买什么、Agent 每一步调用了哪个 Skill、耗时多少、是否缓存命中、是否降级”。

---

## 1. 当前问题

用户实测暴露的问题已经部分修复，但前端展示仍不够工业化：

1. 推荐卡片没有足够明确展示：
   - 已匹配食材；
   - 缺失食材；
   - 补买建议；
   - 偏好命中。
2. Agent 时间线有 events，但展示没有充分体现：
   - planner；
   - skill；
   - evaluator/judge；
   - latency；
   - cache_hit；
   - degraded。
3. 用户需要能直观看到推荐真的围绕当前输入食物，而不是“芹菜炒牛肉”这种不相关结果。

---

## 2. 严禁事项

1. 不要做营销落地页。
2. 不要引入 WebSocket/SSE。
3. 不要用大段说明文字堆页面。
4. 不要改动推荐算法主逻辑；推荐算法问题应回后端 decision 修。
5. 不要破坏底部 tab 图标大小和位置。
6. 不要新增会导致 H5 构建失败的第三方库。

---

## 3. 必改/检查文件

| 文件 | 操作 | 要求 |
|---|---|---|
| `bsapp/src/pages/home/home.vue` | 修改 | Agent 时间线展示 planner/skill/evaluator 字段 |
| `bsapp/src/pages/explore/explore.vue` | 修改 | 推荐/搜索结果展示匹配食材和偏好 |
| `bsapp/src/pages/recipe-detail/recipe-detail.vue` | 检查/修改 | 加入今日用餐计划入口保持可见 |
| `bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue` | 检查/修改 | 展示 VLM cache/latency 状态 |
| `scripts/verify_frontend_regressions.mjs` | 修改 | 增加关键 UI 文案/交互 smoke |

如果实际文件名不同，先用 `rg` 找到对应页面，不要凭空新建重复页面。

---

## 4. 推荐卡片展示要求

推荐卡片至少展示这些字段，字段不存在时优雅隐藏：

```javascript
recipe._meta?.matched_ingredients
recipe._meta?.missing_ingredients
recipe._meta?.preference_matches
recipe._meta?.purchase_suggestions
recipe.llm_reranked
```

展示规则：

1. `matched_ingredients`：绿色/主色小标签，文案短，如 `已用：牛肉、韭黄`。
2. `missing_ingredients`：弱提示，如 `缺：鸡蛋`。
3. `purchase_suggestions`：显示为 `建议补买：鸡蛋 2个`。
4. `preference_matches`：显示 `符合偏好：少油、减脂`。
5. `llm_reranked`：可以显示一个小标识 `AI重排`，但不要夸大成“AI原创”。

验收：

- 输入 `牛肉韭黄`，首屏推荐必须能看到 `牛肉` 或 `韭黄` 的匹配提示。
- 如果推荐只命中一个核心食材，必须显示缺失/补买说明。

---

## 5. Agent 时间线展示要求

`events` 中不同类型展示：

| event.type | 展示重点 |
|---|---|
| `plan` | `planner_source`、`tool`、`reason`、`candidate_tools` |
| `tool_start` | skill 名称和阶段 |
| `tool_result` | `skill.category`、`latency_ms`、`retry_count`、`cache_hit`、`error_code` |
| `evaluation` | verdict、issues 数量 |
| `soft_judge` | scores、WARN/PASS |
| `final` | final message |

UI 原则：

1. 不要做大卡套小卡。
2. 时间线要紧凑，适合答辩展示。
3. `degraded/error` 用明显但不过度的警示样式。
4. 移动端不能横向溢出。
5. 文案短，不要写长篇解释。

---

## 6. 前端 smoke 脚本要求

修改 `scripts/verify_frontend_regressions.mjs`，至少检查：

1. 首页能打开。
2. 推荐输入框可输入 `牛肉韭黄`。
3. 点击推荐/发送后页面不报 console error。
4. 页面能出现推荐列表或明确错误提示。
5. 菜谱库搜索 `韭黄炒蛋` 能看到结果文案。
6. 底部 tab 的识别/社区图标元素尺寸不异常（至少不为 0）。

如果脚本没有启动 dev server 的能力，只写成连接既有 `localhost` 的 smoke，并在文档里写清前置条件。

---

## 7. 手工验收清单

修复记录必须包含手工验收清单：

1. 新注册用户登录后，首页不应出现旧用户库存/收藏/用餐数据。
2. 首页/AI 助手输入 `牛肉韭黄`，不得首推无韭黄说明的 `芹菜炒牛肉`。
3. 推荐卡显示匹配食材、缺失食材或补买建议。
4. 菜谱库搜索 `韭黄炒蛋` 能命中 `韭黄炒鸡蛋`。
5. 菜谱详情能加入今天早餐/午餐/晚餐/加餐。
6. 用餐计划 tab 能切换，不只是 UI 切换，数据也按 meal slot 切换。
7. 社区发图、点赞、收藏 toggle 正常。
8. 识别页上传图片有压缩/推理/完成阶段反馈。
9. Agent 时间线能看到 planner、skill、evaluation。
10. 手机宽度下底部 tab 图标大小位置一致。

---

## 8. 验证命令

```bash
node scripts/verify_frontend_regressions.mjs
```

```bash
cd bsapp
npm run build:h5
```

后端 API 回归：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_agent.py \
  tests/test_decision.py \
  tests/test_decision_memory_matching.py
```

---

## 9. 修复记录要求

完成后新增：

- `docs/迭代修改/45-v6-前端可解释展示与验收修复记录.md`
- `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/45-v6-前端可解释展示与验收修复记录.md`

必须写清：

1. 哪些字段来自后端，哪些只是前端展示。
2. 哪些用户实测问题被回归验证。
3. 浏览器/移动端手工检查结果。
4. H5 构建结果。
5. 未完成项和风险。

