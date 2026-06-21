# ByteSavor v5 任务包

这个文件夹是给 subagent 的 v5 执行入口。

建议执行顺序：

1. `01-v5基础工程化任务书_给Subagent.md`
   - 先做验证脚本、pytest markers、文档索引。
   - 这是后续所有工作的验证底座。

2. `03-v5账号登录与用户数据库完善任务书_给Subagent.md`
   - 再做账号密码登录和用户表字段。
   - 账号系统会影响社区、收藏、评论等所有登录态功能。

3. `02-v5社区模块完善任务书_给Subagent.md`
   - 最后做社区完善。
   - 社区依赖登录态，应该放在账号体系之后。

执行规则：

- 不要三份任务同时改。
- 每完成一份都要写对应修复记录，并同步到可见目录。
- 每份任务都必须贴完整验证命令和结果。
- 如果 DB 测试因沙箱无法连接 MySQL 失败，必须说明是权限问题，并在可访问 MySQL 的环境复跑。
- 不要新增本地 CNN/ONNX、WebSocket、LLM Judge 阻断主流程。

当前基线：

- 核心非 DB：`84 passed, 1 skipped`
- DB 依赖：`24 passed`
- Eval mock：`72/72`
- Eval api：`72/72`
- H5 构建：`DONE Build complete`
