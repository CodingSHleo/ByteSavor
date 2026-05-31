# ByteSavor V3.0 后端开发日志

## 这个项目是什么

ByteSavor 是一个 AI 饮食助手。用户拍一张冰箱/食材的照片（或者打字说"家里有牛肉和南瓜，30分钟做个减脂餐"），系统自动识别食材、推荐菜谱、生成购物清单。

整个系统的架构在飞书文档里定义好了，核心思想叫 **B-Y-T-E 智能闭环**：

| 阶段 | 英文 | 做什么 | 对应接口 |
|------|------|--------|---------|
| B | Perception | 看懂图片里的食材 | `/v1/sense/analyze` |
| Y | Decision | 根据食材推荐菜谱 | `/v1/decision/meal-plan` |
| T | Task | 生成购物清单 | `/v1/task/*` |
| E | Feedback | 收集用户反馈，越用越聪明 | `/v1/feedback/*` |

后端用的是 **Python FastAPI**，数据库用 **MySQL**。

---

## 项目代码在哪

```
~/Desktop/bytesavor-backend/
```

### 怎么启动

```bash
cd ~/Desktop/bytesavor-backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动后打开浏览器访问 `http://127.0.0.1:8000/docs` 就能看到所有接口的 Swagger 文档。

### 项目文件结构

```
app/
├── main.py                  # 程序入口，启动服务、注册路由
├── schemas.py               # 定义请求和响应的数据格式
│
├── core/                    # 基础设施（模块一）
│   ├── config.py            # 读 .env 配置文件
│   ├── database.py          # 连接 MySQL
│   ├── redis.py             # 连接 Redis
│   └── security.py          # JWT 登录令牌 + 密码加密
│
├── middleware/
│   └── auth.py              # 身份验证中间件
│
├── models/
│   └── __init__.py          # 数据库表结构
│
├── services/                # 业务逻辑
│   ├── user.py              # 用户注册/登录/画像
│   └── vlm/                 # AI 视觉识别
│       ├── base.py          #   provider 抽象接口
│       ├── openai.py        #   OpenAI 兼容 provider
│       └── prompts.py       #   场景 prompt 模板
│
└── routers/                 # 接口层（收 HTTP 请求，调 service，返回结果）
    ├── auth.py              # 注册 / 登录
    ├── user.py              # 用户画像 / 营养状态
    ├── sense.py             # B-感知：食材识别
    ├── decision.py          # Y-决策：菜谱推荐（暂为 Mock）
    ├── task.py              # T-执行：购物清单（暂为 Mock）
    ├── agent.py             # Agent 统一入口（暂为 Mock）
    └── feedback.py          # E-反馈（暂为 Mock）
```

---

## 模块一：基础设施（已完成）

### 做了什么

写代码之前，先把"地基"打好。模块一解决了三个问题：

1. **配置管理**：数据库地址、密码、JWT 密钥这些东西不能写死在代码里。用 `.env` 文件存，`config.py` 读。
2. **数据库连接**：让程序能连上 MySQL，支持异步（不会因为查数据库而卡住）。
3. **登录认证**：用户登录后发一个 JWT 令牌，后续请求带这个令牌就能知道是谁。

### 关键文件

**`app/core/config.py`** — 配置中心
```python
class Settings(BaseSettings):
    mysql_host: str = "127.0.0.1"    # MySQL 地址
    mysql_password: str = ""          # MySQL 密码
    jwt_secret: str = "..."           # JWT 签名密钥
    # ... 还有很多配置项
```
所有配置都从 `.env` 文件读取。换环境（开发/测试/生产）只需改 `.env`，不用改代码。

**`app/core/database.py`** — 数据库连接
```python
engine = create_async_engine("mysql+asyncmy://...")  # 异步 MySQL 引擎
async def get_db():
    async with async_session() as session:
        yield session  # 用完后自动关闭，不会泄漏连接
```

**`app/core/security.py`** — 安全相关
```python
hash_password("123456")   # → 加密后的密文
create_token(user_id)      # → JWT 令牌（24小时有效）
decode_token(token)        # → 解析出 user_id
```

**`app/middleware/auth.py`** — 身份验证
```python
async def get_current_user(cred):
    # 从 HTTP 请求的 Authorization 头里取出 token
    # 解密 → 拿到 user_id
    # 如果 token 无效或过期 → 返回 401
```

### 怎么验证模块一做好了

```
请求 /v1/user/profile（不带 token） → 401 "缺少认证信息"
请求 /v1/user/profile（带假 token） → 401 "token 无效或已过期"
```
这说明认证中间件生效了。

---

## 模块二：用户系统（已完成）

### 之前的样子（Mock）

调用 `/v1/user/profile` 永远返回一个假用户 "Louis"：
```json
{"user_id": "u_001", "name": "Louis", "goal": "fat_loss"}
```
不管谁访问、不管什么 token，返回都一样。

### 改了之后

用户数据存在 MySQL 里，不同用户看到的是自己的真实数据。

### 新增的接口

| 方法 | 路径 | 做什么 |
|------|------|--------|
| POST | `/v1/auth/register` | 注册（传 openid，首次注册/后续静默登录） |
| POST | `/v1/auth/login` | 登录（传 openid，返回 JWT token） |
| GET | `/v1/user/profile` | 查看自己的画像（需带 token） |
| PUT | `/v1/user/profile` | 修改自己的偏好（改目标、口味等） |
| GET | `/v1/nutrition/status` | 查看营养状态 |

### 数据库里存什么

建了 3 张表：

**users 表** — 用户基础信息
| 字段 | 说明 |
|------|------|
| id | 用户ID（如 `u_109351d1c8b741b0`） |
| openid | 微信 OpenID（唯一标识） |
| phone | 手机号 |
| name | 昵称 |
| created_at | 注册时间 |

**profiles 表** — 用户画像（1对1）
| 字段 | 说明 |
|------|------|
| user_id | 关联 users 表 |
| goal | 饮食目标：fat_loss / muscle_gain / balanced |
| preferences | 口味偏好列表，如 `["spicy", "high_protein"]` |
| health_score | 健康评分 |

**nutrition_logs 表** — 营养记录（1对多，每天一条）
| 字段 | 说明 |
|------|------|
| user_id | 关联 users 表 |
| score | 当日营养分数 |
| deficits | 缺乏的营养素，如 `["vitamin_c", "fiber"]` |
| recorded_at | 记录日期 |

### 完整调用流程举例

```
1. 用户首次打开小程序
   POST /v1/auth/register  { openid: "wx_abc123" }
   → 系统在 users 表建一行，profiles 表建一行（默认值）
   → 返回 { token: "eyJ...", user_id: "u_...", is_new: true }

2. 查看个人主页
   GET /v1/user/profile   (Header: Authorization: Bearer eyJ...)
   → 中间件解析 token → 拿到 user_id
   → 查 users JOIN profiles → 返回画像数据
   → { user_id, name, goal, preferences, health_score }

3. 修改偏好
   PUT /v1/user/profile   { goal: "muscle_gain", preferences: ["high_protein"] }
   → 更新 profiles 表
   → 返回更新后的数据

4. 查看营养状态
   GET /v1/nutrition/status
   → 查 nutrition_logs 表最近一条记录
   → 返回 { score: 65, deficits: ["vitamin_c"] }
```

### 代码怎么组织的

```
请求进来
  → router (auth.py / user.py)     只负责收请求、调 service、返回结果
    → service (services/user.py)    真正的业务逻辑：查数据库、判断、计算
      → model (models/__init__.py)  定义数据库表结构
```

这样分层的好处：如果以后换数据库（比如从 MySQL 换 PostgreSQL），只改 model 和 service，router 和接口完全不动。

---

## 模块三：感知层 B-Sense（已完成）

### 这个模块是干什么的

对应 B-Y-T-E 里的 **B（Perception，感知）**。用户拍一张食材照片，系统要能识别出图片里有哪些食材、新不新鲜、大概多重。

### 之前的样子（Mock）

永远返回西兰花 + 牛肉：
```json
{
  "ingredients": [
    {"name": "西兰花", "confidence": 0.98, "freshness": "high", "state": "新鲜"},
    {"name": "牛肉", "confidence": 0.95, "freshness": "normal", "state": "冷藏"}
  ],
  "portion_estimation": {"total_weight": 320}
}
```

### 改了之后

接口先尝试调用真实的 AI 视觉模型（VLM）。如果 VLM 没配（比如开发环境没有 AI 服务），自动降级返回 Mock 数据，接口不会报错。

### 怎么调用 AI 视觉模型

写在 `app/services/vlm/openai.py` 里：

```python
async def analyze_food(image_url: str) -> dict | None:
    # 1. 检查 .env 里配了 VLM 地址没有
    if not settings.vlm_api_url:
        return None  # 没配 → 上层降级 Mock

    # 2. 发 HTTP 请求给 VLM
    resp = await httpx.post(
        settings.vlm_api_url,
        json={
            "model": "qwen-vl",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": "识别图片中的食材，返回 JSON"}
                ]
            }]
        }
    )

    # 3. 从 VLM 返回中提取 JSON
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)
```

### 降级策略（重要）

4 种情况会自动降级到 Mock：
1. `.env` 里没配 VLM_API_URL → 返回 Mock
2. VLM 服务返回错误（非 200）→ 返回 Mock
3. 网络超时 → 返回 Mock
4. VLM 返回的内容解析失败 → 返回 Mock

这保证了：
- 开发时没配 VLM 也能跑
- VLM 挂了接口不会 500
- VLM 配好后自动生效，一行代码不用改

### 怎么接入真实 VLM

改 `.env` 文件：
```
VLM_API_URL=https://your-vlm-service.com/v1/chat/completions
VLM_API_KEY=sk-your-api-key
```
重启服务即可。

---

## 三个模块合起来，现在能做什么

```
用户打开小程序
  │
  ├─ 注册/登录 → 拿到 token → 存本地
  │     POST /v1/auth/register
  │
  ├─ 拍一张冰箱照片
  │     POST /v1/sense/analyze  { image_url: "https://..." }
  │     → 返回识别出的食材列表
  │
  └─ 查看个人偏好
        GET /v1/user/profile
        → 返回 { goal: "fat_loss", preferences: ["spicy"] }
```

后续模块四（Y-决策）完成后，拿到食材列表 + 用户偏好 → 推荐菜谱，整个 BYTE 链路就打通了。

---

## 模块四：决策层 Y-Decision（已完成）

### 这个模块是干什么的

对应 BYTE 里的 **Y（Decision，决策）**。拿到食材列表后，系统要像一个营养师一样推荐菜谱。

### 改了之后

不再是固定返回"香辣牛肉西兰花"。根据你传的食材、时间限制、口味、健康目标，系统从菜谱库里匹配出最合适的菜谱，按匹配度排序返回。

### 核心算法

```
硬过滤（不满足直接淘汰）
  └─ 烹饪时间 > 时间限制 → 淘汰

软排序（三个 0~1 分加权）
  ├─ 食材匹配分 (50%): 你有牛肉+西兰花, 菜谱需要牛肉+西兰花+蒜 → 67%
  ├─ 标签匹配分 (30%): 你选 spicy, 菜谱标签含 spicy → 加分
  └─ 偏好匹配分 (20%): 你喜欢 high_protein, 菜谱标签含 high_protein → 加分

探索模式（没传食材时）
  └─ 不报错, 全量推荐, 按标签+偏好排序
```

### 每条推荐都带解释

```json
{
  "title": "香辣牛肉西兰花",
  "match_score": 0.65,
  "reasons": ["已有食材: 牛肉, 西兰花", "口味匹配: spicy", "高蛋白适合减脂"]
}
```

让用户知道"为什么推荐这个"。

### 新增的关键文件

| 文件 | 作用 |
|------|------|
| `models/recipe.py` | 菜谱数据表（10 道种子菜谱） |
| `services/decision.py` | 匹配引擎：硬过滤 + 软排序 + 可解释性 |
| `services/decision_engine.py` | 抽象基类，后期换 Neo4j/GraphRAG 只需新增子类 |
| `services/nutrition.py` | 营养缺口计算 |
| `seed/recipes.json` | 10 道真实菜谱数据 |

### 审查中修复的安全问题

- **user_id 不从请求体获取**：原来 `{"user_id":"u1"}` 用户可伪造别人 ID。改为从 JWT token 解析，无法伪造。
- **硬过滤/软排序拆分**：原来分数混在一起，可能出现"用户要求 15 分钟但系统返回 60 分钟菜谱"。现在硬约束直接淘汰，不会出错。

---

## 开发规范（之后写代码遵守）

1. **router 不写业务逻辑**：router 只收请求、调 service、返回结果。真正的逻辑写在 service 里。
2. **service 返回 dict，不返回 ORM 对象**：service 和 router 之间用纯 Python 字典传数据，不用数据库对象。
3. **每个 commit / write 操作都要 rollback**：`try: commit() except: rollback()`。
4. **错误统一格式**：`{status: "error", error: {code: "XXX", message: "..."}, trace_id: "uuid"}`。全局异常处理器会兜底。
5. **接口路径不动**：Schema 可以加字段、改字段，但路由路径不删不改（前端已经对接了）。
