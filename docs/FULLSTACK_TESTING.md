# ByteSavor 全栈测试交付说明

这份文档给测试同学使用，目标是从 GitHub 拉下代码后，能快速跑起后端、前端、数据库、测试脚本，并按业务主线做人工验收。

## 1. 测试范围

| 模块 | 覆盖内容 |
|---|---|
| 账号 | 注册、密码登录、用户数据隔离 |
| 识别 | 拍照识别、品质鉴定、探店向导、VL 缓存/超时 |
| 推荐 | 食材硬约束、偏好融合、菜谱搜索搜广推 |
| Agent | Planner、Skill 调度、事件流、运行时 Evaluator |
| 用餐计划 | 餐次切换、加餐/宵夜、加入这一餐、完成/取消 |
| 库存/清单 | 采纳菜谱后库存扣减、缺失食材补购清单 |
| 营养 | 完成用餐后今日营养变化，推荐不覆盖真实摄入 |
| 偏好 | 评分和自由文本反馈写入长期记忆 |
| 社区 | 图片发布、点赞/取消、收藏/取消、详情页 |
| Eval | mock 模式、API 模式黑箱 Eval |

## 2. 环境准备

### 后端

```bash
cd ByteSavor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DB=bytesavor
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET=test-local-secret-change-me
```

如果没有本机 MySQL/Redis，可以使用 Docker：

```bash
docker compose up -d db redis
```

### 前端

```bash
cd bsapp
npm install
```

## 3. 启动服务

### 启动后端

```bash
cd ByteSavor
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动后打开：

```text
http://127.0.0.1:8000/docs
```

### 启动 H5 前端

另开一个终端：

```bash
cd ByteSavor/bsapp
npm run dev:h5
```

终端会输出本地访问地址，通常是：

```text
http://localhost:5173
```

或：

```text
http://localhost:5174
```

## 4. 一键验证命令

### 快速基线

不要求启动后端，不要求 MySQL 可用。会跑核心非 DB 测试、Eval mock、H5 构建：

```bash
./scripts/verify_quick.sh
```

### 前端静态回归

检查推荐搜索、解释标签、社区 API 调用、Tab 图标等关键前端回归点：

```bash
node scripts/verify_frontend_regressions.mjs
```

### DB 测试

需要 MySQL/Redis 和 `.env`：

```bash
./scripts/verify_db.sh
```

### API 模式 Eval

需要后端已经启动：

```bash
API_BASE=http://127.0.0.1:8000 ./scripts/verify_eval_api.sh
```

### 全栈脚本

默认跑 quick + 前端回归：

```bash
./scripts/test_fullstack.sh
```

带 DB 和 API Eval：

```bash
RUN_DB=1 RUN_API_EVAL=1 API_BASE=http://127.0.0.1:8000 ./scripts/test_fullstack.sh
```

## 5. 人工验收主线

### 5.1 账号与数据隔离

1. 注册新账号。
2. 登录后检查首页、用餐计划、社区个人状态。
3. 确认新用户不会自动继承旧用户库存、用餐计划、收藏和点赞状态。

建议测试账号：

```text
账号：tester@example.com
密码：Test123456
昵称：测试同学
```

### 5.2 推荐与 Agent

输入：

```text
番茄牛肉减脂30分钟
```

期望：

- 推荐结果优先覆盖“番茄”和“牛肉”。
- 不应该复用上一轮“青椒牛肉”等旧结果。
- 不应出现“耗油牛肉”错别字，应为“蚝油”。
- 推荐卡片展示已用食材、缺失食材、推荐理由。
- 如果缺食材，应说明建议购买什么，而不是无解释替换成无关菜。

### 5.3 加入这一餐与用餐计划

1. 在推荐结果点击“加入这一餐”。
2. 检查今日用餐计划中对应餐次出现该菜。
3. 检查餐次可以切换：早餐、午餐、晚餐、加餐、宵夜。
4. 检查菜品清单和购物清单。
5. 点击完成这一餐。
6. 检查今日营养数据变化，并且刷新后仍保持真实记录。

### 5.4 偏好反馈

完成用餐后输入反馈：

```text
味道不错，但下次少油一点，我喜欢快炒。
```

期望：

- 反馈成功提交。
- 后续推荐能体现“少油”“快炒”等偏好。

### 5.5 识别、品质鉴定、探店

使用 `demo_tests/` 中图片：

- `场景一_拍照推荐`：普通食材/菜品识别。
- `场景三_品质鉴定`：不要在没有声音、重量的情况下编造“敲击声”“重量感”等依据。
- `场景四_营养分析`：营养估算和记录链路。
- `场景五_探店向导`：刺身饭/拼盘识别和讲解。

期望：

- 识别失败时有明确错误提示。
- 同一张 demo 图片重复识别应命中缓存或明显更快。
- 探店向导不要直接返回“无法识别”。

### 5.6 社区

1. 发布带图片的社区内容。
2. 点赞一次应变为已点赞，再点一次取消。
3. 收藏一次应变为已收藏，再点一次取消。
4. 进入详情页，检查正文摘要、图片、点赞/收藏状态。

## 6. 小程序构建

```bash
cd bsapp
npm run build:mp-weixin
```

然后使用微信开发者工具打开构建产物。小程序正式体验需要配置：

- 微信 AppID。
- HTTPS 后端域名。
- request/uploadFile 合法域名。
- 隐私协议和平台审核信息。

## 7. 数据与重置

后端启动时会自动建表，并导入：

```text
app/seed/recipes.json
```

如果要重置本地数据：

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS bytesavor; CREATE DATABASE bytesavor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

然后重启后端。

## 8. 测试通过标准

建议最终验收至少满足：

- `./scripts/verify_quick.sh` 通过。
- `node scripts/verify_frontend_regressions.mjs` 通过。
- 有 MySQL/Redis 环境时 `./scripts/verify_db.sh` 通过。
- 后端启动后 `./scripts/verify_eval_api.sh` 通过。
- H5 人工主线从注册到完成一餐、偏好反馈、社区互动能跑通。

