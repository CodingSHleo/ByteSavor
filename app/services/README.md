# services - 业务逻辑层

这里写真正的业务代码，router 只负责调这些函数。

| 文件 | 干什么的 |
|------|---------|
| user.py | 用户注册、登录、查画像、改偏好 |
| decision.py | 推荐引擎：检索候选 → 硬过滤（时间）→ 软排序（食材/标签/偏好打分）→ fallback → 生成推荐理由 |
| decision_engine.py | 推荐引擎的抽象接口，后面如果要换成 Neo4j/GraphRAG 引擎，只需要在这里加新类 |
| shopping.py | 购物清单合并：同名同单位累加、不同单位分列、display 格式化 |
| agent.py | BYTE 全流程编排：意图解析 → B感知 → Y决策 → T执行，每个阶段的成功/失败都有记录 |
| feedback.py | 存储用户评分，并根据高分/低分自动调整用户偏好 |
| nutrition.py | 根据推荐菜谱的营养成分和用户目标，算出营养缺口 |
| llm.py | 调 LLM 做自然语言意图解析（目前连本地 Ollama qwen2.5:1.5b） |
| providers.py | Provider 接口定义（Agent 不直接依赖具体 service，依赖这些接口） |
| vlm/ | VLM 视觉模型调用（目前抽象好了，等接入真实 VLM） |
