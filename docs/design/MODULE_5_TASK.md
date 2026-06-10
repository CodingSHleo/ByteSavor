# 模块五：执行层 (T-Task) + Agent 实现思路

## 一、现状

| 方法 | 路径 | 当前行为 |
|------|------|---------|
| POST | `/v1/task/merge-list` | Mock 返回固定清单 |
| POST | `/v1/agent/execute` | Mock 返回固定结果 |

Mock 合并清单永远返回 "牛肉 300g + 蒜蓉 10g"，不会合并重复食材。
Agent 入口永远返回 "南瓜炖牛肉"，不管输入是什么。

## 二、目标

### T-Task
- `/v1/task/merge-list`：传入多个 recipe_id → 合并去重 → 返回统合购物清单
- 同名食材数量相加，不同名保留

### Agent
- `/v1/agent/execute`：自然语言输入 → 解析意图 → 调 Sense + Decision → 组装返回
- 这是 BYTE 全流程的唯一统一入口

## 三、新增文件

```
app/services/shopping.py     # 购物清单合并引擎
app/services/agent.py        # Agent 统一编排（B→Y→T 串联）
```

## 四、修改文件

```
app/routers/task.py          # Mock → 调 shopping service
app/routers/agent.py         # Mock → 调 agent service
```

## 五、shopping.py 设计

```python
async def merge_shopping_list(db, recipe_ids: list[str]) -> list[dict]:
    # 1. 查菜谱，拿到每个菜谱的 ingredients
    # 2. 解析 amount（"300g" → 数值+单位）
    # 3. 同名食材数量相加
    # 4. 不同名食材保留
    # 返回: [{"name": "牛肉", "amount": "600g"}, ...]
```

### 单位解析规则
- `300g` / `200ml` / `1勺` / `少许` / `2个` / `3瓣` / `1根`
- 同单位才相加（`300g` + `200g` = `500g`，但 `2个` 和 `300g` 不能加）
- 无单位的（`少许`、`适量`）直接保留不合并

## 六、agent.py 设计

```python
async def execute(db, user_input: str, user_id: str | None = None, image_url: str | None = None):
    # 1. 解析自然语言意图 → 提取 ingredients, constraints
    # 2. 如果有 image_url → 调 vlm.analyze_food (Sense)
    # 3. 调 decision.recommend (Decision)
    # 4. 调 shopping.merge_shopping_list (Task)
    # 5. 汇总返回全流程结果
```

第 1 步的意图解析，在 LLM 不可用时用规则降级（关键词匹配"减脂""30分钟""牛肉"）。

### 降级规则解析
```python
def parse_intent(text: str) -> dict:
    goal = "balanced"
    time_limit = 30
    ingredients = []
    if "减脂" in text: goal = "fat_loss"
    if "增肌" in text: goal = "muscle_gain"
    if re.search(r"(\d+)分钟", text): time_limit = int(re.search(r"(\d+)分钟", text).group(1))
    # 匹配常见食材名
    known = ["牛肉","鸡肉","猪肉","鸡蛋","番茄","西兰花","南瓜","豆腐","鱼","虾","土豆"]
    for k in known:
        if k in text: ingredients.append(k)
    return {"goal": goal, "time_limit": time_limit, "ingredients": ingredients}
```

## 七、验证

```bash
# 1. 合并清单
curl -X POST /v1/task/merge-list \
  -d '{"recipes":["r_001","r_003"]}'
# 香辣牛肉西兰花(牛肉300g+西兰花200g) + 南瓜炖牛肉(牛肉400g+南瓜300g)
# → 牛肉 700g, 西兰花 200g, 南瓜 300g

# 2. Agent 自然语言
curl -X POST /v1/agent/execute \
  -d '{"input":"家里有牛肉和南瓜，30分钟做个减脂餐"}'
# → 全流程结果，包含食材识别+菜谱推荐+购物清单
```

## 八、依赖

- 模块一（数据库）
- 模块三（Sense，Agent 调用了 vlm.analyze_food）
- 模块四（Decision，Agent 调用了 decision.recommend）

## 九、实现状态（2026-05-27）✅ 已完成

### 新增文件
| 文件 | 说明 |
|------|------|
| `app/services/shopping.py` | 购物清单合并引擎：解析单位 + 同名累加 |
| `app/services/agent.py` | Agent 编排：意图解析 → B→Y→T 全流程串联 |

### 修改文件
| 文件 | 说明 |
|------|------|
| `app/routers/task.py` | Mock → 真实合并引擎 |
| `app/routers/agent.py` | Mock → 真实 Agent 编排 |

### 验证结果
```
合并清单 r_001+r_003 → 牛肉 300g+400g=700.0g ✅
Agent "牛肉南瓜30分钟减脂" → intent 正确解析 → 菜谱推荐 → 购物清单 ✅
空 recipes → error: NO_RECIPES ✅
```

## 十、不在本模块做的

- LangGraph 真实 Agent 编排（当前顺序调用，后续接 LangGraph）
- 外卖/生鲜平台对接
- 清单自动下单
- 真实 LLM 意图解析（当前规则降级）
