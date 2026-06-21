# ByteSavor 社区、收藏、库存清点扩展说明

## 已完成能力

本次扩展把社区、收藏、菜谱库和库存清点接入真实前后端链路。

### 后端

- 新增库存管理接口：
  - `POST /v1/inventory/items`
  - `PUT /v1/inventory/items/{item_id}`
  - `DELETE /v1/inventory/items/{item_id}`
  - `GET /v1/inventory/stats`
- 新增菜谱清点器：
  - `POST /v1/recipes/check`
  - 支持 `system_recipe` 和 `community_post`
  - 返回已有食材、缺少食材、购物清单、匹配比例、是否可做
- 新增收藏：
  - `GET /v1/favorites`
  - `POST /v1/favorites`
  - `DELETE /v1/favorites`
  - `GET /v1/favorites/status`
  - 收藏保存 `snapshot`，社区帖变化后仍能展示基本信息
- 新增社区：
  - 图文/菜谱/健康咨询/饮食打卡帖子
  - 点赞、评论、作者删除
  - 菜谱帖必须有结构化 `recipe_payload.ingredients`，才能进入清点器
- Agent 扩展：
  - 当用户问“收藏的菜现在库存能不能做/缺什么”时，会调用 `inventory`、`favorites`、`recipe_check` 工具
  - Agent 事件流会显示这些工具调用结果，不再只是普通推荐 API

### 前端

- 底栏改为：首页 / 识别 / 菜谱 / 社区 / 我的。
- 菜谱页从“探索菜谱”升级为“菜谱库”，每张菜谱支持：
  - 收藏
  - 清点
  - 进入详情
- 首页推荐菜谱支持：
  - 收藏
  - 清点
  - 加入计划
- 菜谱详情页收藏已接后端，不再是假心形状态。
- 补齐旧页面引用的 `icon_*.svg` 图标资源，避免登录、首页、菜谱、清单、设置等页面出现图标空白。
- 新增页面：
  - `pages/inventory/inventory`：库存管理
  - `pages/recipe-checker/recipe-checker`：菜谱清点器
  - `pages/favorites/favorites`：我的收藏
  - `pages/community/community`：社区 feed
  - `pages/community-detail/community-detail`：帖子详情
  - `pages/community-publish/community-publish`：发布内容
- 我的页新增入口：
  - 我的收藏
  - 库存管理
  - 我的社区

## 主流程

1. 用户拍照识别或手动添加食材，写入 `ingredient_inventory`。
2. 用户在菜谱库搜索或从首页推荐选择菜谱。
3. 点击“清点”，后端用当前库存和菜谱食材做比较。
4. 如果缺食材，可以导入购物清单；如果想吃，可以加入今日计划。
5. 加入计划不会计入摄入。
6. 用户点击“完成这一餐”后，才写入营养统计并扣减库存。
7. 完成后评分评论写入偏好记忆，后续推荐会读取。
8. 社区菜谱可以被收藏、清点、加入自己的链路。

## 测试结果

已通过：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_auth.py tests/test_decision.py tests/test_meals_inventory.py \
  tests/test_feedback_memory.py tests/test_food_guide.py \
  tests/test_inventory_stats.py tests/test_recipe_checker.py \
  tests/test_favorites.py tests/test_community.py \
  tests/test_community_recipe_flow.py tests/test_agent_tools_inventory_favorites.py \
  tests/test_agent.py tests/test_agent_runtime.py tests/test_langgraph_agent.py
```

结果：`38 passed, 2 warnings`。

前端构建已通过：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

镜像前端也已同步并构建通过：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/frontend/bytesavorapptest5_31/bytesavorapptest5_31/bytesavor-uniapp
npm run build:h5
```

## 剩余风险

- 当前账号仍是 openid + JWT 演示认证，不是密码体系。生产需要微信 `code2session` 或密码哈希。
- 图片上传还没有正式对象存储，社区图片字段目前是 JSON 结构预留。
- 库存单位换算是 MVP：同单位可精确比较，不同单位会保守标记缺少/待确认。
- 社区内容没有审核系统，健康咨询需要继续保持“非医疗建议”边界。
- 菜谱搜索仍主要在前端过滤/后端全量返回，数据量继续增长后应加分页和 SQL 预过滤。
- 新增图标为轻量线性 SVG，已解决 404/空白问题；后续如果追求统一品牌质感，可以再替换成完整设计系统图标。
静态资源检查：

- 已扫描 `bsapp/src` 中 `/static/icons/...` 引用。
- 当前 26 个图标引用均存在对应资源，未发现缺失。

