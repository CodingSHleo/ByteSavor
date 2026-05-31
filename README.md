# ByteSavor V3.0 后端

一个基于 AI Agent 的饮食全链路系统后端，按 B-Y-T-E（感知-决策-执行-反馈）闭环设计。用户拍照或打字描述食材，系统自动推荐菜谱、生成购物清单，并根据用户反馈持续学习偏好。

## 技术栈

- FastAPI + Pydantic（API 框架）
- SQLAlchemy async + MySQL（数据库）
- Ollama + OpenAI 兼容接口（本地 LLM / VLM）
- JWT（身份认证）
- Redis（缓存，连接已配置）

## 环境要求

- Python 3.10+
- MySQL 8.0+
- Ollama（可选，本地跑 LLM 用）

## 快速开始

**1. 克隆项目**
```bash
git clone https://github.com/CodingSHleo/ByteSavor.git
cd ByteSavor
```

**2. 装 MySQL 并建库**
```bash
# macOS
brew install mysql && brew services start mysql

# 设密码并建库
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'bytesavor'; FLUSH PRIVILEGES; CREATE DATABASE IF NOT EXISTS bytesavor CHARACTER SET utf8mb4;"
```

**3. 装 Python 依赖**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. 配置环境变量**
```bash
cp .env.example .env
```

`.env` 里需要改的：
- `MYSQL_PASSWORD` — MySQL 密码
- `VLM_API_URL` / `LLM_API_URL` — 如果跑本地模型，填 ollama 地址

**5. 启动**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger 接口文档，可以页面上直接调接口测试。

## 跑本地 AI（可选）

用 Ollama 跑本地模型来做意图解析：

```bash
# 装 Ollama
brew install ollama && brew services start ollama

# 下拉模型
ollama pull qwen2.5:1.5b

# 配 .env
LLM_API_URL=http://127.0.0.1:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
```

配好重启服务，Agent 的自然语言解析就会走真实 LLM 推理（不配的话自动降级正则匹配，不影响系统运行）。

本地 VLM 食材识别目前还没有稳定跑通，这部分会降级返回 Mock 数据。如果有云端 VLM API（比如 Qwen-VL），填 `VLM_API_URL` 就能直接用。

## 接口总览

全部接口在 `/docs` 页面上有 Swagger 文档。

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/v1/auth/register` | 注册/静默登录 |
| 认证 | POST | `/v1/auth/login` | 登录 |
| 用户 | GET | `/v1/user/profile` | 查画像（需登录） |
| 用户 | PUT | `/v1/user/profile` | 改偏好 |
| 用户 | GET | `/v1/nutrition/status` | 营养状态 |
| 感知 | POST | `/v1/sense/analyze` | 食材识别 |
| 决策 | POST | `/v1/decision/meal-plan` | 推荐菜谱 |
| 决策 | GET | `/v1/recipes/{id}` | 菜谱详情 |
| 执行 | POST | `/v1/task/merge-list` | 合并购物清单 |
| 执行 | POST | `/v1/agent/execute` | Agent 统一入口（自然语言） |
| 反馈 | POST | `/v1/feedback/meal` | 提交评分反馈 |

## 目录结构

```
app/
├── main.py                # 入口，注册路由和异常处理
├── schemas.py             # 请求/响应数据模型
├── core/                  # 基础设施
│   ├── config.py          # 环境配置
│   ├── database.py        # MySQL 连接
│   ├── redis.py           # Redis 连接
│   └── security.py        # JWT + 密码
├── middleware/
│   └── auth.py            # 认证中间件
├── models/                # 数据库 ORM
│   ├── __init__.py        # User / Profile / NutritionLog / Feedback
│   └── recipe.py          # 菜谱
├── routers/               # 接口层
│   ├── auth.py / user.py  # 认证和用户
│   ├── sense.py           # B-感知
│   ├── decision.py        # Y-决策
│   ├── task.py / agent.py # T-执行
│   └── feedback.py        # E-反馈
├── services/              # 业务逻辑
│   ├── user.py            # 用户逻辑
│   ├── decision.py        # 推荐引擎（检索-过滤-排序-fallback）
│   ├── shopping.py        # 购物清单合并
│   ├── agent.py           # BYTE 全链路编排
│   ├── feedback.py        # 反馈 + 偏好学习
│   ├── nutrition.py       # 营养计算
│   ├── llm.py             # LLM 调用
│   └── vlm/               # VLM provider 抽象
└── seed/                  # 种子数据
    ├── recipes.json       # 10 道菜谱
    └── seed_recipes.py    # 导入脚本
```

## 测试

详细测试文档见 `TEST_PLAN.md`，覆盖 29 个测试用例。快速验证：

```bash
# 启动服务后
# 1. 注册
curl -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"openid":"test_001"}'

# 2. Agent（自然语言全链路）
curl -X POST http://127.0.0.1:8000/v1/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"input":"家里有牛肉和南瓜，30分钟做个减脂餐"}'
```

## 联系

后端开发：李文彬 (23306041)
有问题提 GitHub Issue。
