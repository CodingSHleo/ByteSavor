# ByteSavor 代码审查与修复清单

## P0 - 立即修复

### 1. 服务端文件大小校验
- `/v1/sense/analyze` 无文件大小上限，恶意用户可发送 50MB 图片
- 修复: 加 `image_url` 长度校验 + FastAPI 请求体大小限制

### 2. openid 来源说明
- 当前实现是前端直传 openid，微信生产环境需改为后端 code2session 换取
- 修复: 代码注释说明当前为简化实现，生产环境需接入微信服务端 API

## P1 - 本周修复

### 3. 推荐引擎全表扫描
- `_retrieve()` 每次 SELECT * FROM recipes，2576条可接受但不扩展
- 修复: `_hard_filter()` 下推到 SQL 层，加 cook_time 索引

### 4. Provider 抽象是真抽象
- `_get_intent()` 三级降级链硬编码在 agent.py 内
- 修复: 改为接收 `IntentProvider` 列表参数，`FallbackChain` 迭代器

### 5. E→B 数据回路
- 反馈只写库，不影响同会话后续推荐
- 修复: Agent 层维护 `session_prefs`，与持久化偏好合并

### 6. 食材匹配双向覆盖率
- 当前分母只用菜谱食材数，不公平
- 修复: `(|exact|/|recipe|)*0.6 + (|exact|/|user|)*0.4`

## P2 - 后续改进

### 7. Stage 追踪增强错误语义
- 缺少 error_code / retry_count / degraded_to
- 后续改

### 8. 正则词表外置
- 18种食材硬编码，应改为配置文件或动态构建
- 后续改

### 9. Fallback 语义透传
- 前端不知道结果是 fallback
- Response 加 `"fallback": true` 标志

## P3 - 文档记录

### 10. LLM 菜谱数据质量标注
- 2576道中仅3道 LLM 增强，无质量标注
- recipes 表已有 source 字段，可用

### 11. 缓存策略补充文档
- TTL / key 命名 / 防击穿未文档化
- 补充策略表
