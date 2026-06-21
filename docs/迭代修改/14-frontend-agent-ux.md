# 修改文档 14：前端 Agent 体验增强

## 修改日期
2026-06-20

## 文件变更

### 修改 `bsapp/src/pages/home/home.vue`

#### 1. 新增响应式状态（script setup）
- `agentLoading` — Agent 请求进行中
- `agentProgress` — 假进度 0-85%
- `replayingEvents` / `replayEvents` / `replayIndex` — events 逐条回放控制

#### 2. 骨架屏 + 假进度条（template）
请求期间替代空白区域显示：
- 假进度条（0→30% 规划 / 30→60% 执行 / 60→85% 评估），200ms 递增
- 三条骨架线（长短不一），shimmer 动画

#### 3. events 逐条回放
`sendAgentMessage()` 修改：
- 请求前启动假进度定时器
- HTTP 返回后立即显示回复（events 初始为空）
- 每 500ms 回放一条 event 到消息的 events 列表
- 回放完成后再显示完整 events

#### 4. evaluation 事件展示
`agentEventTitle()` 更新：
- 显示 phase 标签：`评估 [EVALUATING]：通过/部分通过/存在冲突/未通过`
- `agentEventDetail()` 显示具体 issue codes

#### 5. memory_used 展示
在 events 和 intent 之间新增记忆参考展示区：
```
本次参考记忆
[conversation] 沿用了上一轮识别到的牛肉、南瓜
[preference] 偏好口味: high_protein, light
[fact] 读取当前库存 3 项
```

#### 6. CSS 新增
- `.agent-skeleton` — 骨架屏容器
- `.skeleton-line` — shimmer 动画骨架线
- `.skeleton-progress-*` — 假进度条
- `.agent-memory` / `.memory-chip` — 记忆展示
- `.agent-event.evaluation` — 评估事件样式（紫色背景）
