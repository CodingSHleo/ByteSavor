# ByteSavor 全栈运行说明

本文档用于本机联调：后端 FastAPI + MySQL/Redis + 前端 UniApp H5。

## 1. 环境

- Python 3.12+，项目已带 `venv`
- Node.js 18+
- MySQL 8，Redis 7
- 项目根目录：`/Users/liwenbin930/Desktop/bytesavor-backend`
- 前端目录：`/Users/liwenbin930/Desktop/bytesavor-backend/bsapp`

## 2. 后端配置

在项目根目录准备 `.env`。可从 `.env.example` 复制，然后至少确认：

```bash
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=bytesavor
MYSQL_DB=bytesavor

REDIS_URL=redis://127.0.0.1:6379/0

JWT_SECRET=替换成一段随机长字符串

VLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
VLM_API_KEY=你的 DashScope key
VLM_MODEL=qwen-vl-max

LLM_API_URL=http://127.0.0.1:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
```

`JWT_SECRET` 不能为空，也不能是占位值，否则注册/登录会失败。

## 3. 启动基础服务

本机方式：

```bash
brew services start mysql
brew services start redis
mysql -u root -pbytesavor -e "CREATE DATABASE IF NOT EXISTS bytesavor CHARACTER SET utf8mb4;"
```

Docker 方式：

```bash
export JWT_SECRET="替换成一段随机长字符串"
docker compose up -d db redis
```

## 4. 启动后端

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：

```bash
curl http://127.0.0.1:8000/docs
```

浏览器打开：

```text
http://127.0.0.1:8000/docs
```

## 5. 启动前端 H5

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm install
npm run dev:h5
```

Uni/Vite 会输出本地地址，通常是：

```text
http://localhost:5173/
```

前端默认请求：

```text
http://127.0.0.1:8000
```

如果要切换后端地址，可在浏览器控制台设置：

```js
localStorage.setItem('api_base_url', 'http://127.0.0.1:8000')
```

然后刷新页面。

如果之前保存过错误地址，先清掉：

```js
localStorage.removeItem('api_base_url')
```

再刷新页面。H5 默认会使用当前前端页面的 hostname，并请求同 hostname 的 `:8000` 后端。

## 6. 推荐测试顺序

1. 打开前端 H5。
2. 注册/登录，确认不再返回 mock token。
3. 上传或输入图片，验证 `/v1/sense/analyze` 返回真实食材。
4. 使用 Agent 图片推荐，确认返回 `sense -> decision -> task` 三个阶段。
5. 查看菜谱详情。
6. 合并购物清单。
7. 提交反馈，再查看用户画像偏好变化。

## 7. 后端接口快速验证

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"openid":"manual_test_user"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

curl http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":["牛肉","西兰花"],"constraints":{"time_limit":30,"taste":"spicy","goal":"fat_loss"}}'

curl -X POST http://127.0.0.1:8000/v1/task/merge-list \
  -H 'Content-Type: application/json' \
  -d '{"recipes":["r_001"]}'
```

## 8. 测试

需要临时注入 JWT：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q
```

如果本机沙箱阻止访问 MySQL，需要在允许本机 3306 连接的终端里运行。

## 9. 常见问题

- 注册/登录 500：检查 `JWT_SECRET` 是否为空或仍是占位值。
- 前端请求失败：确认后端在 `8000`，前端 API base 是 `http://127.0.0.1:8000`。
- 注册页显示网络异常：先在浏览器控制台执行 `localStorage.removeItem('api_base_url')`，刷新后重试。
- 图片识别返回 mock：检查 `VLM_API_URL`、`VLM_API_KEY`、后端日志里的 `vlm_http` / `vlm_parse_failed`。
- 推荐为空：确认 MySQL 里已 seed 菜谱，后端启动日志应包含 `seed loaded`。
- H5 跨域：后端已放行 `localhost/127.0.0.1:5173/5174`。
