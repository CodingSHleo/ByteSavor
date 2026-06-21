# ByteSavor Agent 黑箱 Eval 体系：下一轮任务书

日期：2026-06-19  
前置条件：先完成 `ByteSavor_Agent规范化实施手册_给子Agent_2026-06-19.md` 中的 Agent phase、termination_reason、MemoryContext、Hard Evaluator、memory_used 等基础规范。  
目标读者：后续实现 Eval 的子 Agent / 工程师  
定位：这是 Agent 规范化完成后的下一轮任务，不是当前 P0 演示修复。
重要边界：本文档讲的是“离线黑箱 Eval Pipeline”，不是运行时 Hard Evaluator。运行时 Evaluator 用来拦截一次请求里的明显错误；离线 Eval 用来判断一次版本迭代后，用户满意度是否整体变好。

---

## 1. 结论：这份建议是否适合 ByteSavor

适合，但必须降级落地。

外部建议提出的“黑箱 Eval + LLM Judge + Human Alignment + CI 报告”方向是对的。它解决的是单元测试无法回答的问题：

> 代码跑通了，但用户会不会满意？

ByteSavor 确实需要这个体系，因为我们的 Agent 输出质量会受到这些变化影响：

- Prompt 改动。
- 推荐权重改动。
- 偏好记忆接入方式变化。
- Agent planner 和工具顺序变化。
- VLM/LLM 模型版本变化。
- Hard Evaluator 规则调整。

但当前不应一步到位做 50 条全量用例 + LLM Judge 三次评分 + GitHub Action 阻断合并。原因：

- 当前首先要规范 Agent 运行时输出，否则 Eval 没有稳定字段可读。
- 真实 DeepSeek Judge 有成本、网络、评分漂移问题。
- CI 暂时不是最短路径，课程演示更需要本地可跑、可解释、可展示的评估报告。

因此采用三阶段落地：

1. P0：10 条快速黄金用例 + 本地规则评分 + Markdown/JSON 报告。
2. P1：扩展到 30-50 条用例 + 可选 LLM Judge + 人工校准样本。
3. P2：接入 CI、趋势图、HTML 报告、阻断阈值。

冷启动策略：

- 当前没有真实用户日志，不能假装已经有线上数据。
- 第一批用例由团队手工构造，基于 demo_test 角色、演示流程和已知 bug。
- 先做 10 条 quick set 验证 runner、scorer、报告格式。
- 再扩充到 30-50 条 full set，覆盖识别、推荐、状态依赖、冲突、澄清和偏好记忆。
- 后续如果有真实用户反馈，只能使用脱敏、重写后的场景，不直接把隐私日志放进 Eval。

---

## 2. 审视结论：采纳、降级、暂缓、拒绝

这份外部建议本身是高质量方向，但如果不结合 ByteSavor 当前状态直接照搬，会导致过度设计、实现顺序错误和演示风险。因此最终裁决如下。

### 2.1 直接采纳

1. 端到端黑箱 Eval 的思想
   - 原因：我们当前已有白盒测试，但白盒测试只能证明接口和状态流程没崩，不能证明推荐结果让用户满意。
   - 落地：建立 `evals/` 目录，维护黄金用例和报告。

2. Eval 用例必须包含完整上下文
   - 原因：ByteSavor 是有状态 Agent，单独测一句 prompt 没意义。
   - 落地：用例包含 user_profile、inventory、today_meals、conversation_history、input、checks。

3. 评分维度要结构化
   - 原因：不能靠“感觉还不错”评价 Agent。
   - 落地：instruction_following、inventory_usage、preference_obedience、nutrition_reasonable、actionability、observability。

4. 报告必须保留 case 细节
   - 原因：只有平均分无法指导修复。
   - 落地：报告写明每条 case 的输出、分数、issues、suggestions、events 摘要。

### 2.2 降级采纳

1. “50 条黄金用例”
   - 外部建议：冷启动做 30-50 条。
   - 我们裁决：先做 10 条 quick set。
   - 原因：现在更缺的是 Eval 框架，而不是大量 case；先跑通闭环，再扩充用例。

2. “LLM Judge”
   - 外部建议：用 DeepSeek 批量打分。
   - 我们裁决：P0 不启用，P1 可选启用。
   - 原因：LLM Judge 有成本、网络不稳定、评分漂移和 prompt 注入风险；先用规则 scorer。

3. “Human Alignment”
   - 外部建议：Spearman 相关系数达到 0.85。
   - 我们裁决：保留人工校准思想，不把 0.85 当硬指标。
   - 原因：课程项目样本量小，强行统计会显得虚假；更务实的是记录人机分歧并修 rubric。

4. “CI/CD 阻断合并”
   - 外部建议：总分低于 4.0 阻断合并。
   - 我们裁决：P2 才考虑，并且先观察不阻断。
   - 原因：当前本地开发和演示优先，贸然上 CI 门禁会浪费时间。

### 2.3 暂缓

1. HTML 报告和雷达图
   - 暂缓原因：P0 Markdown/JSON 足够定位问题。
   - 后续条件：quick eval 稳定后再做可视化。

2. 每条用例跑 3 次取均值
   - 暂缓原因：P0 不调用 LLM Judge，规则评分确定性强；跑 3 次没有收益。
   - 后续条件：启用 LLM Judge 后再考虑重复评分。

3. GitHub Action
   - 暂缓原因：当前更重要的是本地 runner 和用例质量。
   - 后续条件：用例集稳定、评分稳定后再接 CI。

### 2.4 拒绝

1. 把 Eval 写进业务接口
   - 拒绝原因：Eval 是研发质量工具，不应污染用户路径。
   - 正确方式：独立 `evals/` runner 调用 Agent。

2. 用真实用户隐私日志直接构造 Eval
   - 拒绝原因：隐私和复现风险。
   - 正确方式：使用脱敏/人工构造上下文。

3. 初期完全依赖 LLM Judge
   - 拒绝原因：会把“质量评估”变成另一个不可控黑箱。
   - 正确方式：规则 scorer 是主线，LLM Judge 是辅助。

4. 在 Agent 规范化前先做 Eval
   - 拒绝原因：当前 Agent 输出还缺 phase、termination_reason、evaluation、memory_used 等稳定字段；现在做 Eval 会测不到关键质量维度。
   - 正确顺序：先做 Agent 规范化，再做黑箱 Eval。

### 2.5 最终裁决

这套 Eval 体系适合作为 Agent 规范化完成后的下一轮任务，不能插队替代当前 Agent 规范化。最小可落地版本是：

```text
10 条黄金用例
  + 完整上下文
  + 本地规则 scorer
  + JSON/Markdown 报告
  + 不依赖外部 LLM
  + 不接 CI
```

只有这个最小版本跑稳后，再扩展 LLM Judge、人类校准、全量 50 条和 CI 趋势报告。

---

## 3. Eval 和普通测试的区别

当前 `tests/` 主要是白盒测试，回答：

- 接口能不能返回。
- 状态机是否循环。
- 工具是否被调用。
- 数据库写入是否正确。

Agent Eval 要回答：

- 推荐是否真的符合用户目标。
- 是否遵守偏好和忌口。
- 是否利用库存。
- 是否考虑今天已吃了什么。
- 是否没有瞎编。
- 是否能解释为什么这么推荐。
- 用户看到这个结果是否会满意。

白盒测试和 Eval 的关系：

| 层级 | 名称 | 目的 | 当前状态 |
|---|---|---|---|
| L1 | 单元/接口测试 | 代码不崩、接口正确 | 已有较多 |
| L2 | 运行时 Hard Evaluator | 请求中拦截明显错误 | 下一轮 Agent 规范化要做 |
| L3 | 黑箱 Eval Pipeline | 端到端衡量用户满意度 | 本文档规划 |

不要把 L2 和 L3 混在一起：

- L2 在用户请求中运行，必须快、稳定、低成本。
- L3 在研发或发版前运行，可以慢一些，可以生成详细报告。
- L2 的规则可以被 L3 复用，但 L3 不应该污染业务接口。
- L3 可以引入 LLM Judge；L2 默认不依赖 LLM Judge。

---

## 4. 当前代码基础

Eval 需要依赖这些字段和模块：

| 模块 | 文件 | Eval 如何使用 |
|---|---|---|
| Agent 入口 | `app/routers/agent.py` | Eval runner 调用 `/v1/agent/execute` 或直接调用 `LangGraphAgent` |
| Agent 状态 | `app/agent/state.py` | 检查 intent、ingredients、recipes、memory_context |
| Agent 运行时 | `app/agent/langgraph_runtime.py` | 获取 events、errors、termination_reason |
| Agent 评估层 | `app/agent/evaluator.py` | P0 规则评分可复用 hard evaluator |
| 推荐服务 | `app/services/decision.py` | 检查推荐是否命中食材/偏好 |
| 偏好记忆 | `app/services/feedback.py` | 构造老用户偏好上下文 |
| 库存 | `app/services/inventory.py` | 构造库存场景 |
| 餐食记录 | `app/services/meal_memory.py` | 构造今日已吃场景 |
| 前端展示 | 暂不需要 | Eval 先做后端报告，不先改 UI |

---

## 5. 第一阶段 P0：本地快速 Eval

### 4.1 目标

构建一个本地可跑的最小 Eval：

- 10 条黄金用例。
- 不依赖真实 LLM Judge。
- 调用当前 Agent 或 mock 工具运行完整流程。
- 用规则 scorer 给出 0-5 分。
- 输出 JSON 和 Markdown 报告。

### 4.2 新增目录

建议新增：

```text
evals/
  cases/
    agent_quick_10.json
  rubrics/
    dinner_recommendation.json
    image_recognition.json
  reports/
    .gitkeep
  run_agent_eval.py
  scorer.py
  README.md
```

### 4.3 黄金用例格式

文件：`evals/cases/agent_quick_10.json`

建议格式：

```json
[
  {
    "case_id": "eval_001",
    "category": "recommendation",
    "description": "老用户，有偏好和库存，问10分钟晚餐",
    "context": {
      "user_profile": {
        "goal": "fat_loss",
        "preferences": ["light", "high_protein"],
        "avoid_ingredients": ["香菜", "肥肉"]
      },
      "inventory": [
        {"name": "鸡蛋", "amount": 4, "unit": "个"},
        {"name": "番茄", "amount": 2, "unit": "个"},
        {"name": "生菜", "amount": 1, "unit": "把"}
      ],
      "today_meals": [
        {"meal_slot": "lunch", "nutrition": {"calories": 650, "protein": 25}}
      ],
      "conversation_history": [
        {"role": "user", "content": "我不喜欢吃香菜"}
      ]
    },
    "input": {
      "text": "帮我推荐个晚餐，10分钟能做好的",
      "image_url": null
    },
    "checks": [
      {"type": "time_limit", "max_minutes": 15, "weight": 1.0},
      {"type": "avoid_ingredients", "items": ["香菜", "肥肉"], "weight": 1.2},
      {"type": "inventory_usage", "min_used": 1, "items": ["鸡蛋", "番茄", "生菜"], "weight": 1.0},
      {"type": "nutrition_range", "calories_min": 350, "calories_max": 650, "weight": 0.8},
      {"type": "actionability", "requires_steps": true, "weight": 0.8}
    ]
  }
]
```

### 4.4 P0 必须覆盖的 10 条用例

| case_id | 分类 | 场景 |
|---|---|---|
| eval_001 | 推荐 | 老用户有偏好和库存，问 10 分钟晚餐 |
| eval_002 | 推荐 | 新用户只有“牛肉南瓜减脂30分钟” |
| eval_003 | 推荐 | 用户忌口香菜，检查推荐不含香菜 |
| eval_004 | 库存 | 有收藏菜谱，问“我现在能不能做” |
| eval_005 | 餐食 | 午餐已高热量，晚餐应轻量 |
| eval_006 | 多轮 | 第一轮推荐，第二轮让生成购物清单 |
| eval_007 | 澄清 | 用户说“识别这张图”但没有 image_url |
| eval_008 | 识别 | VLM 返回低置信候选，应标为待确认 |
| eval_009 | 异常 | decision 工具返回空，Agent 应 degraded 或给解释 |
| eval_010 | 偏好 | 用户评分后偏好 high_protein，下次推荐体现偏好 |

### 4.5 冷启动扩展到 30-50 条的矩阵

quick set 跑通后，再扩展 full set。full set 不要求一次写完，但每次新增必须有明确场景意图。

| 类别 | 建议数量 | 覆盖重点 |
|---|---:|---|
| 纯感知识别 | 8-10 | 单食材、多食材、模糊图、相似食材、低置信候选 |
| 纯推荐 | 8-10 | 有库存、无库存、有收藏、有偏好、新用户 |
| 多约束推荐 | 8-10 | 减脂/增肌/均衡、30 分钟、忌口、指定食材覆盖 |
| 状态依赖 | 6-8 | 今日已吃、库存已扣减、上一轮识别结果、收藏菜谱清点 |
| 多轮对话 | 4-6 | 先识别再追问、先推荐再替换、先收藏再导入 |
| 异常与冲突 | 4-6 | 空输入、图片缺失、冲突目标、低置信识别、需要澄清 |

必须包含的回归用例：

1. “牛肉南瓜减脂30分钟”不能推荐完全无关食材。
2. 识别导出清单后，本次食品营养不能全为 0。
3. 用户有“不吃香菜”偏好时，推荐不能包含香菜。
4. 今日蛋白缺口较大时，推荐理由要体现蛋白补充。
5. 库存缺少关键食材时，菜谱清点要指出缺什么，而不是直接加入计划。
6. 用户确认摄入后，今日营养和库存变化应体现在后续推荐上下文中。

### 4.6 规则 scorer

文件：`evals/scorer.py`

P0 不调用 LLM。先做规则评分：

```python
def score_case(case: dict, agent_output: dict) -> dict:
    return {
        "case_id": case["case_id"],
        "scores": {
            "instruction_following": 0,
            "inventory_usage": 0,
            "preference_obedience": 0,
            "nutrition_reasonable": 0,
            "actionability": 0,
        },
        "total": 0,
        "issues": [],
    }
```

评分维度：

| 维度 | 检查方式 |
|---|---|
| instruction_following | 时间、目标、请求类型是否满足 |
| inventory_usage | 推荐菜谱是否使用库存食材 |
| preference_obedience | 是否避开忌口，是否命中偏好 |
| nutrition_reasonable | calories/protein 是否在合理范围 |
| actionability | 是否有 recipe、steps、shopping_list 或 ask_user |
| observability | 是否有 events、phase、termination_reason |

### 4.6 Eval runner

文件：`evals/run_agent_eval.py`

P0 可以不启动真实 HTTP 服务，直接使用测试工具构造 Agent：

- 对纯 runtime 评估，用 `LangGraphAgent` + fake tools。
- 对真实接口评估，可选用 `httpx.AsyncClient(ASGITransport(app=app))`。

输出：

```text
evals/reports/agent_eval_YYYYMMDD_HHMM.json
evals/reports/agent_eval_YYYYMMDD_HHMM.md
```

报告必须包含：

- 总分。
- 每条 case 得分。
- 失败 case 列表。
- 每条 case 的 agent reply。
- events 摘要。
- issues 和 suggestions。

### 4.7 P0 验收标准

- `python evals/run_agent_eval.py --quick` 能生成报告。
- 10 条 case 至少能跑完，不因为单条异常中断全局。
- 报告能指出 Top 失败用例。
- 不依赖外部 LLM API。
- 不影响现有 `tests/`。

---

## 6. 第二阶段 P1：LLM Judge

### 5.1 目标

在规则 scorer 之上加入可选 LLM Judge，用于评估“用户满意度”这种规则难以覆盖的维度。

这里的 LLM Judge 对应 Agent 方案里的“双 Agent 评估”思想，但优先放在离线 Eval 中验证稳定性。只有离线 Judge 的 rubric、输出格式和人工校准都稳定后，才考虑把一部分能力下放到运行时软评估。

这不是否定双 Agent，而是控制风险：

- 运行时先用硬规则和用户确认，保证演示和业务稳定。
- 离线 Eval 先用 LLM Judge 评估“步骤是否清晰、推荐是否实用、口味是否合理”等软维度。
- 等 Judge 与人工评分基本一致，再考虑作为运行时 DeepSeek Judge 的可选增强。

### 5.2 新增文件

```text
evals/llm_judge.py
evals/rubrics/judge_prompt.md
evals/human_alignment.md
```

### 5.3 LLM Judge 输入

必须包含：

- case context。
- current input。
- Agent output。
- events 摘要。
- rubric。

不要包含：

- 系统密钥。
- 原始内部 prompt。
- 数据库连接信息。

### 5.4 LLM Judge 输出格式

```json
{
  "scores": {
    "instruction_following": 4.5,
    "inventory_usage": 4.0,
    "preference_obedience": 5.0,
    "nutrition_reasonable": 4.0,
    "actionability": 4.5
  },
  "total": 4.4,
  "reasoning": "简要说明",
  "issues": [],
  "suggestions": []
}
```

### 5.5 P1 限制

- LLM Judge 默认关闭。
- 通过参数开启：

```bash
python evals/run_agent_eval.py --quick --judge llm
```

- 如果没有 `LLM_API_KEY`，自动跳过 LLM Judge，不应失败。
- Judge 不能覆盖事实检查结果。例如硬规则发现推荐完全没用核心食材，LLM Judge 不能把总评改成完全通过，只能解释原因或给改进建议。

### 5.6 人工校准

手动抽取 5-10 条样本，记录人工评分：

```text
evals/human_alignment.md
```

对比：

- 规则评分。
- LLM Judge 评分。
- 人工满意度评分。

目标不是追求数学完美，而是找出 Rubric 是否明显偏离用户感受。

---

## 7. 第三阶段 P2：CI 与趋势报告

### 6.1 目标

让 Eval 成为版本发布前的质量门禁。

### 6.2 建议

- 每次提交只跑 quick 10。
- 发版前跑 full 50。
- 不建议初期阻断 merge，先观察 1-2 周。
- 稳定后再设置阈值。

### 6.3 阈值建议

| 指标 | 阈值 |
|---|---|
| quick_10 average | >= 4.0 |
| no critical cases failed | true |
| observability score | >= 4.0 |
| max case latency | <= 10s，真实模型环境可放宽 |

---

## 8. 子 Agent 实施任务

### Task 1：创建 Eval 目录和用例格式

**文件：**

- Create: `evals/README.md`
- Create: `evals/cases/agent_quick_10.json`
- Create: `evals/rubrics/dinner_recommendation.json`
- Create: `evals/reports/.gitkeep`

**要求：**

- JSON 必须可被 `json.load()` 读取。
- 10 条 case 至少覆盖推荐、库存、多轮、澄清、异常。
- 不要放真实用户隐私。

### Task 2：实现规则 scorer

**文件：**

- Create: `evals/scorer.py`
- Test: `tests/test_eval_scorer.py`

**要求：**

- `score_case(case, output)` 返回 dict。
- 输出包含 total、scores、issues。
- 没有 recipe 时不能崩。
- 没有 events 时 observability 低分。

### Task 3：实现 eval runner

**文件：**

- Create: `evals/run_agent_eval.py`
- Test: `tests/test_eval_runner.py`

**要求：**

- 支持 `--quick`。
- 支持指定 cases 文件。
- 单条 case 失败不影响其他 case。
- 生成 JSON 和 Markdown 报告。

### Task 4：接入 Agent 输出

**文件：**

- Modify: `evals/run_agent_eval.py`
- Modify if needed: `app/agent/langgraph_runtime.py`

**要求：**

- 优先使用 fake tools 保证本地稳定。
- 后续可加 `--mode api` 调真实 ASGI app。
- 报告记录 events、termination_reason、memory_used、evaluation。

### Task 5：LLM Judge 可选接入

**文件：**

- Create: `evals/llm_judge.py`
- Create: `evals/rubrics/judge_prompt.md`

**要求：**

- 默认不启用。
- 没配置 key 不失败。
- 输出必须做 JSON parse 容错。

---

## 9. 我后续 review 会检查什么

会通过：

- P0 不依赖外部 API。
- 用例上下文完整，不只是单句 prompt。
- runner 能跑完并生成报告。
- scorer 不因字段缺失崩溃。
- 报告能看出哪条 case 失败和为什么失败。
- 不污染业务数据库。

会打回：

- 只做 LLM Judge，不做规则 scorer。
- 直接上 CI 阻断。
- 用例太空泛，比如只有“推荐一道菜”。
- 把 eval 写进业务接口里。
- 把测试数据写入真实用户表且不清理。
- 报告只有总分，没有 case 细节。

---

## 10. 答辩表达

可以讲：

> 单元测试只能证明代码路径能跑通，但 Agent 的核心是输出质量。我们计划构建黑箱 Eval：用完整用户上下文、库存、偏好、餐食历史去端到端调用 Agent，再用结构化 Rubric 评估指令遵循、库存利用、偏好遵守、营养合理性和可操作性。这样每次改 prompt、改推荐权重、改记忆系统，都能量化判断 Agent 是变好了还是变差了。

不要讲：

> 我们已经有完整 CI/CD LLM Judge 自动阻断上线。

当前正确说法：

> 当前阶段先落地 10 条快速黄金用例和本地规则评分，后续再扩展 LLM Judge、人类校准和 CI 趋势报告。
