# ByteSavor V3.0 后端测试文档

## 一、测试环境准备

### 1.1 前置依赖
- Python 3.10+
- MySQL 8.0+（本地或远程）
- Homebrew（macOS）

### 1.2 启动 MySQL
```bash
# macOS
brew install mysql && brew services start mysql

# 设置密码
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'bytesavor'; FLUSH PRIVILEGES; CREATE DATABASE IF NOT EXISTS bytesavor CHARACTER SET utf8mb4;"
```

### 1.3 启动后端服务
```bash
cd ~/Desktop/bytesavor-backend
cp .env.example .env
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 1.4 访问 Swagger 文档
浏览器打开 `http://127.0.0.1:8000/docs`，可在此页面直接测试所有接口。

---

## 二、接口测试清单

### 模块一：用户认证 (Auth)

#### 2.1 注册新用户
```bash
curl -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"openid":"wx_test_001"}'
```
**预期**：`status: success`，`data.is_new: true`，`data.token` 非空

#### 2.2 重复注册（静默登录）
```bash
curl -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"openid":"wx_test_001"}'
```
**预期**：`status: success`，`data.is_new: false`，token 可正常使用

#### 2.3 登录未注册用户
```bash
curl -X POST http://127.0.0.1:8000/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"openid":"nonexistent_user"}'
```
**预期**：`status: error`，`error.code: USER_NOT_FOUND`

---

### 模块二：用户画像 (User)

#### 2.4 查画像（无 token → 401）
```bash
curl http://127.0.0.1:8000/v1/user/profile
```
**预期**：HTTP 401

#### 2.5 查画像（有效 token）
```bash
# 先获取 token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"openid":"wx_test_002"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

curl http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer $TOKEN"
```
**预期**：`status: success`，`data` 含 `user_id`, `name`, `goal`, `preferences`, `health_score`

#### 2.6 查画像（过期/错误 token → 401）
```bash
curl http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer invalid_token_here"
```
**预期**：HTTP 401

#### 2.7 修改偏好
```bash
curl -X PUT http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"goal":"muscle_gain","preferences":["high_protein","no_spicy"]}'
```
**预期**：`status: success`，返回更新后 `goal: muscle_gain`, `preferences: ["high_protein","no_spicy"]`

#### 2.8 确认偏好持久化
```bash
curl http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer $TOKEN"
```
**预期**：偏好与 2.7 修改后的值一致

#### 2.9 营养状态查询
```bash
curl http://127.0.0.1:8000/v1/nutrition/status \
  -H "Authorization: Bearer $TOKEN"
```
**预期**：`data.score: 0`, `data.deficits: []`（新用户无记录时的默认值）

---

### 模块三：食材感知 (Sense - B)

#### 2.10 食材识别（VLM 未配置 → 降级 Mock）
```bash
curl -X POST http://127.0.0.1:8000/v1/sense/analyze \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"t1","image_url":"https://example.com/food.jpg"}'
```
**预期**：`status: success`，返回 Mock 食材列表（西兰花+牛肉），`portion_estimation.total_weight: 320`

#### 2.11 缺图片 URL
```bash
curl -X POST http://127.0.0.1:8000/v1/sense/analyze \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"t1","image_url":""}'
```
**预期**：`status: error`，`error.code: NO_IMAGE`

---

### 模块四：菜谱决策 (Decision - Y)

#### 2.12 有食材推荐
```bash
curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":["牛肉","西兰花"],"constraints":{"time_limit":30,"taste":"spicy","goal":"fat_loss"}}'
```
**预期**：
- `data.recipes` 非空，按 `match_score` 降序
- 每条 recipe 含 `recipe_id`, `title`, `match_score`, `reasons`
- reasons 含结构化 `code`、`text`、`meta`
- 香辣牛肉西兰花应在 top 位置

#### 2.13 硬过滤验证
```bash
curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":["排骨"],"constraints":{"time_limit":15}}'
```
**预期**：不返回 60 分钟以上的菜谱（红烧排骨、冬瓜排骨汤等不应出现），如无匹配则返回 fallback 降权结果

#### 2.14 探索模式（空食材）
```bash
curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":[],"constraints":{}}'
```
**预期**：`status: success`，返回推荐菜谱列表（不应报错）

#### 2.15 未登录推荐（无 token 可调用）
```bash
curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":["鸡蛋","番茄"],"constraints":{"taste":"light","goal":"balanced"}}'
```
**预期**：正常返回推荐，番茄炒蛋排前面（无需 token）

#### 2.16 登录后偏好影响推荐
```bash
# 先改偏好为 high_protein
curl -X PUT http://127.0.0.1:8000/v1/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"preferences":["high_protein"]}'

# 再推荐
curl -X POST http://127.0.0.1:8000/v1/decision/meal-plan \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"ingredients":["牛肉"]}'
```
**预期**：高蛋白菜谱排前面，reasons 含 `PREF_MATCH` 和 `HIGH_PROTEIN_GOAL`

#### 2.17 菜谱详情
```bash
curl http://127.0.0.1:8000/v1/recipes/r_001
```
**预期**：返回 r_001 的完整信息（title, steps, ingredients, calories, protein, cook_time, difficulty）

#### 2.18 不存在的菜谱
```bash
curl http://127.0.0.1:8000/v1/recipes/r_999
```
**预期**：`status: error`，`error.code: NOT_FOUND`

---

### 模块五：任务执行 (Task - T)

#### 2.19 购物清单合并
```bash
curl -X POST http://127.0.0.1:8000/v1/task/merge-list \
  -H 'Content-Type: application/json' \
  -d '{"recipes":["r_001","r_003"]}'
```
**预期**：
- 牛肉 300g + 400g 合并为 700g
- 同名同单位食材数量累加
- 不同名单列
- display 整数值不显示 ".0"（700g 不显示 700.0g）

#### 2.20 空菜谱列表
```bash
curl -X POST http://127.0.0.1:8000/v1/task/merge-list \
  -H 'Content-Type: application/json' \
  -d '{"recipes":[]}'
```
**预期**：`status: error`，`error.code: NO_RECIPES`

#### 2.21 Agent 自然语言执行
```bash
curl -X POST http://127.0.0.1:8000/v1/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"input":"家里有牛肉和南瓜，30分钟做个减脂餐"}'
```
**预期**：
- `data.trace_id` 非空
- `data.stages` 含 3 个阶段（sense/decision/task），各含 status + latency_ms
- `data.parsed_intent` 含 goal= fat_loss, time_limit=30, ingredients=["牛肉","南瓜"]
- `data.recipes` 非空，`data.shopping_list` 非空

---

### 模块六：用户反馈 (Feedback - E)

#### 2.22 提交反馈（需登录）
```bash
curl -X POST http://127.0.0.1:8000/v1/feedback/meal \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"recipe_id":"r_001","rating":5}'
```
**预期**：`status: success`，`data.acknowledged: true`，`data.reward_points` > 0

#### 2.23 反馈后偏好自动更新
```bash
# 先记录当前偏好
curl http://127.0.0.1:8000/v1/user/profile -H "Authorization: Bearer $TOKEN"

# 高分评价 r_001（标签: spicy, high_protein, low_carb）
curl -X POST http://127.0.0.1:8000/v1/feedback/meal \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"recipe_id":"r_001","rating":5}'

# 再次查看偏好 → 应新增 spicy/high_protein/low_carb
curl http://127.0.0.1:8000/v1/user/profile -H "Authorization: Bearer $TOKEN"
```
**预期**：偏好列表比评分前增加（新增 r_001 的标签）

#### 2.24 未登录提交反馈 → 401
```bash
curl -X POST http://127.0.0.1:8000/v1/feedback/meal \
  -H 'Content-Type: application/json' \
  -d '{"recipe_id":"r_001","rating":5}'
```
**预期**：HTTP 401

---

## 三、边界与异常测试

### 3.1 极值参数
- `time_limit=5` → 硬过滤淘汰所有菜谱 → 触发 fallback 降权返回
- `ingredients=[]` → 探索模式全量推荐（不报错）
- `rating=0` → 应被 Pydantic 校验拒绝（ge=1）

### 3.2 并发测试
```bash
# 同时发 3 个请求
for i in 1 2 3; do
  curl -s http://127.0.0.1:8000/v1/recipes/r_001 &
done
wait
```
**预期**：3 个请求均正常返回，无连接错误

### 3.3 Token 过期测试
JWT 默认 24 小时过期。测试方法：手动修改 `.env` 中 `JWT_EXPIRE_MINUTES=1`，注册后等 2 分钟再请求。

**预期**：HTTP 401

---

## 四、测试检查清单

| # | 测试项 | 通过 |
|---|--------|------|
| 1 | 注册新用户 | ⬜ |
| 2 | 重复注册静默登录 | ⬜ |
| 3 | 登录未注册用户 | ⬜ |
| 4 | 无 token 查画像 → 401 | ⬜ |
| 5 | 有效 token 查画像 | ⬜ |
| 6 | 错误 token 查画像 → 401 | ⬜ |
| 7 | 修改偏好 | ⬜ |
| 8 | 偏好持久化验证 | ⬜ |
| 9 | 营养状态查询 | ⬜ |
| 10 | Sense 食材识别（Mock 降级） | ⬜ |
| 11 | Sense 缺图片 → error | ⬜ |
| 12 | Decision 有食材推荐 | ⬜ |
| 13 | Decision 硬过滤（time_limit=15） | ⬜ |
| 14 | Decision 探索模式（空食材） | ⬜ |
| 15 | Decision 未登录可调用 | ⬜ |
| 16 | Decision 登录后偏好影响排序 | ⬜ |
| 17 | 菜谱详情 | ⬜ |
| 18 | 不存在的菜谱 → NOT_FOUND | ⬜ |
| 19 | 购物清单合并（同名累加） | ⬜ |
| 20 | 购物清单 display 格式 | ⬜ |
| 21 | 空菜谱列表 → NO_RECIPES | ⬜ |
| 22 | Agent 自然语言全链路 | ⬜ |
| 23 | Agent trace_id + stages | ⬜ |
| 24 | Agent 意图解析 | ⬜ |
| 25 | 提交反馈 | ⬜ |
| 26 | 反馈后偏好自动更新 | ⬜ |
| 27 | 未登录反馈 → 401 | ⬜ |
| 28 | 并发请求 | ⬜ |
| 29 | Token 过期 | ⬜ |
