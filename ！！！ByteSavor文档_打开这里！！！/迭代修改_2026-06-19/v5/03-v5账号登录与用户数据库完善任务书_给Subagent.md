# ByteSavor v5 账号登录与用户数据库完善任务书（给 Subagent）

日期：2026-06-20  
执行对象：subagent  
前置条件：先完成或至少不冲突于 `25-v5基础工程化任务书_给Subagent.md`。  
任务性质：认证与用户数据库基础完善。  

---

## 0. 当前账号系统现状

当前账号系统是演示级：

后端：

- `app/routers/auth.py`
- `app/services/user.py`
- `app/core/security.py`
- `app/models/__init__.py` 中 `User`
- `app/schemas.py` 中 `RegisterRequest` / `LoginRequest`

前端：

- `bsapp/src/pages/login/login.vue`
- `bsapp/src/pages/register/register.vue`
- `bsapp/src/api/index.js`
- `bsapp/src/store/auth.js`

测试：

- `tests/test_auth.py`

当前行为：

1. 注册只需要 `openid` 和可选 `name`。
2. 登录只需要 `openid`。
3. 前端直接输入“微信ID/OpenID”。
4. 没有密码。
5. `User` 表没有正式账号字段：
   - 没有 `username`
   - 没有 `email`
   - 没有 `password_hash`
   - 没有 `auth_provider`
   - 没有 `last_login_at`
   - 没有 `status`
6. `app/core/security.py` 已经有 `hash_password()` 和 `verify_password()`，但业务没使用。

这个模式适合演示，不适合真实用户注册登录。

---

## 1. v5 账号目标

本轮目标：

1. 新增正式账号注册/登录：用户名 + 密码。
2. 保留旧 openid 演示登录兼容，不破坏现有测试和前端旧流程。
3. 用户表补齐必要字段。
4. 注册时校验用户名和密码。
5. 登录时校验密码。
6. 前端登录页增加密码输入。
7. 前端注册页增加账号、密码、确认密码。
8. 测试覆盖新旧两套登录路径。

不做：

1. 不做短信验证码。
2. 不做微信 `code2session` 真接入。
3. 不做找回密码。
4. 不做邮箱验证。
5. 不做第三方 OAuth。
6. 不做用户管理后台。

---

## 2. 数据库设计要求

### 2.1 User 表新增字段

在 `app/models/__init__.py` 的 `User` 增加：

```python
username = Column(String(64), unique=True, nullable=True, index=True)
email = Column(String(120), unique=True, nullable=True, index=True)
password_hash = Column(String(128), default="")
auth_provider = Column(String(30), default="openid")  # openid / password / wechat
status = Column(String(20), default="active")         # active / disabled
last_login_at = Column(DateTime, nullable=True)
```

注意：

- `openid` 暂时保留，兼容旧数据。
- `username` 允许 nullable，避免旧 openid 用户迁移失败。
- `password_hash` 不返回给前端。

### 2.2 临时迁移方式

当前项目还没有 Alembic，所以本轮允许继续使用 `ensure_*` 风格，但必须集中到 user service。

在 `app/services/user.py` 新增：

```python
async def ensure_user_auth_columns(db: AsyncSession) -> None:
    ...
```

检查并补齐：

- `username`
- `email`
- `password_hash`
- `auth_provider`
- `status`
- `last_login_at`

不要把 ALTER 语句散落在 router。

后续 Alembic 会单独做，不在本轮做。

---

## 3. API 设计要求

### 3.1 注册接口兼容旧格式

现有：

```json
POST /v1/auth/register
{
  "openid": "demo",
  "name": "小明"
}
```

新增支持：

```json
POST /v1/auth/register
{
  "username": "demo_user",
  "password": "Aa123456",
  "name": "小明"
}
```

兼容策略：

- 如果传了 `username/password`，走正式密码账号注册。
- 如果只传 `openid`，走旧演示注册。
- 不允许 `username` 和 `openid` 都为空。

### 3.2 登录接口兼容旧格式

现有：

```json
POST /v1/auth/login
{
  "openid": "demo"
}
```

新增支持：

```json
POST /v1/auth/login
{
  "username": "demo_user",
  "password": "Aa123456"
}
```

兼容策略：

- 如果传了 `username/password`，走密码登录。
- 如果只传 `openid`，走旧演示登录。
- 密码错误返回：

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "账号或密码错误"
  }
}
```

- 用户不存在不要暴露“用户名不存在”还是“密码错”，正式账号统一 `INVALID_CREDENTIALS`。
- 旧 openid 登录找不到用户，仍可返回 `USER_NOT_FOUND`，保持兼容。

### 3.3 密码规则

前后端都要校验：

```text
长度 >= 8
至少一个大写字母
至少一个小写字母
至少一个数字
```

后端必须校验，前端校验只是体验优化。

错误码：

```text
WEAK_PASSWORD
USERNAME_TAKEN
INVALID_USERNAME
INVALID_CREDENTIALS
```

### 3.4 Token payload

当前 token：

```python
{"sub": user_id, "openid": openid, "exp": expire}
```

可以保留，但建议新增：

```python
{"sub": user_id, "openid": openid, "username": username, "exp": expire}
```

如果不改 `create_token()` 签名，也可以暂不加 username。不要破坏 `get_current_user()`。

---

## 4. 后端实现任务

### 文件

- 修改：`app/models/__init__.py`
- 修改：`app/services/user.py`
- 修改：`app/routers/auth.py`
- 修改：`app/schemas.py`
- 修改：`tests/test_auth.py`

### 必须新增 service 函数

```python
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    ...
```

```python
async def create_password_user(db: AsyncSession, username: str, password: str, name: str = "", email: str = "") -> User:
    ...
```

```python
async def authenticate_password_user(db: AsyncSession, username: str, password: str) -> User | None:
    ...
```

```python
def validate_password_strength(password: str) -> tuple[bool, str]:
    ...
```

### 密码哈希

必须使用已有：

```python
from app.core.security import hash_password, verify_password
```

严禁明文存储密码。

### 用户名规范

建议：

```text
3-32 位
只能包含字母、数字、下划线、短横线
```

可以使用正则：

```python
^[A-Za-z0-9_-]{3,32}$
```

---

## 5. 前端实现任务

### 文件

- 修改：`bsapp/src/pages/login/login.vue`
- 修改：`bsapp/src/pages/register/register.vue`
- 修改：`bsapp/src/api/index.js`
- 可选修改：`bsapp/src/utils/i18n.js`

### 登录页要求

当前登录页是 openid 输入。改为：

1. 默认显示正式账号登录：
   - 用户名
   - 密码
2. 保留一个“演示 OpenID 登录”折叠/切换入口。
3. 密码输入使用 password 类型。
4. 登录中按钮 disabled。
5. 错误展示后端 message。

### 注册页要求

注册页改为：

- 昵称
- 用户名
- 密码
- 确认密码

前端校验：

- 用户名非空。
- 密码符合规则。
- 两次密码一致。

保留演示 OpenID 注册入口可以放在底部小链接，不要作为主流程。

### API Service

改成支持对象参数，避免参数越来越乱：

```js
async login(payload) {
  // payload: { username, password } or { openid }
}

async register(payload) {
  // payload: { username, password, name } or { openid, name }
}
```

兼容旧调用：

如果现有代码还有：

```js
ApiService.login(openid)
ApiService.register(openid, name)
```

可以在函数里兼容：

```js
if (typeof payload === 'string') {
  data = { openid: payload }
}
```

---

## 6. 测试要求

### 修改 `tests/test_auth.py`

必须覆盖：

1. 旧 openid 注册仍然可用。
2. 旧 openid 登录仍然可用。
3. 用户名密码注册成功。
4. 重复用户名注册失败：`USERNAME_TAKEN`。
5. 弱密码注册失败：`WEAK_PASSWORD`。
6. 密码错误登录失败：`INVALID_CREDENTIALS`。
7. 正确密码登录成功。
8. 登录返回 token、user_id、name。
9. profile token 仍然可用。
10. `password_hash` 不出现在任何响应中。

### 验收命令

DB 环境：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_auth.py
```

全 DB 集合：

```bash
./scripts/verify_db.sh
```

前端构建：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

---

## 7. 数据库检查要求

subagent 在修改前后都要检查用户表结构。

### 修改前检查

```sql
DESCRIBE users;
```

记录当前字段。

### 修改后检查

```sql
DESCRIBE users;
```

必须看到：

```text
username
email
password_hash
auth_provider
status
last_login_at
```

如果没有命令行 MySQL 权限，可以写一个临时只读检查脚本，但不要提交临时脚本。

---

## 8. 安全要求

必须满足：

1. 密码永远不返回给前端。
2. `password_hash` 永远不返回给前端。
3. 密码错误不说明“密码错”或“用户不存在”，统一 `INVALID_CREDENTIALS`。
4. 弱密码不能注册。
5. username 要 trim。
6. username 查询要规范化，建议小写存储。
7. 旧 openid 兼容路径必须注释说明“演示用”。

---

## 9. 文档要求

新增：

```text
docs/迭代修改/30-v5账号登录与用户数据库修复记录.md
```

同步：

```text
！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/30-v5账号登录与用户数据库修复记录.md
```

文档必须包含：

1. 修改前用户表结构。
2. 修改后用户表结构。
3. 新旧登录兼容说明。
4. 密码规则。
5. 测试命令和结果。
6. 前端页面变化。
7. 剩余风险。

---

## 10. 工作量预估

| 模块 | 预估 |
|---|---:|
| User 表字段 + ensure 函数 | 0.5 天 |
| 后端注册/登录逻辑 | 0.5 天 |
| auth 测试补齐 | 0.5 天 |
| 前端登录/注册表单 | 0.5-1 天 |
| 文档和验证 | 0.2 天 |

总计：约 2-3 天。

---

## 11. 交接口径

当前账号系统不是生产账号系统，而是演示登录。

v5 账号任务完成后的正确口径：

> ByteSavor 已从 OpenID 演示登录升级为用户名密码账号体系，并兼容旧 OpenID 演示路径。后端使用 bcrypt 哈希密码，用户表补齐账号字段，前端登录/注册支持密码输入，测试覆盖新旧登录路径。

不要说：

> 已完成微信生产登录。

微信 `code2session` 是后续单独任务。
