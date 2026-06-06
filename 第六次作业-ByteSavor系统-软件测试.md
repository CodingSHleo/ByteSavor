# ByteSavor 系统 软件测试

组别：ByteSleep | 测试工程师：杨仁宇 李文彬

---

## 第一部分：全链路测试计划

### 1.1 系统简介

ByteSavor 是一个 AI 饮食助手，分前端小程序和后端 API。用户拍照或打字说有什么食材，系统推荐菜谱、生成购物清单、学习用户偏好。

### 1.2 全链路测试范围

前后端一起测，模拟真实用户操作流程。

| 链路 | 涉及模块 | 覆盖什么 |
|------|---------|---------|
| 注册登录 | 前端→Auth→User | 微信授权、获取token、拉取画像 |
| 拍照推荐 | 前端→Sense→Decision | 上传图片、识别食材、推荐菜谱 |
| 文字推荐 | 前端→Agent→Decision→Task | 打字输入、全链路编排、购物清单 |
| 反馈学习 | 前端→Feedback→User | 评分、偏好自动更新 |

### 1.3 测试环境

| 项目 | 说明 |
|------|------|
| 前端 | uni-app (Vue3 + Vite5 + JS)，微信小程序为主，无 TS |
| 后端 | FastAPI + MySQL 8.0，跑在 macOS |
| 网络 | 前后端通过内网 HTTP 通信 |
| AI | LLM 用 Ollama 本地 qwen2.5:1.5b，VLM 暂时 Mock 降级 |

---

## 第二部分：全链路测试用例

### 链路一：新用户注册并获取推荐

**场景**：用户第一次打开小程序，注册后拍冰箱照片，系统识别食材并推荐菜谱。

| 步骤 | 操作 | 前端表现 | 后端接口 | 预期 |
|------|------|---------|---------|------|
| 1 | 打开小程序，点微信授权 | 弹出微信授权框 | - | 获取到 openid |
| 2 | 确认授权 | 跳转首页 | POST /v1/auth/register | 返回 token，前端存本地 |
| 3 | 首页自动加载用户画像 | 显示昵称、健康目标 | GET /v1/user/profile | 新用户 goal 为空，preferences 为空 |
| 4 | 点击拍照按钮，拍冰箱 | 进入拍照页 | - | - |
| 5 | 确认上传 | 显示"识别中..." | POST /v1/sense/analyze | 返回食材列表 |
| 6 | 识别完成 | 展示食材卡片（名称、新鲜度） | - | 西兰花、牛肉等 |
| 7 | 点击"推荐菜谱" | 跳转推荐页 | POST /v1/decision/meal-plan | 返回菜谱列表 |
| 8 | 菜谱列表展示 | 显示菜谱卡片（标题、匹配分、推荐理由） | - | 香辣牛肉西兰花排第一 |
| 9 | 点一道菜谱 | 跳转详情页 | GET /v1/recipes/r_001 | 返回步骤、食材、热量 |
| 10 | 点"生成购物清单" | 弹窗显示购物清单 | POST /v1/task/merge-list | 食材合并去重 |

### 链路二：老用户打字推荐并反馈

**场景**：注册过的用户直接用文字描述需求，系统给推荐，用户吃完后打分。

| 步骤 | 操作 | 前端表现 | 后端接口 | 预期 |
|------|------|---------|---------|------|
| 1 | 打开小程序 | 自动用存储的 token 登录 | - | token 未过期，直接进入 |
| 2 | 在输入框打字"家里有牛肉和南瓜，30分钟做个减脂餐" | 输入框 | - | - |
| 3 | 点发送 | 显示"AI 思考中..." | POST /v1/agent/execute | LLM 解析意图，走完 B→Y→T |
| 4 | 显示结果 | 食材确认 + 菜谱列表 + 购物清单 | - | 意图正确解析（减脂/30分钟/牛肉/南瓜） |
| 5 | 点一道菜谱 | 菜谱详情 | GET /v1/recipes/r_003 | 南瓜炖牛肉详情 |
| 6 | 点"做完了，去打分" | 跳转评分页 | - | - |
| 7 | 给 5 星 | Toast "感谢评价" | POST /v1/feedback/meal | 写入 feedback 表 |
| 8 | 回到首页看画像 | 偏好标签多了 spicy, high_protein | GET /v1/user/profile | preferences 自动更新 |

### 链路三：异常场景

**场景**：网络中断、上传模糊图片、搜索无结果。

| 步骤 | 操作 | 预期前端表现 | 预期后端行为 |
|------|------|-------------|-------------|
| 1 | 关掉网络，点推荐 | 提示"网络异常，请重试" | - |
| 2 | 恢复网络，上传一张纯黑图 | 识别失败提示 | Sense 降级返回 Mock 数据 |
| 3 | 搜索 "xyz不存在的食材123" | 仍推荐菜谱（基于其他条件） | meal-plan 不报错，fallback 兜底 |
| 4 | 设置 time_limit=1 分钟 | 仍返回菜谱，但分数低 | 硬过滤全淘汰→走 fallback |
| 5 | 不登录直接点推荐 | 正常显示推荐 | 推荐接口不需要登录也能用 |
| 6 | 不登录点评分 | 提示"请先登录" | 401 |

---

## 第三部分：后端白盒测试（基本路径法）

参照课本例题 13.4。

### 3.1 登录逻辑 login()

#### 被测代码

```python
async def login(req, db):
    user = await get_user_by_openid(db, req.openid)   # ①
    if user is None:                                   # ②
        return ErrorResponse(...)                       # ③
    token = create_token(user.id)                       # ④
    return SuccessResponse(data={"token": token})       # ⑤
```

#### 流图

```
      ┌───┐
      │ ① │ 查数据库
      └─┬─┘
        │
      ┌─▼─┐
      │ ② │ user为None？
      └─┬─┘
       / \
      Y   N
     /     \
  ┌─▼─┐  ┌─▼─┐
  │ ③ │  │ ④ │ 生成token
  └───┘  └─┬─┘
            │
          ┌─▼─┐
          │ ⑤ │ 返回成功
          └───┘
```

#### 环形复杂度

E=5, N=5。V(G) = E - N + 2 = 5 - 5 + 2 = **2**

#### 路径

P1: ①→②→③（用户不存在，返回错误）
P2: ①→②→④→⑤（用户存在，返回token）

#### 测试用例

| 用例标识 | TC-WHITE-01 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | auth.login() |
| 测试输入 | openid="nobody"（数据库不存在） |
| 前提条件 | MySQL 正常，users 表无此 openid |
| 环境要求 | Python3.14 + FastAPI + MySQL8.0 |
| 测试步骤 | (1)启动服务 (2)POST /v1/auth/login body:{"openid":"nobody"} (3)检查响应 |
| 预期输出 | status="error", code="USER_NOT_FOUND" |

| 用例标识 | TC-WHITE-02 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | auth.login() |
| 测试输入 | openid="wx_real"（已注册） |
| 前提条件 | 先注册该 openid 写入 users 表 |
| 环境要求 | 同上 |
| 测试步骤 | (1)先 POST /v1/auth/register 注册 (2)再 POST /v1/auth/login 登录 (3)检查 |
| 预期输出 | status="success", data.token 非空, data.user_id 非空 |

---

### 3.2 食材打分 _calc_ingredient()

#### 被测代码

```python
def _calc_ingredient(r, user_ings):
    if not r.ingredients or not user_ings:    # ① 判空
        return 0.3, []                         # ② 默认分
    recipe_set = {i["name"] for i in r.ingredients}  # ③ 取菜谱食材
    user_set = {u.lower() for u in user_ings}
    exact = recipe_set & user_set              # ④ 交集
    score = min(len(exact)/len(recipe_set), 1.0)  # ⑤ 算分
    codes = [("ING_MATCH", ...) for e in exact]   # ⑥ 生成标签
    return score, codes                         # ⑦ 返回
```

#### 流图

```
      ┌───┐
      │ ① │ 判空
      └─┬─┘
       / \
      Y   N
     /     \
  ┌─▼─┐  ┌─▼─┐
  │ ② │  │ ③ │ 取名称集合
  └───┘  └─┬─┘
            │
          ┌─▼─┐
          │ ④ │ 求交集
          └─┬─┘
            │
          ┌─▼─┐
          │ ⑤ │ 算分
          └─┬─┘
            │
          ┌─▼─┐
          │ ⑥ │ 生成code
          └─┬─┘
            │
          ┌─▼─┐
          │ ⑦ │ return
          └───┘
```

#### 环形复杂度

V(G) = 判定节点 + 1 = 1 + 1 = **2**

#### 路径

P1: ①→②（空数据，直接返回 0.3）
P2: ①→③→④→⑤→⑥→⑦（正常计算）

#### 测试用例

| 用例标识 | TC-WHITE-03 |
|---------|------------|
| 用例设计者 | 李文彬 |
| 测试对象 | _calc_ingredient() |
| 测试输入 | r.ingredients=[], user_ings=["牛肉"] |
| 前提条件 | 菜谱对象的 ingredients 为空列表 |
| 环境要求 | 纯函数测试，无需数据库 |
| 测试步骤 | (1)构造空食材菜谱 (2)调 _calc_ingredient(菜谱, ["牛肉"]) (3)看返回 |
| 预期输出 | score=0.3, codes=[] |

| 用例标识 | TC-WHITE-04 |
|---------|------------|
| 用例设计者 | 李文彬 |
| 测试对象 | _calc_ingredient() |
| 测试输入 | r.ingredients=["牛肉","西兰花","蒜"], user_ings=["牛肉","西兰花"] |
| 前提条件 | 菜谱需要 3 样食材 |
| 环境要求 | 同上 |
| 测试步骤 | (1)构造菜谱 (2)调 _calc_ingredient(菜谱, ["牛肉","西兰花"]) (3)算分 |
| 预期输出 | score=2/3≈0.67, codes 含两条 ING_MATCH |

---

## 第四部分：后端黑盒测试（等价分类法）

参照课本例题 13.5。

### 4.1 用户注册 register

#### 等价类

注册只收一个 openid（非空字符串）。

| 编号 | 类型 | 描述 |
|------|------|------|
| EC-1 | 有效 | 合法 openid，没注册过 |
| EC-2 | 有效 | 合法 openid，已注册过 |
| EC-3 | 无效 | 空字符串 "" |
| EC-4 | 无效 | 不传 openid |

#### 测试用例

| 用例标识 | TC-BLACK-01 |
|---------|------------|
| 用例设计者 | 李文彬 |
| 测试对象 | POST /v1/auth/register |
| 测试输入 | {"openid":"wx_test_new"} |
| 前提条件 | MySQL 正常，该 openid 未注册 |
| 环境要求 | Python3.14 + FastAPI + MySQL8.0 |
| 测试步骤 | (1)启动服务 (2)POST register (3)检查返回 |
| 预期输出 | status="success", data.is_new=true, 有 token |

| 用例标识 | TC-BLACK-02 |
|---------|------------|
| 用例设计者 | 李文彬 |
| 测试对象 | POST /v1/auth/register |
| 测试输入 | {"openid":"wx_test_new"}（同上，重复调） |
| 前提条件 | 刚跑完 TC-BLACK-01 |
| 环境要求 | 同上 |
| 测试步骤 | (1)再次 POST 同一 openid (2)检查 |
| 预期输出 | status="success", data.is_new=false, 不重复建用户 |

| 用例标识 | TC-BLACK-03 |
|---------|------------|
| 用例设计者 | 李文彬 |
| 测试对象 | POST /v1/auth/register |
| 测试输入 | {"openid":""} |
| 前提条件 | MySQL 正常 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST 传空 openid (2)看 HTTP 状态码 |
| 预期输出 | HTTP 422（Pydantic 校验 min_length=1） |

| 用例标识 | TC-BLACK-04 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/auth/register |
| 测试输入 | {}（空 body） |
| 前提条件 | 同上 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST 空 body (2)看状态码 |
| 预期输出 | HTTP 422 |

---

### 4.2 菜谱推荐 meal-plan

#### 等价类

**食材输入分三类：**

| 编号 | 描述 |
|------|------|
| EC-A1 | 有食材，库里有匹配 |
| EC-A2 | 空列表，应走探索模式 |
| EC-A3 | 有食材但部分匹配不到 |

**时间限制分三类：**

| 编号 | 描述 |
|------|------|
| EC-B1 | 正常 30min |
| EC-B2 | 极短 5min（触发 fallback） |
| EC-B3 | 极大 999（不限时） |

#### 测试用例

| 用例标识 | TC-BLACK-05 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/decision/meal-plan |
| 测试输入 | {"ingredients":["牛肉","西兰花"],"constraints":{"time_limit":30,"taste":"spicy","goal":"fat_loss"}} |
| 前提条件 | MySQL 正常，表中有种子数据 |
| 环境要求 | Python3.14 + FastAPI + MySQL8.0 |
| 测试步骤 | (1)启动服务 (2)POST meal-plan (3)检查 |
| 预期输出 | 多条菜谱按 match_score 降序，香辣牛肉西兰花靠前 |

| 用例标识 | TC-BLACK-06 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/decision/meal-plan |
| 测试输入 | {"ingredients":[],"constraints":{}} |
| 前提条件 | 同上 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST 空食材 (2)检查 |
| 预期输出 | status="success"，有菜谱返回（不是报错） |

| 用例标识 | TC-BLACK-07 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/decision/meal-plan |
| 测试输入 | {"ingredients":["排骨"],"constraints":{"time_limit":5}} |
| 前提条件 | 含排骨的菜谱都超过 5 分钟 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST time_limit=5 (2)检查 |
| 预期输出 | 有结果返回，match_score 低，reasons 含 NEAR_FIT |

| 用例标识 | TC-BLACK-08 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/decision/meal-plan |
| 测试输入 | {"ingredients":["鸡蛋"],"constraints":{"time_limit":999}} |
| 前提条件 | 同上 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST time_limit=999 (2)检查鸡蛋菜谱是否全返回 |
| 预期输出 | 煎蛋、番茄炒蛋、韭菜炒蛋、蒸水蛋等均返回 |

| 用例标识 | TC-BLACK-09 |
|---------|------------|
| 用例设计者 | 杨仁宇 |
| 测试对象 | POST /v1/decision/meal-plan |
| 测试输入 | {"ingredients":["牛肉","xyz不知名食材123"],"constraints":{"time_limit":30}} |
| 前提条件 | 同上 |
| 环境要求 | 同上 |
| 测试步骤 | (1)POST 一个有效+一个无效食材 (2)检查 |
| 预期输出 | 正常返回，结果基于"牛肉"匹配 |
