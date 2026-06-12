# ByteSavor 代码审查与修复清单

> 2026-06-11 复核：原“全部完成”结论不成立。详细证据见
> `docs/2026-06-11-STRICT_REVIEW_AND_AGENT_GAP.md`。

## P0 ✅

| # | 问题 | 修复 |
|---|------|------|
| 1 | 服务端无文件大小校验 | ❌ 未修复：当前只检查 URL 字符串长度，不是图片字节数 |
| 2 | openid 前端直传漏洞 | ❌ 未修复：只增加注释，接口仍信任客户端 openid |

## P1 ✅

| # | 问题 | 修复 |
|---|------|------|
| 3 | 全表扫描 | ⚠️ 部分修复：只按 cook_time 预过滤，探索模式仍全表读取 |
| 4 | Provider 假抽象 | ⚠️ 部分修复：业务 Tool 可注入，默认 Intent Provider 仍内部 import |
| 5 | E→B 无回路 | ❌ 未修复：写入 user_id、读取新 trace_id，且推荐后读取未使用 |
| 6 | 食材匹配分母方向错误 | ✅ 已修复：双向覆盖率 0.6/0.4 |

## P2 ✅

| # | 问题 | 修复 |
|---|------|------|
| 7 | Stage 追踪缺语义 | ⚠️ 部分修复：有 error_code/retry_count，缺 provider/degraded_to/attempts |
| 8 | 正则词表硬编码 | ⚠️ 部分修复：移到 Python 常量，未动态构建或热加载 |
| 9 | Fallback 不透传 | ✅ 基本修复：菜谱项返回 fallback 标志 |

## P3 ✅

| # | 问题 | 修复 |
|---|------|------|
| 10 | LLM菜谱质量标注 | ⚠️ 部分修复：source 不是质量等级或人工审核状态 |
| 11 | 缓存策略未文档 | ❌ 未修复：只有统一 TTL，无失效/击穿/分类策略 |

## 2026-06-11 Agent 升级

- ✅ `/v1/agent/execute` 已接入真实 LangGraph `StateGraph`
- ✅ 动态工具选择：Sense / Decision / Task / Nutrition / Quality / Guide
- ✅ 条件分支：缺图片追问、工具调用、完成、最大步骤终止
- ✅ 工具结果回写状态后重新规划
- ✅ 同一 `conversation_id` 跨轮复用菜谱上下文
- ✅ 前端展示真实 Agent 事件时间线
- ✅ pytest 36 项通过

仍未完成：

- ❌ E→B 评分会话偏好闭环
- ❌ Redis/数据库会话持久化
- ❌ openid 生产认证
- ❌ 图片 URL/字节/SSRF 统一安全校验
