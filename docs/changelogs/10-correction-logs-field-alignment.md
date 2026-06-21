# 修改文档 10：correction_logs 表字段对齐手册规范

## 修改日期

2026-06-19

## 修改原因

对手册 Section 9.3 的精确字段规范进行调整。

## 文件变更

### 1. 修改 `app/models/__init__.py` — CorrectionLog 模型

| 修改前字段 | 修改后字段 | 说明 |
|---|---|---|
| `action_type` | `action` | 对齐手册命名 |
| `source_type` | `source` | 对齐手册命名 |
| `original_value` (JSON) | `original_name` (String) | 扁平化，直接存食材名 |
| `new_value` (JSON) | `corrected_name` (String) | 扁平化 |
| (无) | `confidence` (Integer) | 新增，原始置信度*100 |
| (无) | `meta` (JSON) | 新增，扩展元数据 |

### 2. 修改 `app/services/correction_logs.py`

- `log_correction()` 参数对齐新字段：`action`, `source`, `original_name`, `corrected_name`, `confidence`, `meta`
- `get_recent_corrections()` 返回格式包含 confidence/100 转换
- `get_recent_aliases()` 使用 `original_name`/`corrected_name`

### 3. 修改 `app/routers/correction_logs.py`

- POST body 字段对齐：`{action, source, original_name, corrected_name, confidence, meta}`
- action 枚举：`rename | delete | merge | weight_adjust`
- source 枚举：`sense | inventory`
- confidence 为 0.0~1.0 浮点数，后端自动乘 100 存储
