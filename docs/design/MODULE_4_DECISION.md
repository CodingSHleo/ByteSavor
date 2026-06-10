# 模块四：决策层 (Y-Decision) 实现思路

## 一、现状

| 方法 | 路径 | 当前行为 |
|------|------|---------|
| POST | `/v1/decision/meal-plan` | Mock 返回固定菜谱"香辣牛肉西兰花" |
| GET | `/v1/recipes/{recipe_id}` | Mock 返回固定菜谱详情 |

输入是食材列表 + 用户约束（时间/口味/目标），输出是推荐菜谱列表 + 营养缺口。

现在完全没用到输入参数，不管传什么食材都返回同一个菜谱。

## 二、目标

接收食材列表 + 用户约束 → 从菜谱库中匹配 → 按个性化排序 → 返回推荐菜谱 + 营养缺口分析。

## 三、数据表设计

因为 Neo4j + FoodKG 接入需要时间，先用 MySQL 建两张表跑通全链路。

```sql
recipes: id, title, steps(JSON), ingredients(JSON), tags(JSON),
         cook_time, calories, protein, carbs, fat, difficulty
```

```sql
recipe_ingredients: recipe_id, ingredient_name, amount
```

### recipes 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | r_ + uuid |
| title | VARCHAR(100) | 菜谱名 |
| steps | JSON | 烹饪步骤列表 |
| ingredients | JSON | 所需食材 `[{"name":"牛肉","amount":"300g"}]` |
| tags | JSON | 标签 `["spicy","high_protein","low_carb"]` |
| cook_time | INT | 烹饪时间（分钟） |
| calories | INT | 热量（千卡） |
| protein | INT | 蛋白质（克） |
| carbs | INT | 碳水（克） |
| fat | INT | 脂肪（克） |
| difficulty | VARCHAR(10) | easy / medium / hard |
| created_at | DATETIME | 创建时间 |

## 四、匹配逻辑

```
POST /v1/decision/meal-plan { ingredients, constraints }
  │
  ├─ 1. 用 ingredients 匹配 recipes（食材匹配度打分）
  ├─ 2. 用 constraints 过滤（时间/口味/目标/难度）
  ├─ 3. 用用户偏好加权排序（如果带 token）
  ├─ 4. 计算营养缺口（推荐菜谱的营养 vs 目标）
  └─ 5. 返回 RecipeBrief[] + nutrition_gap
```

### 打分规则

1. **食材匹配分** = 用户有的食材 ∩ 菜谱需要的食材 / 菜谱需要的食材
   - 用户有 3 样，菜谱需要 4 样 → 75% 匹配
2. **约束过滤**：
   - `cook_time <= time_limit`
   - `taste` 标签匹配（用户选 spicy → 菜谱 tags 含 spicy 加分）
   - `goal` 目标匹配（fat_loss → 低卡高蛋白加分）
3. **偏好加权**：如果用户登录了，从 profiles 表拿 preferences，菜谱标签匹配的加分

## 五、新增文件

```
app/models/recipe.py         # Recipe ORM
app/services/decision.py     # 匹配引擎（打分/过滤/排序）
app/services/nutrition.py    # 营养缺口计算
app/seed/recipes.json        # 初始菜谱数据（10-15条）
app/seed/seed_recipes.py     # 导入脚本
```

## 六、修改文件

```
app/routers/decision.py      # Mock → 调 decision service
app/main.py                  # lifespan 加 recipes 表建表 + 自动 seed
```

## 七、services/decision.py 设计

```python
async def match_recipes(db, ingredients, constraints, user_profile=None) -> dict:
    # 1. 查出所有菜谱
    recipes = await db.execute(select(Recipe))
    
    # 2. 每个菜谱打分
    scored = []
    for r in recipes:
        match_score = calc_match(r, ingredients)      # 食材匹配
        constraint_score = calc_constraint(r, constraints)  # 约束匹配
        preference_score = calc_preference(r, user_profile) # 偏好匹配
        total = match_score * 0.5 + constraint_score * 0.3 + preference_score * 0.2
        if total > 0.3:  # 匹配度太低的不返回
            scored.append({"recipe_id": r.id, "title": r.title, "match_score": total})
    
    # 3. 按分数排序，取 top 5
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return {"recipes": scored[:5]}
```

## 八、营养缺口计算

推荐菜谱的营养总和 vs 用户一天的目标摄入：
- 用户目标 fat_loss → 需要高蛋白低卡
- 遍历推荐菜谱的营养成分，看缺少什么
- 返回 `{protein: "still_needed", carbs: "exceeded", ...}`

先做简单版：只标记 protein 缺口（最直观）。
复杂版后续接真实营养数据库。

## 九、seed 数据

写 10 条真实菜谱导入 recipes 表，覆盖多种场景：
- 荤菜/素菜/汤
- 不同口味（辣/清淡/酸甜）
- 不同目标（减脂/增肌/均衡）
- 不同烹饪时间（快炒 15min / 炖煮 60min）

这样匹配引擎有足够数据跑出不同的推荐结果。

## 十、验收

```bash
# 1. 传食材 + 约束，验证返回不同菜谱
curl -X POST /v1/decision/meal-plan \
  -d '{"user_id":"u1","ingredients":["牛肉","西兰花"],"constraints":{"time_limit":30,"taste":"spicy","goal":"fat_loss"}}'
# → 返回多个菜谱，按 match_score 排序

curl -X POST /v1/decision/meal-plan \
  -d '{"user_id":"u1","ingredients":["鸡蛋","番茄"],"constraints":{"time_limit":15,"taste":"light","goal":"balanced"}}'
# → 返回不同的菜谱

# 2. 菜谱详情
curl GET /v1/recipes/r_xxx
# → 返回完整步骤

# 3. 带用户 token，验证偏好影响排序
curl -X POST /v1/decision/meal-plan \
  -H "Authorization: Bearer <token>" \
  -d '{"user_id":"u1","ingredients":["牛肉"],"constraints":{"time_limit":30}}'
# → 偏好 high_protein 的用户看到高蛋白菜谱排前面
```

## 十一、依赖

- 模块一（数据库）
- 模块二（用户偏好，可选——没 token 也能用）

## 十二、不在本模块做的

- Neo4j / GraphRAG 接入（后续替换 decision service 底层即可，接口不动）
- 真实营养数据库接入
- 菜品图片/视频

---

## 十三、审查修复（2026-05-27）

| # | 问题 | 级别 | 修复 |
|---|------|------|------|
| 1 | ingredients JSON 双写模型 | P0 | MVP 保留 JSON，model 加注释说明后期拆表 |
| 2 | user_id 从 body 获取可伪造 | P0 | DecisionRequest 移除 user_id，get_optional_user 从 JWT 取 |
| 3 | 硬过滤/软排序混合 | P0 | 重写 decision.py：硬过滤（cook_time 直接淘汰）+ 软排序（食材/标签/偏好三个 0~1 子分） |
| 4 | 空食材报 400 | P1 | 改为探索模式：空 ingredients → 全量推荐，按标签+偏好排序 |
| 5 | 推荐缺少可解释性 | P1 | 每条推荐返回 reasons 列表，如 ["已有食材: 牛肉","高蛋白适合减脂","符合偏好: high_protein"] |
| 6 | DecisionEngine 未抽象 | P1 | 新增 `services/decision_engine.py` — `BaseDecisionEngine` 抽象类，后期 Neo4j/GraphRAG 替换只需新增子类 |
| 7 | nutrition 放错域 | P2 | 文档记录，后期拆为独立 domain |
| 8 | select(Recipe) 全表扫描 | P2 | 10 条没问题，文档记录后期加 SQL 粗召回 |
| 9 | tags/steps JSON 问题 | P2 | model 加 MVP 注释，文档记录后期拆表 |

### 算法修正（第二轮审查后）

原来的打分：
```
total = match * 0.5 + constraint * 0.3 + preference * 0.2  # 三个子分定义域不统一
```

修正后（5 步 pipeline）：
```
1. _retrieve()        候选检索（当前全表，后期 SQL 粗召回）
2. _hard_filter()     硬过滤（cook_time > time_limit → 淘汰）
3. _rank() / _explore_rank()  软排序（三子分 0~1 归一化）
4. _fallback()        无结果时放宽条件，降权推荐
5. _build_reasons()   解释生成（code 编码化，非纯文本）
```

硬过滤/软排序严格分离，三个子分全部 clamp 到 0~1。每步职责单一，后期 GraphRAG 替换只需改第 1、3 步。

### reasons 编码化

改后每条推荐：
```json
{
  "title": "香辣牛肉西兰花",
  "match_score": 0.65,
  "reasons": [
    {"code": "ING_MATCH", "text": "已有食材: 牛肉", "meta": {"ingredient": "牛肉"}},
    {"code": "TASTE_MATCH", "text": "口味匹配: spicy", "meta": {"taste": "spicy"}}
  ]
}
```
前端按 code 渲染，多语言只需改 REASON_TEMPLATES。8 种 code 覆盖所有场景。

### 其他修复
- Recipe 加 source/schema_version 字段（未来数据迁移用）
- pipeline 入口加结构化 logging
- 文档标注：ingredients/tags/steps JSON 为 MVP 方案，后期拆表
- 文档标注：nutrition 后期拆独立 domain
- 文档标注：热门 ingredient-set 做 Redis cache

## 十四、实现状态（2026-05-27）✅ 已完成

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/models/recipe.py` | Recipe ORM：id/title/steps/ingredients/tags/cook_time/calories/protein/carbs/fat/difficulty |
| `app/services/decision.py` | 匹配引擎：食材匹配(50%) + 约束过滤(30%) + 偏好加权(20%) |
| `app/services/nutrition.py` | 营养缺口计算：推荐菜谱营养 vs 目标(减脂/增肌/均衡) |
| `app/seed/recipes.json` | 10 道真实菜谱种子数据 |
| `app/seed/seed_recipes.py` | 种子数据导入脚本（幂等，不重复导入） |

### 修改文件

| 文件 | 说明 |
|------|------|
| `app/routers/decision.py` | Mock → 真实匹配引擎 + 营养缺口。可选登录（有 token 用偏好，无不影响） |
| `app/main.py` | 注册 Recipe 模型建表 + 启动时自动 seed |
| `app/middleware/auth.py` | 新增 `get_optional_user`：有 token 解析，没有不报错 |

### 验证结果

```
牛肉+西兰花+辣+减脂 → 香辣牛肉西兰花 0.72, 蒜蓉西兰花 0.64 ✅
鸡蛋+番茄+清淡     → 番茄炒蛋 0.83 (top) ✅
空食材             → 探索模式，全量推荐 ✅
菜谱详情 r_002     → 番茄炒蛋, 5 steps, 220 kcal ✅
不存在菜谱 r_999   → error: NOT_FOUND ✅
```
