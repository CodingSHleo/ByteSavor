# ByteSavor 期末展演 PPT（5页）

> 展演要求：≤5页 PPT，覆盖①功能概览②技术栈③软件规模。10分钟演示。

---

## 第1页：功能概览（按角色+场景）

**标题：** ByteSavor — AI 饮食全链路助手

**一句话：** 拍照识食材 → 智能推菜谱 → 导出购物清单 → 越用越懂你

**四个用户角色+场景：**

| 角色 | 痛点 | ByteSavor 怎么解决 | 亮点 |
|------|------|------------------|------|
| 家庭主厨 | 面对一堆食材不知道做什么 | 拍照→VLM识别→个性化推荐菜谱 | 细粒度视觉（新鲜度+性状+分量） |
| 健身人群 | 不知道吃了多少热量 | 拍一顿饭→热量分析→一拳/一掌参照→日标对比 | 份量参照体系（一拳米饭=150g=175kcal） |
| 探店美食家 | 不知道菜是什么/背后故事 | 拍菜品→菜系识别→历史故事→最佳吃法 | 8道经典菜知识库（白切鸡/东坡肉/佛跳墙...） |
| 采购者 | 不知道怎么挑好食材 | 拍水果→品质鉴定(优/中/差)→挑选标准 | 西瓜听声/榴莲闻味/西红柿看色 |

**核心论点（来自原始PPT）：** 竞品（薄荷健康/下厨房/小红书）是"工具集合"，各自孤立；ByteSavor 是"决策引擎"，B→Y→T→E 全链路闭环。

**配图：** Gemini 生成四角色场景图

---

## 第2页：技术栈（含亮点难点）

**标题：** 技术架构

```
┌─────────────────────────────────────────┐
│  前端  uni-app (Vue3+Vite5)             │
│        H5 + 微信小程序双端               │
├─────────────────────────────────────────┤
│  后端  FastAPI + MySQL + Redis + Docker │
│        ┌──────┬──────┬──────┬────────┐  │
│        │ B-感知│ Y-决策│ T-执行│ E-反馈 │  │
│        │ VLM  │推荐引擎│Agent │偏好学习│  │
│        └──────┴──────┴──────┴────────┘  │
├─────────────────────────────────────────┤
│  AI    Qwen-VL-Max(DashScope)           │
│        DeepSeek-Chat(推理)              │
│        Ollama qwen2.5:1.5b(本地备份)    │
├─────────────────────────────────────────┤
│  数据  Ta-da数据集 2576道菜谱            │
└─────────────────────────────────────────┘
```

**技术亮点与难点：**

| 难点 | 解决方案 |
|------|---------|
| VLM 识别不稳定/超时 | 三级降级：DashScope → Ollama → 提示重试；图片前端压缩至800px |
| 推荐不够个性化 | 引擎三层打分：食材匹配50%+标签30%+偏好20%，全部归一化0~1 |
| AI 失败不能影响演示 | 每层独立降级：VLM不可用→提示重试；LLM不可用→正则兜底 |
| Agent 编排复杂 | Provider 抽象模式，每阶段独立 trace+status+latency 追踪 |

**配图：** Gemini 生成四层架构图

---

## 第3页：软件规模

**标题：** 软件规模

**答辩硬指标（全部远超要求）：**

| 指标 | 我们 | 要求 | 超标 |
|------|------|------|------|
| 用例/接口 | 11 个 | >3 | 3.6倍 |
| 源文件 | 49 个 | >5 | 9.8倍 |
| 代码行数 | 14,264 行 | >500 | 28倍 |

**代码分布：**

| 部分 | 行数 |
|------|------|
| 后端 Python（6模块+测试） | 2,046 |
| 前端 Vue+JS+CSS | 5,382 |
| 菜谱种子数据 | 132,000+（JSON） |
| 文档+配置+其他 | ~6,800 |

**迭代历程：**

| 版本 | 目标 | 状态 |
|------|------|------|
| V1.0 | 拍菜识图+基础画像+FastAPI骨架 | ✅ |
| V2.0 | 推荐引擎Pipeline+2576道菜谱+个性化排序 | ✅ |
| V3.0 | Agent全链路闭环+5场景演示+VLM真AI | ✅ 本次展演版本 |

**自动化测试：** pytest 23 个用例，覆盖 agent/decision/shopping/auth/sense 模块

---

## 第4页：5个演示场景

**标题：** 现场演示

| # | 场景 | 流程 | 涉及接口 |
|---|------|------|---------|
| 1 | 拍照推荐 | 注册→设偏好→拍照→VLM识别→推荐菜谱→查看做法→评分反馈 | Sense→Decision→Feedback |
| 2 | 清单导出 | 3道菜合并→16项清单+挑拣建议→人数调整数量 | Task/merge-list |
| 3 | 品质鉴定 | 拍水果→品质等级(优/中/差)+挑选标准+购买建议 | Quality/assess |
| 4 | 营养分析 | 拍一顿饭→热量+蛋白质+碳水+脂肪→份量参照(一拳/一掌)→日标对比 | Nutrition/analyze-meal |
| 5 | 探店向导 | 拍菜品→菜系+历史故事+最佳吃法(白切鸡/东坡肉/麻婆豆腐...) | Guide/explore |

**演示亮点：**
- VLM 真 AI 识别（非 Mock！返回真实食材+新鲜度+特征）
- Agent 一句话走全流程（DeepSeek 意图解析）
- 反馈学习：评分后偏好自动更新
- 图片压缩加速+60s超时容错

---

## 第5页：总结

**标题：** 我们完成了什么

- ✅ B-Y-T-E 全链路闭环：感知→决策→执行→反馈
- ✅ 真实 AI 接入：Qwen-VL-Max + DeepSeek-Chat（非 mock）
- ✅ 个性化推荐引擎：偏好加权+反馈学习+可解释 Reasons
- ✅ 2576 道菜谱真实数据集（Ta-da 公开数据集）
- ✅ 5 个可演示完整场景，23 个自动化测试
- ✅ 图片压缩+降级容错+密码保护，演示稳定可靠

**团队：** ByteSleep — 李文彬 鲁洁 陈子朋 罗少裴 刘一茹 杨仁宇 汪自强

---

## Gemini 生图 Prompt

### 图1：四角色场景图（第1页用）
```
A split-screen illustration showing 4 user scenarios for a food AI app.
Top-left: person photographing fridge, label "家庭主厨".
Top-right: person at gym looking at phone, label "健身人群".  
Bottom-left: person at restaurant photographing dish, label "探店美食家".
Bottom-right: person selecting fruit at market, label "采购者".
Each quadrant has a matching green (#059669) accent element.
Clean flat illustration style, white background. Minimal text, icon-focused.
```

### 图2：四层技术架构图（第2页用）  
```
A 4-layer stacked architecture diagram.
Layer 1 "Frontend": phone icon with uni-app/Vue3 label.
Layer 2 "Backend": 4 connected boxes labeled "B-Perception", "Y-Decision", "T-Task", "E-Feedback" in a pipeline.
Layer 3 "AI Models": icons for Qwen-VL, DeepSeek, Ollama.
Layer 4 "Data": database icon with "2,576 recipes" label.
Green (#059669) gradient from top to bottom.
Clean flat design, white background, minimal text.
```
