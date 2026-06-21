# ByteSavor 本轮迭代更新说明

更新时间：2026-06-17  
范围：前端 H5/UniApp、FastAPI 后端、MySQL 数据模型、Agent 工具链、测试与演示环境

## 1. 目标

本轮迭代的目标不是单点修 UI 或单点修接口，而是把 ByteSavor 从“调用若干 API 的饮食工具”推进到更完整的“围绕用户、库存、菜谱、社区、摄入反馈运转的饮食 Agent 系统”。

本轮重点包括：

- 账号注册/登录接入真实后端与数据库，支持不同账号隔离数据。
- 首页、识别、菜谱、社区、我的五个主导航恢复并扩展功能。
- 新增社区、收藏、库存清点、手动菜谱选择、食材统计等功能。
- 拍照识别后的清单、确认摄入、餐食完成、营养记录形成更清晰流程。
- Agent 不只返回文字，而是能读取库存、收藏、菜谱清点等工具结果参与推荐。
- 修复登录/注册“请求失败”、图标缺失、按钮不可见、注册后状态不一致等实际演示风险。

## 2. 当前证据

本轮检查和修改过的关键目录：

- 后端入口：`app/main.py`
- 后端路由：`app/routers/`
- 后端服务：`app/services/`
- 数据模型：`app/models/__init__.py`
- 前端页面：`bsapp/src/pages/`
- 前端 API 封装：`bsapp/src/api/index.js`
- 前端路由与 TabBar：`bsapp/src/pages.json`
- 测试用例：`tests/`

当前主要前端页面包括：

- 登录：`pages/login/login`
- 注册：`pages/register/register`
- 首页：`pages/home/home`
- 拍照识别：`pages/ingredient-recognition/ingredient-recognition`
- 清单导出与确认摄入：`pages/list-export/list-export`
- 菜谱探索：`pages/explore/explore`
- 菜谱详情：`pages/recipe-detail/recipe-detail`
- 健康看板：`pages/health-dashboard/health-dashboard`
- 社区：`pages/community/community`
- 社区详情：`pages/community-detail/community-detail`
- 社区发布：`pages/community-publish/community-publish`
- 我的收藏：`pages/favorites/favorites`
- 我的库存：`pages/inventory/inventory`
- 菜谱清点器：`pages/recipe-checker/recipe-checker`
- 一餐营养分析：`pages/meal-nutrition/meal-nutrition`
- 探店向导：`pages/food-guide/food-guide`
- 食材品质判断：`pages/quality-assessment/quality-assessment`
- 文本导入：`pages/text-import/text-import`

## 3. 本轮功能更新

### 3.1 账号与登录流程

新增和修复点：

- 注册、登录接口继续使用 `/v1/auth/register` 和 `/v1/auth/login`。
- 后端使用 `openid` 创建真实用户记录，写入 MySQL `users` 表。
- 注册时同步创建 `profiles` 用户画像。
- 前端注册页改为复用统一的 `authStore.setAuthData()`，避免注册后本地登录态和登录页不一致。
- 登录页和注册页都保存 `auth_token`、`user_id`、`username` 等统一字段。

本次实际问题定位：

- `8000` 端口曾被另一个项目占用，导致 ByteSavor 鉴权接口返回 404。
- 正确 ByteSavor 后端启动后，注册和登录接口可以返回 token。
- H5 在 `localhost` 下请求后端时可能先走 IPv6 `::1`，而后端监听 IPv4；前端默认 API 地址已改为 `localhost -> 127.0.0.1`。
- 非 200 响应现在会透出后端真实错误信息，例如“用户未注册”，不再只显示笼统的“请求失败”。

### 3.2 社区功能

新增后端：

- `app/routers/community.py`
- `app/services/community.py`
- `CommunityPost`
- `CommunityComment`
- 社区点赞关系表

新增前端：

- `pages/community/community`
- `pages/community-detail/community-detail`
- `pages/community-publish/community-publish`

能力：

- 不同账号可以发布社区内容。
- 内容支持菜谱、健康咨询、饮食经验等类别。
- 支持点赞、取消点赞、评论。
- 社区菜谱可以进入详情，并作为后续收藏、导入清单、菜谱清点的来源。

设计意图：

社区不是单纯展示页，而是让“用户生成菜谱/经验”进入系统数据流。用户看到别人发布的菜谱后，可以收藏、检查自己缺什么食材，再决定是否加入自己的饮食计划。

### 3.3 收藏菜谱

新增后端：

- `app/routers/favorites.py`
- `app/services/favorites.py`
- `RecipeFavorite`

新增前端：

- `pages/favorites/favorites`
- 菜谱卡片、菜谱详情、社区菜谱等位置加入收藏入口。

能力：

- 用户可收藏系统菜谱或社区菜谱。
- 收藏数据按账号隔离。
- “我的”页面可以进入收藏总览。
- 收藏菜谱可作为未来手动选择、Agent 推荐、菜谱清点器的输入来源。

### 3.4 库存与菜品清点器

新增后端：

- `app/routers/inventory.py`
- `app/services/inventory.py`
- `app/routers/recipe_tools.py`
- `app/services/recipe_checker.py`
- `IngredientInventory`

新增前端：

- `pages/inventory/inventory`
- `pages/recipe-checker/recipe-checker`

能力：

- 拍照识别或手动输入后，食材可以进入个人库存。
- 库存支持新增、编辑、删除。
- 库存统计可以展示当前拥有的食材数量、来源、状态等。
- 菜谱清点器可以对某一道菜谱检查“已有食材”和“缺少食材”。
- 用户不必完全依赖 Agent 推荐，也可以主动搜索或选择菜谱，再让系统判断缺什么。

设计意图：

这个模块解决之前“推荐菜谱像单向 API 返回”的问题。系统现在有一个更真实的中间状态：用户当前拥有什么食材。推荐、购物清单、营养计划都应围绕这个状态变化。

### 3.5 餐食计划与营养记忆

新增后端：

- `app/routers/meals.py`
- `app/services/meal_memory.py`
- `MealRecord`

更新前端：

- `pages/list-export/list-export`
- `pages/health-dashboard/health-dashboard`
- `pages/meal-nutrition/meal-nutrition`
- `pages/home/home`

能力：

- 拍照识别结果先形成“本次清单”，不会自动计入今日摄入。
- 用户点击“确认摄入/加入今天计划”后，才进入当天餐食计划。
- 支持早餐、午餐、晚餐，以及自定义餐时覆盖加餐、宵夜等场景。
- 完成一餐后，才写入长期营养记录。
- 记录出错后可以在后续页面删除或调整。
- 今日摄入和营养目标可以在健康看板查看。

设计意图：

这修正了之前的流程问题：识别食物不等于用户已经吃了。真实流程应是：

1. 识别食材或餐食。
2. 用户修正和确认。
3. 选择是否加入今天计划。
4. 吃完后完成这一餐。
5. 写入长期营养与偏好记忆。
6. 根据剩余食材和营养缺口推荐下一餐。

### 3.6 偏好反馈与长期记忆

更新后端：

- `app/services/feedback.py`
- `app/routers/feedback.py`
- `PreferenceMemory`

能力：

- 完成一餐后可以进行评分。
- 用户可补充“喜欢/不喜欢的原因”。
- 后端将评分和文本反馈写入偏好记忆。
- 推荐系统可以读取偏好记忆，影响排序与推荐理由。

设计意图：

这让 Agent 闭环更接近真实：不是只在本次请求里推荐，而是把用户长期选择和评价纳入下一次推荐。

### 3.7 Agent 工具链增强

更新后端：

- `app/routers/agent.py`
- `app/agent/runtime.py`
- `app/agent/langgraph_runtime.py`
- `app/agent/planner.py`
- `app/agent/state.py`

Agent 可调用的工具扩展为：

- `sense`：图像/食材识别
- `decision`：菜谱推荐
- `task`：购物清单合并
- `nutrition`：营养分析
- `quality`：食材品质判断
- `guide`：探店向导
- `inventory`：读取和使用个人库存
- `favorites`：读取收藏菜谱
- `recipe_check`：菜谱清点

本轮改进后的 Agent 定位：

- 不是只把一句话转发给大模型。
- 它有用户状态：账号、画像、偏好、库存、收藏、今日摄入。
- 它有工具：能查库存、查收藏、查菜谱、做营养分析、合并清单。
- 它有执行阶段：感知、理解、决策、执行、反馈。
- 它能把结果同步给前端可操作模块，而不是只显示一段文本。

还需要继续加强的点：

- Agent 对话 UI 仍可继续增强多轮上下文展示。
- 工具调用过程可视化还可以更清楚地呈现给答辩老师。
- 长期记忆参与推荐的权重仍需要更多测试样本调优。

### 3.8 多角色独立功能入口

本轮保留“一个 Agent 可以完成一切”的方向，同时增加了独立页面和独立接口，便于测试和答辩展示。

对应关系：

- 厨房用户：拍照识别食材、导出清单、库存管理、推荐下一餐。
- 健康管理用户：一餐营养分析、今日摄入、周趋势、营养目标。
- 探店用户：菜品识别、历史故事、口味技法、最佳吃法。
- 采购用户：缺少食材、购物清单、库存补充。
- 社区用户：发布菜谱、评论、点赞、收藏、导入自己的计划。

这样做的原因：

- 单一识别接口覆盖所有场景会让前端语义不清。
- 分角色页面能让演示更稳定，也更符合期末展演“功能设计是否合理、有逻辑性、符合功能场景”的评分点。
- Agent 作为总入口保留，但独立功能页承担可控演示和回归测试。

## 4. UI 与交互更新

本轮 UI 重点不是大面积换皮，而是在原有风格基础上补齐功能深度：

- 恢复并保留底部 TabBar：首页、识别、菜谱、社区、我的。
- 首页加入更强的信息看板感，不再像功能很少的单页工具。
- 图标系统补齐，减少 `icon_xxx.svg` 缺失导致的小图标不显示。
- 菜谱、清单、识别、购物、收藏等关键操作加入明确按钮。
- 修复部分按钮白底白字、不可见、点击反馈弱的问题。
- 清单页区分“本次识别食物营养”和“今日累计摄入/缺口”。

仍需注意：

- H5、手机浏览器、小程序端对 SVG、rpx、fixed TabBar 的表现可能不同。
- 答辩前应在真实手机上走完整 demo，并截图保存关键页面。

## 5. 后端数据模型更新

本轮新增或强化的数据表概念：

- `users`：真实注册账号。
- `profiles`：用户画像、目标、偏好、身体数据、营养目标。
- `ingredient_inventory`：个人食材库存。
- `meal_records`：今日餐食计划与完成记录。
- `preference_memories`：评分与文本反馈解析后的偏好记忆。
- `recipe_favorites`：收藏菜谱。
- `community_posts`：社区内容。
- `community_comments`：社区评论。
- 社区点赞关系表：记录用户点赞状态。

核心数据流：

```text
注册/登录
  -> 用户画像
  -> 拍照识别/文本导入/手动录入
  -> 食材库存
  -> 菜谱推荐或手动选择
  -> 菜谱清点
  -> 加入今日餐食计划
  -> 完成这一餐
  -> 写入营养记录与偏好记忆
  -> 下一次 Agent 推荐读取库存、偏好、收藏和营养缺口
```

## 6. 运行与测试地址

电脑端 H5 测试地址：

```text
http://localhost:5174/
```

后端文档地址：

```text
http://127.0.0.1:8000/docs
```

手机端测试注意：

- 手机不能访问自己设备上的 `localhost` 来连接电脑服务。
- 手机应打开电脑局域网 IP，例如：

```text
http://电脑局域网IP:5174/
```

- 后端也必须能从手机访问：

```text
http://电脑局域网IP:8000/docs
```

## 7. 本轮验证

已经执行过的验证：

- 后端 `/docs` 可访问。
- `/v1/auth/register` 注册新账号成功。
- `/v1/auth/login` 使用同账号登录成功。
- 默认 `demo` 账号登录成功。
- 前端 H5 构建通过：

```bash
npm run build:h5
```

构建结果：

```text
DONE  Build complete.
```

已存在测试文件覆盖方向：

- `tests/test_auth.py`
- `tests/test_decision.py`
- `tests/test_meals_inventory.py`
- `tests/test_inventory_stats.py`
- `tests/test_recipe_checker.py`
- `tests/test_favorites.py`
- `tests/test_community.py`
- `tests/test_community_recipe_flow.py`
- `tests/test_agent_tools_inventory_favorites.py`
- `tests/test_feedback_memory.py`
- `tests/test_food_guide.py`
- `tests/test_agent.py`
- `tests/test_agent_runtime.py`
- `tests/test_langgraph_agent.py`

由于当前环境对本地 MySQL 连接存在沙箱限制，部分 pytest 在沙箱内会报：

```text
Can't connect to MySQL server on '127.0.0.1' ([Errno 1] Operation not permitted)
```

这不是业务断言失败，而是当前工具环境访问本地 MySQL 被限制。真实运行时以后端实际服务和接口 curl 为准。

## 8. 负面审查

### 8.1 账号系统仍是演示级

当前仍以 `openid` 直传作为账号标识，适合课程演示，不适合生产环境。生产环境应接微信 `code2session` 或标准用户名密码/手机号验证码，并做好密码哈希、登录限流和账号恢复。

### 8.2 Agent 闭环还需要更强可解释性

虽然 Agent 已接入库存、收藏、菜谱清点、营养分析等工具，但前端还可以进一步展示：

- 本次调用了哪些工具。
- 每个 stage 耗时多少。
- 哪些外部模型降级了。
- 推荐结果为什么使用或没使用某个食材。

这对答辩非常重要，因为老师可能会质疑“这是不是只是 API 串联”。

### 8.3 推荐算法仍需更多离线评估

当前推荐已经考虑食材、标签、偏好、营养目标，但权重仍需要通过 demo 测试和人工标注进一步调优。建议后续补充 20-50 条“输入食材 -> 期望菜谱”的离线评估集。

### 8.4 库存扣减和营养写入仍要严测

演示中最容易出错的是：

- 同一个食材被识别成多个候选。
- 用户修改数量后，营养估算是否同步变化。
- 完成一餐后库存是否扣减。
- 删除摄入记录后，今日营养是否回滚。

这部分需要用角色测试逐条走。

### 8.5 手机端网络仍需现场确认

电脑浏览器 `localhost` 正常，不代表手机能访问。现场演示前必须确认：

- 电脑和手机在同一网络。
- 防火墙允许 5174 和 8000。
- 前端 storage 中没有残留旧的 `api_base_url`。

如有残留，可在浏览器开发者工具或页面设置中清除本地缓存。

## 9. 建议 Demo 流程

推荐现场演示顺序：

1. 注册一个新账号，证明用户进入真实数据库。
2. 登录后进入首页，展示今日看板为空或初始状态。
3. 拍照识别食材，手动删除/修正错误候选。
4. 导出清单，展示本次食材营养和今日缺口。
5. 加入今日餐食计划，选择早餐/午餐/晚餐或自定义餐时。
6. 完成这一餐，填写评分和偏好原因。
7. 回到健康看板，展示今日摄入变化。
8. 进入菜谱清点器，选择一道菜谱，展示已有和缺少食材。
9. 收藏菜谱，在“我的收藏”查看。
10. 发布一条社区菜谱，用另一个账号登录后点赞/评论。
11. 最后回到 Agent，输入“牛肉南瓜减脂30分钟”，说明 Agent 会结合库存、偏好、营养缺口和菜谱工具给出推荐。

## 10. 后续优先级

P0：

- 继续稳定登录/注册现场网络环境。
- 确保手机端能访问电脑后端。
- 完整走一遍 demo_test 角色流程。

P1：

- Agent 工具调用过程前端可视化。
- 库存扣减和营养回滚补充自动化测试。
- 偏好记忆参与推荐的展示说明。

P2：

- 社区内容图片上传持久化。
- 菜谱搜索和筛选体验增强。
- 推荐算法离线评估集。

P3：

- 生产级账号体系。
- 更正式的数据库迁移工具。
- 更完整的部署脚本和环境自检。

