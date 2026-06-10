# ByteSavor V3.0 核心技术文档

> 基于实际代码的完整技术说明。覆盖架构、算法、API、数据流、创新点。

---

## 一、项目概览

### 1.1 定位

基于多模态 Agent 的饮食全链路系统。用户拍照或打字描述食材 → VLM 识别 → 推荐引擎匹配菜谱 → 生成购物清单 → 反馈学习偏好。

### 1.2 规模

| 指标 | 数值 |
|------|------|
| 后端 Python | 2,224 行 / 47 文件 |
| 前端 Vue/JS/CSS | 5,714 行 / 23 文件 |
| 测试 pytest | 212 行 / 7 文件 |
| API 路由 | 11 个模块 |
| 菜谱数据 | 2,576 道（Ta-da 数据集 + 手写 60 道 + DeepSeek 增强 3 道） |
| 食材挑选知识库 | 50+ 种食材 |

### 1.3 目录结构

```
app/
├── main.py              # FastAPI入口, CORS, 异常处理, 启动建表
├── schemas.py           # Pydantic请求/响应模型
├── core/                # 基础设施
│   ├── config.py        # pydantic-settings读.env
│   ├── database.py      # SQLAlchemy async + asyncmy
│   ├── redis.py         # Redis连接池
│   ├── security.py      # JWT签发/校验 + bcrypt
│   └── cache.py         # Redis缓存工具
├── middleware/
│   └── auth.py          # JWT认证中间件(get_current_user/get_optional_user)
├── models/              # ORM模型
│   ├── __init__.py      # User, Profile, NutritionLog, Feedback
│   └── recipe.py        # Recipe(含story/culture_tags/source)
├── routers/             # 11个路由模块
│   ├── auth.py          # 注册/登录
│   ├── user.py          # 画像CRUD
│   ├── sense.py         # B-感知: VLM食材识别
│   ├── decision.py      # Y-决策: 推荐引擎
│   ├── task.py          # T-执行: 清单合并+人数调整
│   ├── agent.py         # Agent编排入口
│   ├── feedback.py      # E-反馈: 评分+偏好学习
│   ├── assistant.py     # AI助手(DeepSeek对话)
│   ├── quality.py       # 品质鉴定
│   ├── nutrition.py     # 营养分析
│   └── guide.py         # 探店向导
├── services/            # 业务逻辑层
│   ├── user.py          # 用户注册/登录/画像
│   ├── decision.py      # 推荐引擎pipeline(5步)
│   ├── decision_engine.py # 推荐引擎抽象基类
│   ├── shopping.py      # 购物清单合并引擎
│   ├── agent.py         # Agent编排(三级降级+Stage追踪)
│   ├── feedback.py      # 反馈+偏好学习
│   ├── assistant.py     # AI美食助手(DeepSeek)
│   ├── quality.py       # 品质评估(VLM+知识库)
│   ├── nutrition_analyzer.py # 营养分析+份量参照
│   ├── nutrition.py     # 营养缺口计算
│   ├── food_guide.py    # 美食向导(经典菜知识库)
│   ├── ingredient_tips.py # 50+食材挑选知识库
│   ├── recipe_presenter.py # 菜谱展示格式化
│   ├── providers.py     # Provider抽象接口
│   ├── llm.py           # Ollama LLM调用
│   ├── llm_deepseek.py  # DeepSeek LLM调用
│   ├── neo4j.py         # Neo4j连接器(桩)
│   ├── langgraph_agent.py # LangGraph适配层
│   └── vlm/             # VLM provider
│       ├── base.py      # 抽象基类
│       ├── openai.py    # OpenAI兼容provider
│       └── prompts.py   # 场景prompt模板
└── seed/
    ├── recipes.json     # 2576道菜谱
    └── seed_recipes.py  # 启动导入脚本
```

---

## 二、架构设计

### 2.1 B-Y-T-E 闭环

```
用户输入(拍照/文字)
    │
    ▼
┌─────────────────────────────────────────┐
│  Agent 编排层                            │
│  trace_id + stages[] + degraded 标记     │
│  DeepSeek→Ollama→正则 三级意图解析      │
├─────────────────────────────────────────┤
│  B-感知     │  Y-决策    │  T-执行    │  E-反馈   │
│  VLM识别    │  推荐引擎   │  清单合并   │  偏好学习  │
│  Qwen-VL-Max│  5步Pipeline│  人数调整   │  评分更新  │
└─────────────────────────────────────────┘
    │
    ▼
  返回: 食材列表 + 菜谱推荐 + 购物清单 + 偏好状态
```

### 2.2 分层架构

```
┌──────────────────────────────────────┐
│  Router层 (HTTP接口)                 │
│  接收请求 → 参数校验 → 调Service →   │
│  返回 SuccessResponse/ErrorResponse  │
├──────────────────────────────────────┤
│  Service层 (业务逻辑)                │
│  算法实现 / 数据聚合 / 外部API调用    │
│  不操作HTTP，不操作数据库连接         │
├──────────────────────────────────────┤
│  Model层 (数据定义)                  │
│  SQLAlchemy ORM / Pydantic Schema    │
├──────────────────────────────────────┤
│  Core层 (基础设施)                   │
│  配置/数据库/缓存/认证               │
└──────────────────────────────────────┘
```

路由层不写SQL，服务层不读HTTP请求，模型层只定义结构。三层单向依赖。

### 2.3 数据表设计

```
users (用户基础)
  id, openid(唯一), phone, name, created_at

profiles (用户画像)
  user_id(FK→users), goal, preferences(JSON), health_score

nutrition_logs (营养记录)
  id, user_id(FK→users), score, deficits(JSON), recorded_at

feedback (用户反馈)
  id, user_id(FK→users), recipe_id, rating, created_at

recipes (菜谱)
  id, title, steps(JSON), ingredients(JSON), tags(JSON),
  cook_time, calories, protein, carbs, fat, difficulty,
  story, culture_tags(JSON), source, schema_version
```

---

## 三、核心算法详解

### 3.1 推荐引擎 Pipeline（decision.py）

**代码位置：** `app/services/decision.py`

**五步流程：**

```
1. _retrieve()     → SELECT * FROM recipes（2576道全量）
2. _hard_filter()  → cook_time > time_limit → 淘汰
3. _rank()         → 食材50% + 标签30% + 偏好20%
4. _fallback()     → 全淘汰时降权返回
5. _build_reasons() → 生成可解释理由
```

**打分公式（全部归一化 0~1）：**
```python
// _rank() 第68行
s = s_ing * 0.5 + s_tag * 0.3 + s_pref * 0.2

// _calc_ingredient() 第133-141行
recipe_names = {i["name"].lower() for i in r.ingredients}
exact = recipe_names & user_set  // 精确匹配
score = min(len(exact) / len(recipe_names), 1.0)

// _calc_tag() 第144-164行
base = 0.2
if taste in tags: score += 0.3
if goal=="fat_loss" and "high_protein" in tags: score += 0.25
...

// _calc_pref() 第167-174行
if not prefs: return 0.5  // 新用户不惩罚！
hits = [p for p in prefs if p.lower() in tags]
score = min(0.5 + len(hits) * 0.2, 1.0)
```

**冷启动策略：**
- 新用户偏好为空 → `_calc_pref` 返回 0.5（基准分，不惩罚）
- 用户食材为空 → `is_explore` 标志 → `_explore_rank` 全量推荐
- 硬过滤全淘汰 → `_fallback` 放宽条件降权返回

**可解释性：**
每条推荐返回 `reasons` 数组，结构化格式 `{code, text, meta}`。前端按 code 渲染多语言文案。8种 reason code:
`ING_MATCH`, `TASTE_MATCH`, `LOW_CARB`, `HIGH_PROTEIN_GOAL`, `BALANCED`, `PREF_MATCH`, `QUICK`, `NEAR_FIT`

### 3.2 VLM 识别 Skills 体系

**代码位置：** `app/services/vlm/openai.py`

**Skill 1: 细粒度 Prompt**
`prompts.py` 的 `FOOD_ANALYSIS` 要求 VLM 返回：名称、置信度、新鲜度(high/medium/low)、状态(新鲜/冷藏/冷冻)、外观特征(颜色纹理)、分量估算(克数)。将 VLM 从分类器变为质检员。

**Skill 2: 鲁棒解析器**
```python
// _parse() 第47-62行
def _parse(data):
    content = data["choices"][0]["message"]["content"]
    // 1. Markdown代码块
    if "```json" in content: ...
    elif "```" in content: ...
    // 2. 文本中嵌JSON
    elif "{" in content and "}" in content: ...
    // 3. 校验
    if "ingredients" not in parsed: parsed["ingredients"] = []
    // 4. 截断检测
    if finish == "length": logger.warning("vlm_truncated")
```

**Skill 3: 品质鉴定知识库**
`ingredient_tips.py`：50+ 种食材的挑选标准。VLM 识别 + 知识库匹配 = 优/中/差品质报告。

**Skill 4: 三级降级链**
```
DashScope API(qwen-vl-max) → Ollama本地(qwen2.5-vl) → 提示用户重试
```

**Skill 5: 前端图片压缩**
`ingredient-recognition.vue` 第189行：canvas resize 到 800px 宽，JPEG 质量 75%，3MB→200KB。

### 3.3 Agent 编排引擎

**代码位置：** `app/services/agent.py`

**三级意图降级：**
```python
// _get_intent() 第12-29行
1. DeepSeek (api.deepseek.com) → 结构化JSON
2. Ollama 本地 (qwen2.5:1.5b) → 备用
3. 正则匹配 → 最终兜底(18种常见食材)
```

**Stage 追踪：**
每次执行返回 `trace_id + stages[] + degraded`：
```json
{
  "trace_id": "abc123",
  "stages": [
    {"stage":"sense", "status":"success", "latency_ms":5},
    {"stage":"decision", "status":"success", "latency_ms":3},
    {"stage":"task", "status":"success", "latency_ms":2}
  ],
  "degraded": false
}
```

**Provider 抽象：**
`providers.py` 定义三个 Protocol：`SenseProvider`, `DecisionProvider`, `TaskProvider`。Agent 只依赖接口，router 用闭包注入实现。后期换 LangGraph 只需改注入层。

### 3.4 购物清单合并引擎

**代码位置：** `app/services/shopping.py`

**合并规则：**
- 同名+同单位 → 数值累加（300g+400g=700g）
- 不同单位 → 保留独立条目
- `_can_merge()` 判断单位兼容性（g/ml/kg等15种可合并单位）

**人数调整：**
`task.py` 第35-53行：DeepSeek 按人数智能调整全表数量。2人→4人自动翻倍。

**挑拣建议：**
`ingredient_tips.py` 50+ 种食材的挑选标准。`enrich_shopping_list()` 给每项附加 tip。

### 3.5 偏好学习闭环

**代码位置：** `app/services/feedback.py`

```python
// submit_feedback() 第8-36行
1. 写入 feedback 表
2. 查询菜谱标签
3. rating >= 4 → 追加标签到用户偏好
4. rating <= 2 → 移除匹配标签
5. 更新 profiles 表
```

**效果：**
```
评分前: preferences=[]
评分 r_001(标签:spicy,high_protein,low_carb) 5星 → ['spicy','high_protein']
评分 r_005(标签:light,high_protein,low_carb,fat_loss) 5星 → ['spicy','high_protein','light','low_carb']
推荐时: PREF_MATCH 理由出现 → 加权排序
```

---

## 四、API 总览

### 4.1 核心接口（11个模块）

| 模块 | 方法 | 路径 | 功能 |
|------|------|------|------|
| Auth | POST | `/v1/auth/register` | 注册/静默登录(OpenID) |
| Auth | POST | `/v1/auth/login` | 登录 |
| User | GET | `/v1/user/profile` | 查画像(需JWT) |
| User | PUT | `/v1/user/profile` | 改偏好(goal+preferences) |
| User | GET | `/v1/nutrition/status` | 营养状态 |
| Sense | POST | `/v1/sense/analyze` | VLM食材识别 |
| Decision | POST | `/v1/decision/meal-plan` | 菜谱推荐 |
| Decision | GET | `/v1/recipes` | 菜谱列表 |
| Decision | GET | `/v1/recipes/{id}` | 菜谱详情(含步骤/营养/文化) |
| Task | POST | `/v1/task/merge-list` | 清单合并+挑拣建议 |
| Agent | POST | `/v1/agent/execute` | Agent全流程(mode:full/plan/recommend) |
| Feedback | POST | `/v1/feedback/meal` | 评分→偏好学习 |
| Assistant | POST | `/v1/assistant/chat` | AI助手对话(DeepSeek) |
| Quality | POST | `/v1/quality/assess` | 品质鉴定 |
| Nutrition | POST | `/v1/nutrition/analyze-meal` | 营养分析 |
| Guide | POST | `/v1/guide/explore` | 探店向导 |

### 4.2 统一响应格式

```json
// 成功
{"status":"success", "data":{...}, "trace_id":"uuid"}

// 错误
{"status":"error", "error":{"code":"XXX","message":"..."}, "trace_id":"uuid"}
```

---

## 五、关键设计决策

### 5.1 为什么不用 Mock 降级

Sense 路由第17行：VLM 不可用时返回 `ErrorResponse(code=VLM_UNAVAILABLE)`，不伪造食材数据。与竞品不同——我们宁可说"识别失败"也不返回假数据。

### 5.2 为什么 MySQL 而非 PostgreSQL

PPT 原计划用 PostgreSQL，实际选 MySQL。理由：团队都会 MySQL，JSON 类型够存非结构化菜谱数据，asyncmy 驱动稳定。后期换 PG 只需改 database.py 一行。

### 5.3 为什么顺序 Pipeline 而非 LangGraph

`langgraph_agent.py` 已预留适配层。当前 LLM 能力（本地 1.5B 模型）不足以支撑 LangGraph 的条件分支。等推理能力到位后，改注入层即可切换，Agent 接口不变。

### 5.4 为什么不用 Neo4j

`neo4j.py` 连接器已写好。2576 条菜谱数据量下，MySQL JSON 查询足够。`cook_time` 和 `ingredients` 的索引已覆盖推荐引擎需求。

### 5.5 为什么 JWT 默认空密钥会拦截

`security.py` 第7-9行：启动时检查 `JWT_SECRET`，空值或占位值直接 `RuntimeError`。防止部署时忘记配密钥。

---

## 六、测试体系

### 6.1 pytest 自动化

23 个测试用例，覆盖：
- `test_agent.py`：意图解析(正则)+Agent execute 全流程
- `test_auth.py`：注册/登录/画像(含唯一openid隔离)
- `test_decision.py`：推荐/探索/详情/不存在
- `test_shopping.py`：单位解析/合并/格式化
- `test_sense.py`：VLM不可用时不返回mock

### 6.2 端到端验证

5 个演示场景全链路通过（`demo_tests/README.md`），图片已压缩优化。

---

## 七、部署

### Docker Compose 一键启动

```bash
docker compose up -d
# MySQL:3306 + Redis:6379 + Backend:8000
```

JWT_SECRET 必须通过环境变量注入，不设置会拒绝启动。

### 本地开发

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
