# 模块二：用户系统 实现思路

## 一、现状

### 已有接口（Mock）
| 方法 | 路径 | 当前行为 |
|------|------|---------|
| GET | `/v1/user/profile` | 返回固定用户 Louis |
| GET | `/v1/nutrition/status` | 返回固定分数 65 |

### 缺少的功能
- 用户注册 / 登录
- 用户画像持久化
- 偏好管理
- 营养状态的历史记录

---

## 二、目标

模块二完成后，以下接口返回**真实数据库数据**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/auth/register` | 新增：微信登录注册 |
| POST | `/v1/auth/login` | 新增：返回 JWT |
| GET | `/v1/user/profile` | 改：从 MySQL 查 |
| PUT | `/v1/user/profile` | 新增：修改画像 |
| GET | `/v1/nutrition/status` | 改：查最近营养记录 |
| GET | `/v1/user/history` | 改：查历史记录 |

---

## 三、数据表设计

### 3.1 users 表
```sql
CREATE TABLE users (
    id          VARCHAR(32)  PRIMARY KEY,        -- u_ + uuid hex
    openid      VARCHAR(64)  NOT NULL UNIQUE,     -- 微信 OpenID
    phone       VARCHAR(20)  DEFAULT '',
    name        VARCHAR(50)  DEFAULT '',
    avatar_url  VARCHAR(256) DEFAULT '',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.2 profiles 表
```sql
CREATE TABLE profiles (
    user_id     VARCHAR(32)  PRIMARY KEY,
    goal        VARCHAR(30)  DEFAULT '',           -- fat_loss / muscle_gain / balanced
    preferences JSON         NOT NULL,             -- ["spicy","high_protein",...]
    health_score INT         DEFAULT 60,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3.3 nutrition_logs 表
```sql
CREATE TABLE nutrition_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     VARCHAR(32)  NOT NULL,
    score       INT          NOT NULL,
    deficits    JSON         NOT NULL,             -- ["vitamin_c","fiber"]
    recorded_at DATE         NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3.4 表之间的关系
```
users (1) ──── (1) profiles
users (1) ──── (N) nutrition_logs
```

---

## 四、新增/修改的代码文件

### 4.1 新建文件

```
app/
├── models/
│   ├── __init__.py
│   └── user.py           # SQLAlchemy ORM 模型 (User, Profile, NutritionLog)
├── services/
│   └── user.py           # 用户业务逻辑 (注册、登录、查画像、改偏好)
└── routers/
    └── auth.py           # 新增: 注册/登录路由
```

### 4.2 修改文件

```
app/routers/user.py       # 改: 从 Mock → 查 MySQL
app/schemas.py            # 加: RegisterRequest, LoginRequest, ProfileUpdate
```

---

## 五、各文件详细设计

### 5.1 models/user.py —— ORM 模型

三个类对应三张表：

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String(32), primary_key=True)
    openid = Column(String(64), unique=True, nullable=False)
    phone = Column(String(20), default="")
    name = Column(String(50), default="")
    avatar_url = Column(String(256), default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Profile(Base):
    __tablename__ = "profiles"
    user_id = Column(String(32), ForeignKey("users.id"), primary_key=True)
    goal = Column(String(30), default="")
    preferences = Column(JSON, default=list)
    health_score = Column(Integer, default=60)

class NutritionLog(Base):
    __tablename__ = "nutrition_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"))
    score = Column(Integer)
    deficits = Column(JSON)
    recorded_at = Column(Date)
```

### 5.2 services/user.py —— 业务逻辑

核心函数：

```python
async def create_user(db, openid: str, phone: str = "", name: str = "") -> User
    # 1. 生成 user_id = f"u_{uuid4().hex[:16]}"
    # 2. INSERT users + INSERT profiles (默认值)
    # 3. return user

async def get_user_by_openid(db, openid: str) -> User | None
    # SELECT * FROM users WHERE openid = ?

async def get_user_by_id(db, user_id: str) -> User | None
    # 含 JOIN profiles

async def get_profile(db, user_id: str) -> dict
    # 返回 {user_id, name, goal, preferences, health_score}

async def update_profile(db, user_id: str, goal: str, preferences: list) -> None

async def get_nutrition_status(db, user_id: str) -> dict
    # SELECT * FROM nutrition_logs WHERE user_id=? ORDER BY recorded_at DESC LIMIT 1

async def get_meal_history(db, user_id: str, limit: int = 20) -> list
```

### 5.3 routers/auth.py —— 注册/登录

```
POST /v1/auth/register
  入参: { openid, phone?, name? }
  逻辑:
    1. openid 是否已存在 → 存在则直接返回 token (静默登录)
    2. 不存在 → create_user → 返回 token + user_id
  
POST /v1/auth/login
  入参: { openid }
  逻辑:
    1. 查 users 表
    2. 找到 → 返回 token + user_id
    3. 没找到 → 400 "用户未注册"
```

微信小程序的登录流程本质上是拿 `wx.login()` 的 code 换 openid，然后走注册/静默登录。这里模拟这个流程，接口直接用 openid 作为标识。

### 5.4 routers/user.py —— 改造

原来的 Mock 返回值改为从 service 层 + DB 拿：

```python
# GET /v1/user/profile —— 原来
return SuccessResponse(data={"user_id":"u_001","name":"Louis",...})

# GET /v1/user/profile —— 改成
@router.get("/v1/user/profile")
async def get_user_profile(user=Depends(get_current_user), db=Depends(get_db)):
    profile = await user_service.get_profile(db, user["sub"])
    return SuccessResponse(data=profile)
```

同理改造 `GET /v1/nutrition/status`。

---

## 六、调用链

### 首次打开小程序
```
POST /v1/auth/register { openid: "wx_xxx" }
  → services/user.create_user()
  → INSERT users + profiles
  → 返回 { token, user_id }
  → 小程序存 token，以后每次请求带 Authorization: Bearer <token>
```

### 已注册用户打开
```
POST /v1/auth/login { openid: "wx_xxx" }
  → 查到已有用户
  → 返回 { token, user_id }
```

### 查看个人主页
```
GET /v1/user/profile  (Header: Authorization: Bearer <token>)
  → middleware/auth.py: get_current_user 解析 token 拿到 user_id
  → services/user.py: get_profile(user_id)
  → 返回 { user_id, name, goal, preferences, health_score }
```

### 修改偏好
```
PUT /v1/user/profile { goal: "fat_loss", preferences: ["low_carb","no_shellfish"] }
  → services/user.py: update_profile()
  → UPDATE profiles SET ...
```

---

## 七、Schema 新增字段

```python
class RegisterRequest(BaseModel):
    openid: str = Field(..., min_length=1)

class LoginRequest(BaseModel):
    openid: str = Field(..., min_length=1)

class ProfileUpdate(BaseModel):
    goal: str | None = None
    preferences: list[str] | None = None

class AuthResponse(BaseModel):
    token: str
    user_id: str
    name: str
```

---

## 八、验证方式

模块二完成后，按顺序 curl 验证：

```bash
# 1. 注册新用户
curl -X POST localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"openid":"wx_test_001"}'
# 期望: { "status":"success", "data":{ "token":"eyJ...", "user_id":"u_...", "name":"" } }

# 2. 查看画像（未认证 → 401）
curl localhost:8000/v1/user/profile
# 期望: 401

# 3. 查看画像（带 token → 200 + 数据库数据）
curl localhost:8000/v1/user/profile \
  -H "Authorization: Bearer <token>"
# 期望: 真实数据

# 4. 修改偏好
curl -X PUT localhost:8000/v1/user/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"goal":"muscle_gain","preferences":["high_protein","no_spicy"]}'
# 期望: success

# 5. 再次查画像，确认偏好已更新
curl localhost:8000/v1/user/profile \
  -H "Authorization: Bearer <token>"
# 期望: goal=muscle_gain, preferences 已变
```

---

## 九、依赖

- 模块一（数据库连接、JWT）✅ 已完成
- MySQL 需要创建 bytesavor 数据库和表

## 十、不在本模块做的

- 微信服务器端 code→openid 的接口调用（需要微信 AppID/Secret，环境相关）
- 营养日志的写入（留给 E 反馈模块）
- B-Y-T-E 业务逻辑（留给后续模块）

---

## 十一、实现状态（2026-05-25）

### 已完成的代码文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `app/models/__init__.py` | ✅ 已完成 | User, Profile, NutritionLog 三张表 ORM |
| `app/services/user.py` | ✅ 已完成 | create_user, get_profile, update_profile, get_nutrition_status |
| `app/routers/auth.py` | ✅ 已完成 | POST /v1/auth/register, POST /v1/auth/login |
| `app/routers/user.py` | ✅ 已改造 | Mock → 查 DB + JWT 认证 |
| `app/schemas.py` | ✅ 已更新 | 新增 RegisterRequest, LoginRequest, ProfileUpdate |
| `app/main.py` | ✅ 已更新 | 注册 auth 路由, lifespan 自动建表 |

### 实现中修复的问题

- **外键约束 bug**：`create_user` 中 user 和 profile 同时 add 导致 MySQL 外键检查失败。修复：`db.add(user)` 后加 `await db.flush()` 确保 user 先写入，再 add profile
- **事务 rollback**：`create_user` 和 `update_profile` 加了 `try/except/rollback`，防止中间失败产生脏数据
- **统一异常处理**：`main.py` 加 `@app.exception_handler(Exception)` 全局捕获未处理异常，统一返回 `{status:"error", error:{code, message}, trace_id}` 格式，落地产 Contract Layer 规范
- **nutrition_logs 索引**：`recorded_at` 字段加了 `index=True`，优化按时间查询性能

### 已确认无需改

| # | 审查意见 | 实际情况 |
|---|---------|---------|
| 1 | Schema/ORM 边界 | ✅ 已分离：`models/` ORM + `schemas.py` API Schema，service 返回 dict |
| 4 | JWT 不完整 | ✅ `exp` 已有，refresh token 属 MVP 后优化 |
| 5 | 配置管理 | ✅ `pydantic-settings` + `.env`，支持多环境 |
| 7 | 伪异步 | ✅ `AsyncSession` + `asyncmy` + `create_async_engine`，真异步 |
| 8 | Agent/User 耦合 | ⚠️ 架构提醒，后续开发遵循 DDD 边界不互调原则 |

### 全链路验证结果（2026-05-25）

```
=== 1. 注册新用户 ===
{"is_new":true, "token":"eyJ...", "user_id":"u_109351d1c8b741b0"} ✅

=== 2. 重复注册（静默登录） ===
{"is_new":false, "token":"eyJ..."} ✅ 不重复创建

=== 3. 无 token 查画像 ===
401 "缺少认证信息" ✅

=== 4. 带 token 查画像 ===
{"user_id":"u_...","goal":"","preferences":[],"health_score":60} ✅ DB 真实数据

=== 5. 改偏好 ===
PUT → {"goal":"muscle_gain","preferences":["high_protein","no_spicy"]} ✅

=== 6. 再次查画像，确认已改 ===
{"goal":"muscle_gain","preferences":["high_protein","no_spicy"]} ✅

=== 7. 营养状态（无记录时） ===
{"score":0,"deficits":[]} ✅
```

### 环境

- MySQL：本地 Homebrew，root / bytesavor，库 bytesavor（含 3 张表）
- 服务：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
