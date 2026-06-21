# ByteSavor 社区、收藏、菜谱清点器与库存统计扩展设计

## Goal

把 ByteSavor 从“拍照识别后调用推荐 API”的体验，升级成围绕用户账号、食材库存、菜谱库、收藏、社区内容和用餐闭环运转的饮食操作系统。新增社区不是孤立论坛，而是让社区菜谱可以进入收藏、清单、库存清点、今日计划、完成摄入、偏好学习这条主链路。

## Current Evidence

已检查的本地证据：

- 后端模型：[app/models/__init__.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/models/__init__.py)
- 菜谱模型：[app/models/recipe.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/models/recipe.py)
- 后端入口：[app/main.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/main.py)
- 认证接口：[app/routers/auth.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/routers/auth.py)
- 推荐接口：[app/routers/decision.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/routers/decision.py)
- 库存和用餐接口：[app/routers/meals.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/routers/meals.py)
- 库存和用餐服务：[app/services/meal_memory.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/services/meal_memory.py)
- 推荐服务：[app/services/decision.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/services/decision.py)
- 用户画像和营养目标：[app/services/user.py](/Users/liwenbin930/Desktop/bytesavor-backend/app/services/user.py)
- 前端 API：[bsapp/src/api/index.js](/Users/liwenbin930/Desktop/bytesavor-backend/bsapp/src/api/index.js)
- 前端页面配置：[bsapp/src/pages.json](/Users/liwenbin930/Desktop/bytesavor-backend/bsapp/src/pages.json)
- 首页 Agent/推荐/三餐：[bsapp/src/pages/home/home.vue](/Users/liwenbin930/Desktop/bytesavor-backend/bsapp/src/pages/home/home.vue)
- 探索菜谱页：[bsapp/src/pages/explore/explore.vue](/Users/liwenbin930/Desktop/bytesavor-backend/bsapp/src/pages/explore/explore.vue)
- 自动化测试：[tests/test_meals_inventory.py](/Users/liwenbin930/Desktop/bytesavor-backend/tests/test_meals_inventory.py)

当前已有能力：

- 真实账号注册和登录已落到 `users` 表，认证方式是演示环境的 openid + JWT。当前不是密码注册体系，生产微信小程序应改为 code2session。
- 已有 `profiles`、`ingredient_inventory`、`meal_records`、`nutrition_logs`、`feedback`、`preference_memories`。
- 已有拍照识别、品质鉴定、一餐营养分析、探店向导、文本导入、首页 Agent、今日三餐计划、完成用餐后写营养和扣库存。
- 已有菜谱库 `recipes`，推荐接口可按食材、目标、偏好、回避信号排序。
- 已有测试覆盖账号、推荐、Agent、库存扣减、反馈偏好、探店增强等主路径。

当前缺口：

- 收藏仍是局部 UI 状态，不是数据库能力。
- 探索菜谱只是菜谱列表，不知道用户当前库存、缺什么、能做什么。
- 社区不存在；用户不能发布图文菜谱、评论、点赞，也不能把别人菜谱导入自己的清单。
- 库存缺少独立管理页，手动买菜、修改数量、删除食材、按库存找菜都没有成体系。
- Agent 还没有把收藏、社区菜谱、库存清点器作为工具纳入编排，因此容易被质疑只是聊天框调用推荐 API。

## Constraints

- 不破坏现有 B-Y-T-E 主线：识别/输入食材 -> 推荐菜谱 -> 导出清单/加入计划 -> 完成用餐 -> 写营养和偏好。
- 任何发帖、收藏、导入清单、加入计划都不能直接算摄入；只有“完成这一餐”才能写 `meal_records.status=completed` 和营养汇总。
- 社区健康咨询只能做饮食经验交流，不做医疗诊断。
- 当前项目没有正式迁移工具，表结构扩展要延续现有启动时 `Base.metadata.create_all` + 小型兼容迁移的风格。
- 当前仓库有大量未提交改动，实施时不得回滚用户已有代码。
- 前端是 uni-app/Vue，后端是 FastAPI + SQLAlchemy async + MySQL/SQLite 测试环境。
- 图标系统存在缺失风险，新增页面不能继续引用不存在的图标。

## Product Design

### Core Objects

本次扩展围绕四个核心对象展开：

1. 食材库存：用户当前拥有什么、数量是多少、来源是什么、是否新鲜。
2. 菜谱库：系统菜谱 + 社区结构化菜谱，能搜索、筛选、查看详情。
3. 收藏菜谱：用户喜欢或稍后想做的菜谱，来源可以是系统菜谱或社区菜谱。
4. 用餐计划和完成记录：把菜谱放到早餐/午餐/晚餐/加餐/宵夜/自定义餐时，完成后扣库存、写营养、触发偏好学习。

### Main User Flows

**库存到做饭：**

用户拍照识别或手动添加食材 -> 进入库存 -> 在菜谱页按“当前库存可做”筛选 -> 选择菜谱 -> 清点器显示已有/缺少/数量差额 -> 加入今日计划 -> 吃完后完成 -> 扣库存、写营养、评分学习偏好。

**收藏到复用：**

用户在首页推荐、菜谱库、菜谱详情、社区帖子看到喜欢的菜 -> 点击收藏 -> 我的页可查看收藏 -> 以后从收藏进入清点器 -> 按当前库存判断能不能做。

**社区到主链路：**

用户 B 发布结构化菜谱帖 -> 用户 A 浏览社区 -> 收藏或导入清单 -> 清点器比较用户 A 的库存 -> 加入计划 -> 完成用餐。健康咨询类帖子只支持阅读、评论、点赞、收藏，不支持直接导入清单。

**Agent 升级：**

用户问“我收藏的南瓜牛肉能不能用现在库存做？”Agent 应调用收藏读取、库存读取、菜谱清点器，给出缺少项和下一步按钮，而不是只做普通推荐。

## Data Model Design

### New Tables

`community_posts`

- `id`: integer primary key
- `user_id`: foreign key to `users.id`
- `title`: string
- `content`: text/string
- `category`: `recipe` / `health` / `checkin`
- `images`: JSON array
- `recipe_payload`: JSON object, only meaningful for recipe posts
- `like_count`: integer
- `comment_count`: integer
- `created_at`, `updated_at`

`community_comments`

- `id`: integer primary key
- `post_id`: foreign key to `community_posts.id`
- `user_id`: foreign key to `users.id`
- `content`: string
- `created_at`

`community_likes`

- `id`: integer primary key
- `post_id`: foreign key to `community_posts.id`
- `user_id`: foreign key to `users.id`
- `created_at`
- unique `(post_id, user_id)`

`recipe_favorites`

- `id`: integer primary key
- `user_id`: foreign key to `users.id`
- `target_type`: `system_recipe` / `community_post`
- `target_id`: string
- `snapshot`: JSON object
- `created_at`
- unique `(user_id, target_type, target_id)`

### Existing Table Enhancements

`ingredient_inventory` 已有 `name`、`amount`、`unit`、`source`、`freshness`、`confidence`、`meta`。第一阶段不强行迁移更多字段，但服务层要补齐：

- 手动新增
- 修改数量/单位/新鲜度
- 删除食材
- 批量导入后去重合并
- 按当前库存计算可做菜谱

`meal_records` 已有 `recipe_snapshot`、`ingredients_used`、`nutrition`，适合承接系统菜谱和社区菜谱的快照。社区菜谱完成后也写快照，不依赖原帖长期存在。

## API Design

### Inventory

- `POST /v1/inventory/import`: 保留，用于识别和批量导入。
- `GET /v1/inventory/current`: 保留。
- `POST /v1/inventory/items`: 手动新增单个食材。
- `PUT /v1/inventory/items/{item_id}`: 修改数量、单位、新鲜度。
- `DELETE /v1/inventory/items/{item_id}`: 删除食材。
- `GET /v1/inventory/stats`: 返回来源、数量、新鲜度、可做菜谱数量等统计。

### Recipe Library And Checker

- `GET /v1/recipes`: 扩展 query 参数：`q`、`tag`、`source`、`inventory=fit|near|all`、`favorite=true`。
- `GET /v1/recipes/{recipe_id}`: 保留。
- `POST /v1/recipes/check`: 输入 `target_type` 和 `target_id`，返回已有、缺少、数量差额、可做比例、建议购物清单。
- `POST /v1/recipes/search`: 可选；如果 GET 参数足够，先不新增。

### Favorites

- `GET /v1/favorites`
- `POST /v1/favorites`
- `DELETE /v1/favorites`
- `GET /v1/favorites/status?target_type=&target_id=`

### Community

- `GET /v1/community/posts`
- `POST /v1/community/posts`
- `GET /v1/community/posts/{post_id}`
- `DELETE /v1/community/posts/{post_id}` author-only
- `POST /v1/community/posts/{post_id}/like`
- `DELETE /v1/community/posts/{post_id}/like`
- `GET /v1/community/posts/{post_id}/comments`
- `POST /v1/community/posts/{post_id}/comments`

### Agent Tools

第一阶段不改 Agent 总入口形态，新增可被 Agent 调用的工具函数：

- `get_current_inventory(user_id)`
- `search_recipes(q, inventory_mode, user_id)`
- `check_recipe_against_inventory(target_type, target_id, user_id)`
- `list_favorites(user_id)`
- `get_community_recipe(post_id)`

当用户问题包含“收藏”“社区”“我现在有什么”“缺什么”“能不能做”时，Agent planner 应优先调用这些工具。

## Frontend Design

### Navigation

推荐底栏：

- 首页：保留 B-Y-T-E 总览、今日三餐、Agent、下一餐推荐。
- 识别：保留拍照识别入口，并继续能导入库存。
- 菜谱：由现有“探索”升级，承担系统菜谱、库存可做、收藏、社区菜谱搜索。
- 社区：新增图文/菜谱/健康咨询 feed。
- 我的：用户画像、身体数据、营养目标、收藏、我的发布、历史、设置。

“知识”不作为 tab 保留，可放进首页快捷入口或我的页工具区，避免底栏过满。

### New Pages

- `pages/inventory/inventory.vue`: 当前库存管理，支持手动添加、编辑、删除、按库存找菜。
- `pages/recipe-checker/recipe-checker.vue`: 菜谱清点器，展示已有/缺少/数量差额/加入购物清单/加入计划。
- `pages/favorites/favorites.vue`: 我的收藏，系统和社区菜谱统一展示。
- `pages/community/community.vue`: 社区 feed。
- `pages/community-detail/community-detail.vue`: 帖子详情、评论、点赞、收藏、导入清单。
- `pages/community-publish/community-publish.vue`: 发布图文或结构化菜谱。

### Component Rules

- 统一菜谱卡片要支持：收藏按钮、清点按钮、加入计划、来源标签。
- 收藏按钮必须读后端状态，不再只改本地变量。
- 图标必须使用已存在资源或新增完整资源，禁止继续引用不存在的 `icon_*.svg`。
- 社区菜谱卡必须明确标识“来自社区”，营养值可以标注为“用户估算/未验证”。

## Negative Review

- 如果先做社区，会出现“能发帖但不能服务饮食闭环”的空功能。因此实施顺序应先做库存清点器和收藏，再做社区。
- 如果收藏不做快照，社区帖被删除后收藏页会断；所以收藏表需要 `snapshot`。
- 如果菜谱清点器只比较食材名称，不处理数量和单位，用户会继续遇到“明明只有一个西瓜/一份饭，却算成多份”的问题。MVP 先支持同单位精确比较，跨单位换算作为风险明确保留。
- 如果 Agent 不接新工具，新增页面再多也不能回答“我们的 Agent 做了什么”。Agent 必须把库存、收藏、菜谱清点器纳入工具链。
- 如果社区健康咨询没有边界文案，演示时会有医学建议风险。
- 如果直接把“知识”替换成“社区”但不保留知识入口，用户之前的功能会消失。需要迁移入口。

## Verification

自动化测试：

- `tests/test_inventory_stats.py`
- `tests/test_recipe_checker.py`
- `tests/test_favorites.py`
- `tests/test_community.py`
- `tests/test_agent_tools_inventory_favorites.py`

前端验证：

- `npm run build:h5`
- 浏览器检查：首页、识别、菜谱、社区、我的五个 tab 可达。
- 冒烟流程：注册新账号 -> 手动加库存 -> 搜索菜谱 -> 清点缺少 -> 收藏 -> 加入计划 -> 完成 -> 评分 -> 营养和库存更新。

角色 demo：

- 场景一：家庭做饭，拍照识别后推荐并清点。
- 场景二：买菜清单，缺少项导入清单。
- 场景三：品质鉴定，仍保持独立入口。
- 场景四：营养分析，完成摄入后更新营养目标。
- 场景五：探店向导，仍由 VLM + LLM 补全故事和吃法。
- 新场景六：社区收藏，别人发布菜谱 -> 我收藏 -> 我按库存清点并加入计划。

