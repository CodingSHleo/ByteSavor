# ByteSavor v5 社区模块完善任务书（给 Subagent）

日期：2026-06-20  
执行对象：subagent  
前置条件：先完成 `25-v5基础工程化任务书_给Subagent.md`，不要和基础工程化脚本混在同一轮大改。  
任务性质：社区业务闭环完善，不重做社区页面，不做大规模 UI 重构。

---

## 0. 当前社区模块现状

当前已经有基础社区能力：

后端：

- `app/routers/community.py`
- `app/services/community.py`
- `CommunityPost`
- `CommunityComment`
- `CommunityLike`

前端：

- `bsapp/src/pages/community/community.vue`
- `bsapp/src/pages/community-detail/community-detail.vue`
- `bsapp/src/pages/community-publish/community-publish.vue`

测试：

- `tests/test_community.py`
- `tests/test_community_recipe_flow.py`

已具备能力：

- 创建帖子。
- 列表按分类筛选。
- 查看详情和评论。
- 点赞/取消点赞。
- 评论。
- 作者删除帖子。
- 社区菜谱可收藏、可清点食材。

但现在社区仍属于“能跑的 MVP”，还不是完整产品闭环。

---

## 1. 当前主要缺口

### 1.1 后端语义不够严谨

当前问题：

1. `delete_post()` 对不存在帖子返回 `deleted=False`，路由仍返回 success，前端难以区分“已删”和“不存在”。
2. `like_post()` / `unlike_post()` 对不存在帖子返回 `{"error": "NOT_FOUND"}`，但 HTTP 仍是 success。
3. `list_posts(category=xxx)` 对非法 category 没有明确错误，可能返回空列表。
4. `CommunityPostRequest` 字段太宽松：
   - title 可以空字符串，靠 service 抛错。
   - category 没有 schema 约束。
   - images 没有限制长度/类型。
   - recipe_payload 没有结构化 schema。
5. 评论没有删除能力。
6. 帖子返回没有 `liked_by_me`，前端无法显示当前用户是否已点赞。
7. 列表没有分页，数据多了以后会一次性返回全部。

### 1.2 前端社区体验不完整

当前问题：

1. 社区列表没有 loading 骨架和错误态。
2. 发布按钮未处理未登录状态。
3. 发布页缺少前端校验：
   - 标题为空仍可点发布。
   - recipe 分类没有食材时才由后端报错。
   - health/checkin 没有针对性字段。
4. 点赞按钮没有 liked 状态，只能一直“点赞”。
5. 评论没有空态、发送中状态、失败提示。
6. 社区菜谱卡片没有展示结构化食材/热量/步骤摘要，和“菜谱分享”的价值不明显。
7. 删除帖子没有前端入口，虽然后端有删除接口。
8. 没有分页/加载更多。

### 1.3 测试覆盖不足

当前测试覆盖了 happy path，但缺少：

1. 非作者删除 forbidden。
2. 删除不存在帖子。
3. 点赞不存在帖子。
4. 重复点赞不增加计数。
5. 取消点赞计数减少。
6. 非法 category。
7. recipe 帖无 ingredients 返回错误。
8. 空评论返回错误。
9. 列表分页。
10. `liked_by_me` 当前用户态。

---

## 2. v5 社区完善目标

本轮社区只做“闭环完善”，不做复杂社交系统。

完成后应达到：

1. 后端错误语义清楚。
2. 列表支持分页。
3. 当前用户可看到 `liked_by_me`。
4. 前端有基本 loading/error/empty 状态。
5. 发布页有前端校验。
6. 详情页能点赞/取消点赞、评论、作者删除。
7. 社区菜谱卡片能展示食材摘要，并能继续收藏/清点。
8. 测试覆盖核心异常和边界。

---

## 3. 严禁事项

subagent 不要做这些：

1. 不要重写整个社区 UI。
2. 不要引入图片上传服务。
3. 不要引入关注/私信/推荐流。
4. 不要改数据库大结构，除非必要字段极少。
5. 不要做 WebSocket 实时评论。
6. 不要把社区和 Agent Eval 混在一个任务里。
7. 不要影响现有收藏、清点、菜谱详情链路。

---

## 4. Task 1：后端错误语义收口

### 文件

- 修改：`app/routers/community.py`
- 修改：`app/services/community.py`
- 测试：`tests/test_community.py`

### 要求

#### 1. 删除不存在帖子

当前：

```python
deleted, code = await community.delete_post(...)
return SuccessResponse(data={"deleted": deleted})
```

要求：

- 不存在返回 `ErrorResponse(code="POST_NOT_FOUND")`
- 非作者返回 `ErrorResponse(code="FORBIDDEN")`
- 删除成功返回 `deleted=True`

#### 2. 点赞/取消点赞不存在帖子

当前 service 返回 dict 内嵌 error，但 router 仍 success。

要求：

- `like_post()` 不存在返回 `ErrorResponse(code="POST_NOT_FOUND")`
- `unlike_post()` 不存在返回 `ErrorResponse(code="POST_NOT_FOUND")`

可以选择让 service 返回 `(data, code)`，或在 router 中检查 `data.get("error")`。

#### 3. 非法 category

`GET /v1/community/posts?category=bad` 应返回：

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CATEGORY"
  }
}
```

### 必补测试

在 `tests/test_community.py` 增加：

```python
async def test_community_delete_missing_post_returns_error(client):
    ...

async def test_community_like_missing_post_returns_error(client):
    ...

async def test_community_invalid_category_returns_error(client):
    ...
```

验收命令：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community.py
```

---

## 5. Task 2：列表分页与 liked_by_me

### 文件

- 修改：`app/routers/community.py`
- 修改：`app/services/community.py`
- 修改：`bsapp/src/api/index.js`
- 修改：`bsapp/src/pages/community/community.vue`
- 测试：`tests/test_community.py`

### 后端要求

`GET /v1/community/posts` 支持：

```text
category=all
limit=20
offset=0
```

返回：

```json
{
  "posts": [],
  "total": 0,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

如果用户已登录，post dict 增加：

```json
{
  "liked_by_me": true
}
```

如果未登录：

```json
{
  "liked_by_me": false
}
```

注意：

- `get_optional_user` 应用于 list/detail，不要强制登录才能看社区。
- `liked_by_me` 只在有 token 时查当前用户点赞表。

### 前端要求

社区列表：

- 首次加载显示 loading。
- 空列表显示 empty。
- 加载失败显示 error，并提供重试。
- 支持“加载更多”。
- 点赞状态显示“已赞/点赞”。

不要做复杂瀑布流。

### 必补测试

```python
async def test_community_list_supports_pagination(client):
    ...

async def test_community_list_includes_liked_by_me_for_logged_user(client):
    ...
```

验收：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community.py
```

---

## 6. Task 3：发布页前端校验

### 文件

- 修改：`bsapp/src/pages/community-publish/community-publish.vue`

### 要求

发布前端必须校验：

1. 标题不能为空。
2. 内容不能为空，或 recipe 分类必须有步骤/说明。
3. recipe 分类至少 1 个有效食材。
4. 食材名不能为空，amount 可选。
5. 发布中禁用按钮，避免重复提交。
6. 后端错误 message 要展示给用户。

建议实现：

```js
const submitting = ref(false)

function validateForm() {
  if (!form.value.title.trim()) return '请输入标题'
  if (!form.value.content.trim()) return '请输入内容'
  if (form.value.category === 'recipe') {
    const validIngredients = ingredients.value.filter(i => i.name.trim())
    if (!validIngredients.length) return '菜谱至少需要 1 个食材'
  }
  return ''
}
```

提交按钮：

```html
<button class="submit" :disabled="submitting" @tap="submit">
  {{ submitting ? '发布中...' : '发布' }}
</button>
```

验收方式：

- 空标题点发布，不发请求，toast 提示。
- recipe 无食材点发布，不发请求，toast 提示。
- 正常发布成功返回列表。

---

## 7. Task 4：社区详情页交互补齐

### 文件

- 修改：`bsapp/src/pages/community-detail/community-detail.vue`
- 修改：`bsapp/src/api/index.js`

### 要求

详情页补：

1. loading 状态。
2. error 状态。
3. 空评论状态。
4. 点赞/取消点赞：
   - 如果 `post.liked_by_me` 为 true，按钮显示“已赞”
   - 点击已赞时调用 unlike
   - 点击未赞时调用 like
5. 作者删除入口：
   - 如果后端返回 `user_id` 等于当前用户 id，显示删除按钮。
   - 删除前二次确认。
   - 删除成功后返回列表。

如果前端当前拿不到当前 user id，可以先只做：

```text
详情页显示删除按钮，后端 FORBIDDEN 时 toast “只能删除自己的帖子”
```

不要为了这个引入复杂全局状态重构。

---

## 8. Task 5：社区菜谱展示增强

### 文件

- 修改：`bsapp/src/pages/community/community.vue`
- 修改：`bsapp/src/pages/community-detail/community-detail.vue`

### 要求

对 `category === "recipe"` 的帖子展示：

- 食材摘要：前 3 个食材。
- 热量：`recipe_payload.calories`，没有就不显示。
- 步骤数：`recipe_payload.steps.length`。
- 操作：收藏、清点。

列表卡片不要太大，只加一行摘要：

```text
牛肉 120g / 南瓜 150g · 420 kcal · 3 步
```

详情页可以展示完整食材和步骤。

---

## 9. Task 6：测试收口

### 文件

- 修改：`tests/test_community.py`
- 修改：`tests/test_community_recipe_flow.py`

### 必测清单

`tests/test_community.py` 至少覆盖：

1. 创建 recipe 帖成功。
2. recipe 帖无 ingredients 失败。
3. 创建非法 category 失败。
4. 列表分页。
5. 点赞重复不增加计数。
6. 取消点赞减少计数。
7. 非作者删除 forbidden。
8. 作者删除成功。
9. 删除不存在帖子返回 error。
10. 空评论返回 error。

`tests/test_community_recipe_flow.py` 至少覆盖：

1. 社区菜谱收藏。
2. 社区菜谱清点。
3. 缺失食材生成 missing。
4. 社区菜谱结构字段存在：title、ingredients、steps。

验收命令：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_community.py \
  tests/test_community_recipe_flow.py
```

期望：

```text
全部通过
```

---

## 10. 文档要求

完成后新增：

```text
docs/迭代修改/28-v5社区模块完善修复记录.md
```

同步到：

```text
！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/28-v5社区模块完善修复记录.md
```

文档必须包含：

1. 修改文件列表。
2. 后端错误语义变化。
3. 前端页面变化。
4. 新增测试列表。
5. 测试命令和结果。
6. 未完成项。

---

## 11. 最终验收命令

社区专项：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q \
  tests/test_community.py \
  tests/test_community_recipe_flow.py
```

DB 集合：

```bash
./scripts/verify_db.sh
```

前端构建：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

如果已完成 v5 基础工程化脚本，则最终跑：

```bash
./scripts/verify_quick.sh
./scripts/verify_db.sh
./scripts/verify_eval_api.sh
```

---

## 12. 工作量预估

| 模块 | 预估 |
|---|---:|
| 后端错误语义 | 0.5 天 |
| 分页 + liked_by_me | 0.5 天 |
| 前端列表/详情/发布体验 | 1 天 |
| 测试补齐 | 0.5 天 |
| 文档与同步 | 0.2 天 |

总计：约 2-3 天，取决于前端细节打磨程度。

---

## 13. 交接口径

社区当前不是“没做”，而是：

> 社区 MVP 已有基础发帖、点赞、评论、收藏和清点联动，但还缺分页、当前用户点赞态、错误语义、前端状态和边界测试。v5 社区任务的目标是把社区从能跑的 MVP 收口成可答辩、可演示、可维护的闭环模块。

subagent 不要推倒重来，只按上述任务补齐。
