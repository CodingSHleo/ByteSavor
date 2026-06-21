# 修改文档 13：Redis conversation checkpoint + SkillDescriptor

## 修改日期
2026-06-20

## 文件变更

### 1. 修改 `app/agent/langgraph_runtime.py` — Redis conversation checkpoint

**修改位置**：新增 `_load_previous_state()` / `_save_state()` 方法

**原逻辑**：会话状态只存内存（`_conversation_states` 字典），服务重启丢失。

**新逻辑**：
- 先查内存 → 再查 Redis → 都没有则新建状态
- 每次 `run()` 结束后同时写内存 + Redis
- Redis key: `bs:<md5(agent|conv|conversation_id)>`，TTL 900s（15min）
- Redis 写入失败不阻塞主流程（cache_set 内部 try/except + debug log）
- InMemorySaver 保留不变，作为 LangGraph 内部的 checkpoint

### 2. 新增 `app/agent/skill_descriptor.py` — 轻量元数据

见下方 SkillDescriptor 部分。
