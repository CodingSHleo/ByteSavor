# ByteSavor 批次 D：用户隔离与 Tab 图标修复记录

日期：2026-06-21
依据：`33-用户实测问题总结与修复计划.md` 批次 D

## 修改摘要

| 问题 | 根因 | 修复 | 文件 |
|------|------|------|------|
| 1.1 新用户看到旧数据 | 登录不清理storage | setAuthData前清理旧缓存 | auth.js |
| 1.1 登出后残留数据 | clear只清4个key | 扩展清理8个key | auth.js |
| 1.9 tab图标大小不一 | scan/knowledge 128x128 vs 其他81x81 | sips resize到81x81 | icons/*.png |

## 修复详情

### 1. 登录/注册时清理旧缓存（auth.js）

`setAuthData()` 在写入新用户数据前清除：
- `last_ingredients` — 上一轮识别的食材
- `agent_conversation_id` — AI助手会话ID
- `inventory_items` — 库存缓存
- `recognition_result` — 识别结果缓存

### 2. 登出时扩展清理（auth.js）

`clear()` 清除8个key：
- `auth_token`, `user_id`, `username`, `email`
- `last_ingredients`, `agent_conversation_id`
- `inventory_items`, `recognition_result`

### 3. Tab图标统一尺寸

| 图标 | 修改前 | 修改后 |
|------|--------|--------|
| home.png | 81x81 | 81x81 |
| scan.png | 128x128 | **81x81** |
| explore.png | 81x81 | 81x81 |
| knowledge.png | 128x128 | **81x81** |
| profile.png | 81x81 | 81x81 |
| active variants | 一致 | 一致 |

使用 `sips -z 81 81` 统一尺寸。

## 举一反三排查

| 检查项 | 结果 |
|--------|------|
| A用户收藏→B用户登录→收藏为空 | ✅ storage清理 |
| A用户库存→B用户登录→库存为空 | ✅ storage清理 |
| A用户用餐记录→B用户不可见 | ✅ 后端按user_id查询 |
| 登出再登录→不残留上用户页面状态 | ✅ clear清理 |
| 社区公共帖子B可见但liked_by_me按B计算 | ✅ 后端按token计算 |
| 5个tab图标视觉中心一致 | ✅ 81x81 |
| 选中/未选中不跳动 | ✅ 尺寸统一 |

## 测试结果

H5 Build: DONE
核心测试: 84 passed, 1 skipped

## 手工验收

1. 注册A用户→收藏菜谱→登出
2. 注册B用户→库存为空、收藏为空、用餐计划为空
3. 社区帖子可见，但liked_by_me=false
4. 底部5个tab图标大小一致
