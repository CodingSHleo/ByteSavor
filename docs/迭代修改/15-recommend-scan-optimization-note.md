# 修改文档 15：推荐全表扫描优化说明

## 当前策略

推荐服务 `app/services/decision.py` 的 `_retrieve()` 函数使用 `select(Recipe).where(...)` 全表扫描菜谱表。

## 短期可接受的原因

1. 当前菜谱数据量小（< 200 条），全表扫描延迟 < 5ms
2. MySQL 对 `cook_time` 条件使用索引过滤
3. 演示阶段数据量不会突增
4. Python 侧的 `_rank()` 排序在 < 200 条数据上耗时 < 1ms

## 后续优化方向（P2）

当菜谱量超过 1000 条时：

1. **食材倒排索引**：预计算每个菜谱的食材标签，存入 Redis Set
   - key: `bs:idx:ingredient:{name}` → recipe_ids
   - 推荐时取交集，大幅减少 SQL 扫描行数
2. **SQL 预过滤**：在 `_retrieve()` 中使用 `Recipe.ingredients` JSON 字段的 MySQL 8.0 JSON_CONTAINS 过滤
3. **缓存热门推荐**：高频食材组合的推荐结果直接走 Redis 缓存

## 验证

当前推荐服务在演示环境（< 200 条菜谱）延迟通常 < 100ms（含 SQL + Python 排序），不构成演示瓶颈。
