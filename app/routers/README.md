# routers - 接口层

每个文件对应一组 API 路由。router 只负责接收 HTTP 请求、调 service 拿结果、返回响应，不写业务逻辑。

| 文件 | 所属模块 | 接口 |
|------|---------|------|
| auth.py | 认证 | 注册、登录 |
| user.py | 用户 | 查/改画像、营养状态 |
| sense.py | B-感知 | 食材识别 |
| decision.py | Y-决策 | 推荐菜谱、菜谱详情 |
| task.py | T-执行 | 购物清单合并 |
| agent.py | T-执行 | Agent 统一入口（自然语言） |
| feedback.py | E-反馈 | 提交评分 |
