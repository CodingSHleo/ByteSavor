# 模块六：反馈层 (E-Feedback) 实现思路

## 一、现状

| 方法 | 路径 | 当前行为 |
|------|------|---------|
| POST | `/v1/feedback/meal` | Mock 返回 acknowledged + reward_points: 5 |

不存数据库，评分丢了就丢了。

## 二、目标

- 用户对菜谱评分 → 写入 feedback 表
- 更新 nutrition_log（健康数据记录）
- 根据高评分菜谱的 tags 微调用户偏好（简单 RL 信号）

## 三、数据表

```sql
feedback: id, user_id, recipe_id, rating, created_at
```

## 四、新增文件

```
app/services/feedback.py    # 反馈业务逻辑
```

## 五、修改文件

```
app/routers/feedback.py     # Mock → 真实存储 + 偏好微调
app/schemas.py              # 加 FeedbackRequest 已有
```

## 六、反馈流程

```
POST /v1/feedback/meal { recipe_id, rating }
  │
  ├─ 1. 写入 feedback 表
  ├─ 2. 如果 rating >= 4：取该菜谱 tags，往用户 preferences 追加新标签
  ├─ 3. 如果 rating <= 2：从用户 preferences 移除匹配标签
  └─ 4. 返回 acknowledged + reward_points
```

偏好微调逻辑：用户喜欢辣 → preferences 自动加 "spicy"，下次推荐 spicy 菜谱排前面。

## 七、验证

```bash
# 1. 提交高评分反馈
curl -X POST /v1/feedback/meal \
  -H "Authorization: Bearer <token>" \
  -d '{"recipe_id":"r_001","rating":5}'
# → acknowledged, 用户偏好自动加 spicy/high_protein/low_carb

# 2. 查画像，确认偏好被更新
curl /v1/user/profile -H "Authorization: Bearer <token>"
# → preferences 含 spicy, high_protein, low_carb
```

## 八、依赖

- 模块一（数据库）
- 模块二（用户偏好读写）

## 九、不在本模块做的

- RLHF 真实强化学习管道
- 长期健康趋势分析
- 推荐模型重新训练
