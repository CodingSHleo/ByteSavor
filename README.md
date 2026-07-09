# ByteSavor

ByteSavor 是一个面向饮食场景的多模态 Agent 系统，覆盖食材识别、菜谱推荐、用餐计划、库存/购物清单、营养记录、偏好记忆和社区分享。系统采用 B-Y-T-E 闭环设计：

- **B / Sense**：图片或文本感知食材、菜品、品质和探店场景。
- **Y / Decision**：结合食材、时间、健康目标、库存和用户偏好生成推荐。
- **T / Task**：采纳菜谱后加入用餐计划，联动库存扣减和补购清单。
- **E / Feedback**：完成用餐后记录摄入，把评分和文字反馈沉淀为长期偏好。

项目已经完成 H5 和微信小程序端适配；测试同学可优先用 H5 全栈链路测试，同一套前端代码也可构建 `mp-weixin`。

## 当前规模

统计口径：`app`、`bsapp/src`、`tests`、`scripts`、`evals` 下的 `.py/.js/.vue` 文件。

| 指标 | 当前规模 |
|---|---:|
| 测试文件 | 30 个 |
| 测试用例/测试函数 | 179 个 |
| 源码/测试脚本文件 | 155 个 |
| 代码行数 | 23,455 行 |

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | uni-app / Vue 3 / Vite 5 |
| 后端 | FastAPI / Pydantic / SQLAlchemy Async |
| 数据库 | MySQL 8 / Redis |
| Agent | LangGraph Harness / Skill Registry / Runtime Evaluator / Offline Eval |
| AI | Qwen-VL 兼容视觉接口 / DeepSeek 或 OpenAI 兼容 LLM |
| 测试 | pytest / Eval Runner / 前端静态回归脚本 |

## 目录结构

```text
app/                  FastAPI 后端、Agent、业务服务、ORM
app/seed/recipes.json 菜谱种子数据，服务启动时自动导入
bsapp/                uni-app 前端，支持 H5 和微信小程序构建
demo_tests/           演示/测试图片和手工测试素材
docs/                 架构、测试、迭代和交付文档
evals/                黑箱 Eval 用例、runner、评分器和报告
scripts/              一键验证、DB 验证、Eval API 验证、演示缓存预热
tests/                后端、Agent、推荐、社区、用餐计划等测试
```

## 环境要求

- Python 3.10+，建议 3.12
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- 可选：Qwen-VL / DeepSeek / Ollama 等 OpenAI 兼容模型接口

## 本地启动

### 1. 克隆和安装依赖

```bash
git clone https://github.com/CodingSHleo/ByteSavor.git
cd ByteSavor

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd bsapp
npm install
cd ..
```

### 2. 准备 MySQL 和 Redis

可以用本机服务，也可以用 Docker Compose 启动数据库：

```bash
docker compose up -d db redis
```

本机 MySQL 示例：

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bytesavor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

至少需要配置：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DB=bytesavor
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET=请替换为随机长字符串
```

AI 接口可选。不配置时，核心后端、推荐、用餐计划、社区和大部分测试仍可运行；视觉识别和 LLM 增强能力会走降级或跳过外部调用。

```env
VLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
VLM_API_KEY=你的视觉模型Key
VLM_MODEL=qwen-vl-max
LLM_API_URL=https://api.deepseek.com/v1/chat/completions
LLM_API_KEY=你的LLM Key
LLM_MODEL=deepseek-chat
```

不要把真实 `.env` 或 API Key 提交到 GitHub。

### 4. 启动后端

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动后访问：

- Swagger：`http://127.0.0.1:8000/docs`
- Agent 入口：`POST /v1/agent/execute`

### 5. 启动前端 H5

```bash
cd bsapp
npm run dev:h5
```

默认会启动本地 H5 页面，前端 API 地址在 `bsapp/src/api/index.js` 中配置。

### 6. 构建微信小程序

```bash
cd bsapp
npm run build:mp-weixin
```

然后用微信开发者工具打开生成目录，按微信平台要求配置合法域名、HTTPS、隐私协议和版本审核。

## 测试入口

推荐测试同学先看：

- [docs/FULLSTACK_TESTING.md](docs/FULLSTACK_TESTING.md)
- [docs/TEST_PLAN.md](docs/TEST_PLAN.md)
- [demo_tests/README.md](demo_tests/README.md)

常用命令：

```bash
# 非 DB 核心测试 + Eval mock + H5 构建
./scripts/verify_quick.sh

# 前端搜索/推荐/页面回归
node scripts/verify_frontend_regressions.mjs

# DB 相关测试，需要 MySQL/Redis 和 .env
./scripts/verify_db.sh

# 后端已启动后，跑 API 模式 Eval
API_BASE=http://127.0.0.1:8000 ./scripts/verify_eval_api.sh

# 串联主要验证，DB/API 可通过开关启用
./scripts/test_fullstack.sh
RUN_DB=1 RUN_API_EVAL=1 ./scripts/test_fullstack.sh
```

## 推荐测试账号

项目支持真实注册/登录，测试同学可自行注册。建议使用独立测试账号，避免不同测试人员数据互相污染：

```text
账号：tester@example.com
密码：Test123456
昵称：测试同学
```

如需清空数据，可重建 `bytesavor` 数据库；后端启动时会自动建表并导入 `app/seed/recipes.json`。

## 手工测试主线

1. 注册/登录，确认新用户没有继承其他用户数据。
2. 使用 `demo_tests` 图片测试拍照识别、品质鉴定、探店向导。
3. 输入“番茄牛肉减脂30分钟”，确认推荐优先覆盖番茄和牛肉。
4. 点击加入这一餐，检查用餐计划、菜品清单、购物清单。
5. 完成这一餐，检查今日营养和历史记录变化。
6. 提交“少油一点、喜欢快炒”等反馈，检查偏好记忆影响下一轮推荐。
7. 测试社区发布图片、点赞/取消点赞、收藏/取消收藏。

## 数据说明

- `app/seed/recipes.json`：菜谱种子数据，服务启动自动导入。
- `demo_tests/`：演示图片和测试素材，可用于人工测试视觉识别、品质鉴定、探店和营养分析。
- `evals/cases/quick.jsonl`：Agent 黑箱 Eval 快速用例。

## 常见问题

### 1. 后端启动后没有菜谱？

确认 MySQL 可连接，重启后端。`app.main` 的 lifespan 会自动建表并调用 `app/seed/seed_recipes.py` 导入菜谱。

### 2. 视觉识别失败？

检查 `VLM_API_URL`、`VLM_API_KEY`、`VLM_MODEL`。没有配置视觉模型时，可以先测试非视觉链路：登录、推荐、用餐计划、社区、Eval mock。

### 3. DB 测试连接不上 MySQL？

确认 `.env` 中 MySQL 配置正确，或使用：

```bash
docker compose up -d db redis
```

再运行：

```bash
./scripts/verify_db.sh
```

### 4. 前端请求不到后端？

确认后端在 `http://127.0.0.1:8000` 运行，并检查 `bsapp/src/api/index.js` 中的 API 基地址。

