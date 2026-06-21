# 修改文档 07：correction_logs 纠错日志

## 修改日期

2026-06-19

## 修改目标

对应方案文档 Section 4 P1.5（correction_logs 纠错日志）。记录用户对识别/库存结果的修改操作，用于后续同义词和识别后处理优化。

## 文件变更

### 1. 新增 `app/services/correction_logs.py`

**原代码**：不存在此文件。

**新增内容**：
- `log_correction(db, user_id, action_type, source_type, original_value, new_value)` — 记录一条纠错操作
- `get_recent_corrections(db, user_id, limit)` — 查询用户最近的纠错记录
- `get_recent_aliases(db, user_id, limit)` — 获取用户最近的改名纠错，返回 `[{from, to}]` 别名映射列表

**action_type 枚举**：
| 类型 | 说明 |
|------|------|
| `delete` | 用户删除识别结果 |
| `rename` | 用户修改食材名称 |
| `merge` | 用户合并重复食材 |
| `weight_change` | 用户修改食材重量 |

### 2. 新增 `app/routers/correction_logs.py`

**原代码**：不存在此文件。

**新增路由**：
- `POST /v1/correction-logs` — 记录纠错（需登录）
- `GET /v1/correction-logs?limit=20` — 查询纠错历史（需登录）

### 3. 修改 `app/models/__init__.py`

**修改位置**：原 CommunityLike 模型之后（第 138 行之后）

**新增模型** `CorrectionLog`：
```python
class CorrectionLog(Base):
    __tablename__ = "correction_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(20), nullable=False)  # delete/rename/merge/weight_change
    source_type = Column(String(20), default="sense_result")  # sense_result/inventory
    original_value = Column(JSON, default=dict)
    new_value = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
```

### 4. 修改 `app/main.py`

- 导入 `correction_logs` 路由
- 注册 `app.include_router(correction_logs.router)`

### 5. 后续集成（P2）

- correction_logs 数据将用于 MemoryContext 的 `correction_memory.recent_aliases`
- 可用于离线回流到同义词标准化规则
