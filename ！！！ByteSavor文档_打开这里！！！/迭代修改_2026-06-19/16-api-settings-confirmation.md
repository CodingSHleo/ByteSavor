# 修改文档 16：API 地址设置 + L2 用户确认交互

## 修改日期
2026-06-20

## 一、手机端 API 地址设置入口

### 修改 `bsapp/src/pages/settings/settings.vue`

**新增 UI 区域**（在"系统偏好"和"隐私安全"之间）：
- 显示当前 API 地址（从 `uni.getStorageSync('api_base_url')` 读取，未设置时显示"自动检测"）
- "修改"按钮 → 弹出输入框，可输入局域网 IP（如 `http://192.168.1.100:8000`）
- "重置"按钮 → 清除 storage，恢复自动检测
- 输入自动去尾部斜杠

**新增函数**：
- `editApiUrl()` — 弹出编辑弹窗，写入 `uni.setStorageSync('api_base_url', url)`
- `resetApiUrl()` — 清除 storage，恢复自动检测

**原理**：API 服务 `bsapp/src/api/index.js` 已支持 `getStorageSync('api_base_url')` 优先级读取，无需改 API 层。

## 二、L2 用户确认交互

### 后端：修改 `app/routers/agent.py`

**新增函数** `_build_confirmation_prompts(result) -> list[dict]`：
- 扫描 evaluation events 中的 NEEDS_USER_CONFIRMATION / LOW_CONFIDENCE_INGREDIENT / CORE_INGREDIENT_MISSED
- 生成对应的确认提示，包含 `question` 和 `options`（含 action: confirm/retry/accept/skip）
- 返回结果新增 `confirmation_prompts` 字段

### 前端：修改 `bsapp/src/pages/home/home.vue`

**新增 UI**（在 memory_used 和 intent 之间）：
- 确认卡片（琥珀色背景）展示问题和操作按钮
- 每个按钮对应 action：重新推荐 / 确认 / 跳过 / 接受替代

**新增函数** `handleConfirmation()`：
- retry → 自动重新发送 Agent 请求
- confirm/accept → 显示确认 toast
- skip → 静默跳过

**CSS**：`.agent-confirm` / `.confirm-card` / `.confirm-btn` 琥珀色调样式
