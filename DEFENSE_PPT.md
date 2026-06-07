# ByteSavor 期末展演 PPT（5页 · 5分钟讲完）

---

## 第1页：系统功能概览

**标题：** 基于多模态 Agent 的全场景饮食全链路解析系统

**四格功能展示：**

| | | |
|---|---|---|
| 🏠 **家庭烹饪** | 💪 **健康饮食** |
| 拍照识别食材 → 生成菜谱 | 营养缺口分析 → 宏/微量营养素 |
| 🛒 **购物执行** | 🧠 **长期个性化** |
| 多菜谱合并清单+挑拣建议 | 评分反馈 → 自动更新偏好 |

**底部一行：** B（感知）→ Y（决策）→ T（执行）→ E（反馈）

**一句话：** 竞品是互相孤立的"工具集合"，ByteSavor 是把识别→推荐→执行→反馈串成一条可追踪的 Agent 流水线。

---

## 第2页：核心流程与技术架构

**架构图（自上而下）：**

```
uni-app 前端 (Vue3 + Vite5, H5 + 微信小程序)
        │
   FastAPI API 层
        │
 ┌──────┼──────┬──────┐
 B-感知  Y-决策  T-执行  E-反馈
 Sense  Decision Task   Feedback
 VLM    推荐引擎  Agent  偏好学习
 └──────┴──────┴──────┘
        │
 MySQL + Redis + VLM(Qwen-VL-Max) + LLM(DeepSeek-Chat)
```

**技术栈：**

| 层 | 技术 |
|----|------|
| 前端 | uni-app + Vue3 + Vite5 |
| 后端 | FastAPI + SQLAlchemy async + MySQL + Redis |
| AI | Qwen-VL-Max(视觉) / DeepSeek-Chat(推理) / Ollama(本地备份) |
| 认证 | JWT（空密钥启动拦截） |
| 数据 | 菜谱种子数据 2,576 道 + 用户画像 + 反馈记录 |
| 部署 | Docker Compose 一键启动 |

**技术亮点：**
- Agent 编排：每阶段独立 trace_id + status + latency_ms 追踪
- 推荐引擎：硬过滤(时间)+软排序(食材50%+标签30%+偏好20%)+Fallback
- 购物清单：同名同单位累加，不兼容单位独立条目
- VLM 风险控制：解析 JSON、处理失败返回空+提示重试，不伪造假数据
- 偏好学习：高分菜谱标签自动写入用户偏好，下次推荐加权

---

## 第3页：软件规模与验证

**规模（全部远超要求）：**

| 指标 | 实际 | 要求 | 超标 |
|------|------|------|------|
| 核心接口 | 11 个（+ quality/nutrition/guide 扩展） | >3 | 3.6x |
| 源文件 | **79 个** | >5 | 15.8x |

**代码量：**

| 部分 | 行数 |
|------|------|
| 后端 Python（6模块） | 2,211 |
| 前端 Vue/JS/CSS | 5,621 |
| 测试（pytest） | 212 |
| 全量工程（含菜谱数据） | ~146k |

**自动化测试：** 23 个 pytest 通过，覆盖 auth/sense/decision/shopping/agent 模块

**构建验证：** H5 build 通过，Docker Compose 可一键启动

---

## 第4页：核心算法与工程难点

**Agent 编排流水线：**
```
用户输入 → 意图解析(DeepSeek→Ollama→正则三级降级)
  → Sense(VLM识别，失败返回空+提示重试)
  → Decision(硬过滤+软排序，全淘汰触发Fallback)
  → Task(清单合并，人数参数智能调整)
  → 返回 trace_id + stages + degraded 标记
```

**推荐引擎打分公式：**
```
总分 = 食材匹配(精确+模糊) × 0.5 + 标签匹配(口味+目标) × 0.3 + 偏好匹配(历史) × 0.2
全部归一化 0~1，保证权重有效
```
每条推荐带 reasons（code+text+meta），前端可解释"为什么推荐这个"。

**购物清单合并规则：**
- 同名+同单位 → 数量累加（300g + 400g = 700g）
- 不同单位 → 保留独立条目
- 人数参数 → DeepSeek 智能调整全表数量

**偏好学习闭环：**
- 评分 ≥4 → 菜谱标签写入用户画像
- 评分 ≤2 → 移除匹配标签
- 下次推荐加权排序

---

## 第5页：现场演示路线

**主线演示（前端，约 7 分钟）：**

| 步骤 | 操作 | 展示内容 |
|------|------|---------|
| 1 | 打开首页，输入"牛肉南瓜减脂30分钟" | Agent 意图解析+回复文字+菜谱列表 |
| 2 | 点击一道菜谱 | 菜谱详情：做法步骤+营养+文化故事 |
| 3 | 识别页 → 拍照/上传 | VLM 真 AI 识别食材（新鲜度+特征+分量） |
| 4 | 进入健康看板 → 购物清单 | 多菜谱合并+挑拣建议 |
| 5 | 去反馈页评分 | 偏好自动更新 |

**兜底方案（API 直接展示，约 2 分钟）：**

如果前端任何环节卡住，立刻切到 Swagger 页面直接调接口：
```
/v1/agent/execute     → 自然语言全流程
/v1/decision/meal-plan → 推荐菜谱
/v1/task/merge-list   → 清单合并
/v1/feedback/meal     → 评分反馈
```

**最后一句话：** "我们不是做一个菜谱 App，而是把识别、推荐、执行、反馈串成一条可追踪的 Agent 流水线。前端为主演示，API 兜底保证稳定。"

---

## Gemini 生图 Prompt

### 第1页用：四格场景图
```
A 2x2 grid illustration showing 4 food AI scenarios.
Top-left: person photographing fridge ingredients, label "家庭烹饪".
Top-right: person checking nutrition chart on phone, label "健康饮食".
Bottom-left: shopping cart with merged ingredient list, label "购物执行".
Bottom-right: star rating feeding back to a profile icon with arrow, label "长期个性化".
Green (#059669) accent in each quadrant. Clean flat style, white background.
Below the grid: "B → Y → T → E" in a connected arrow line.
```

### 第2页用：技术架构图
```
A 4-layer stacked architecture diagram.
Layer 1 "uni-app Frontend": phone icon with "Vue3 + Vite5".
Layer 2 "FastAPI Layer": horizontal pipeline of 4 connected boxes: "B-Sense", "Y-Decision", "T-Task", "E-Feedback".
Layer 3 "AI Models": three icons labeled "Qwen-VL-Max", "DeepSeek-Chat", "Ollama".
Layer 4 "Data": icons for "MySQL", "Redis", "2,576 recipes".
Green (#059669) gradient top to bottom. Clean flat design, white background.
```
