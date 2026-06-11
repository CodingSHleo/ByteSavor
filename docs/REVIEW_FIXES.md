# ByteSavor 代码审查与修复清单（全部完成）

## P0 ✅

| # | 问题 | 修复 |
|---|------|------|
| 1 | 服务端无文件大小校验 | `sense.py`: `len(image_url) > 8MB` 校验 |
| 2 | openid 前端直传漏洞 | `auth.py`: 注释说明开发直传/生产 code2session |

## P1 ✅

| # | 问题 | 修复 |
|---|------|------|
| 3 | 全表扫描 | `decision.py:_retrieve()` SQL层 WHERE cook_time |
| 4 | Provider 假抽象 | `agent.py:_get_intent()` providers列表参数 |
| 5 | E→B 无回路 | 新增 `session_prefs.py`，feedback→agent 即时生效 |
| 6 | 食材匹配分母方向错误 | `_calc_ingredient()` 双向覆盖率 0.6/0.4 |

## P2 ✅

| # | 问题 | 修复 |
|---|------|------|
| 7 | Stage 追踪缺语义 | 所有 stage 加 `error_code` + `retry_count` |
| 8 | 正则词表硬编码 | 外置 `intent_keywords.py`，29种食材 |
| 9 | Fallback 不透传 | `recommend()` 返回 `"fallback": true/false` |

## P3 ✅

| # | 问题 | 修复 |
|---|------|------|
| 10 | LLM菜谱质量标注 | recipes 表已有 `source` 字段(seed/tada/demo) |
| 11 | 缓存策略未文档 | `core/cache.py` TTL=600s, key=md5(食材+约束) |
