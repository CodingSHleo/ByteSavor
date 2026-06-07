# ByteSavor 期末展演 PPT（5页）

> 要求：≤5页 PPT + 10分钟演示。我们数据远超要求（11接口/49文件/14264行）。

---

## 第1页：我们解决了什么问题

**标题：** ByteSavor — 从"四个痛点"到"一个闭环"

**上半部分：四个场景的痛点（来自原始PPT Slide 4-5）**

| 场景 | 痛点 | 现有App的不足 |
|------|------|-------------|
| 生活烹饪 | 不知道做什么/怎么做/怎么买菜 | 识图只能分类，看不出新鲜度 |
| 探店美食 | 不知道菜是什么/背后故事 | 缺乏文化知识图谱 |
| 健康饮食 | 热量多少/是否达标 | 营养数据透明度<20% |
| 决策损耗 | App间反复跳转 | 识图-营养-清单互相孤立 |

**下半部分：竞品Baseline对比（来自原始PPT Slide 8）**

| 能力 | 薄荷健康 | 下厨房 | 小红书 | **ByteSavor** |
|------|---------|--------|--------|-------------|
| 拍照识食材 | ✅ 基础分类 | ❌ | ❌ | ✅ **细粒度(新鲜度+性状+分量)** |
| 个性化推荐 | ❌ | 标签匹配 | ❌ | ✅ **偏好加权+反馈学习** |
| 购物清单 | ❌ | 单菜谱 | ❌ | ✅ **多菜谱合并+挑拣建议** |
| 营养分析 | ✅ 手动录入 | ❌ | ❌ | ✅ **拍照即算+份量参照** |
| 文化向导 | ❌ | 部分 | 零散 | ✅ **经典菜知识库+故事** |
| 全链路打通 | ❌ 孤立 | ❌ 孤立 | ❌ | ✅ **B→Y→T→E闭环** |

**核心论点：** 竞品是"工具集合"，ByteSavor 是"决策引擎"。我们的 Baseline 设定在决策逻辑，而非存储规模。

**配图：** Gemini 生成 Baseline 对比雷达图

---

## 第2页：B-Y-T-E 技术架构

**标题：** B-Y-T-E 智能闭环 + 技术实现

**BYTE框架（来自原始PPT Slide 9）：**

```
B (Better Perception / 感知)
  技术: Qwen-VL-Max (DashScope)
  技能: 识别食材名称/新鲜度/性状特征/分量估算
  降级: VLM不可用 → Ollama本地 → 提示重试

Y (Yielding Decisions / 决策)  
  技术: DeepSeek-Chat + 推荐引擎Pipeline
  技能: 个性化菜谱推荐(食材50%+标签30%+偏好20%)
  特色: 硬过滤+软排序+Fallback+可解释Reasons

T (Task Automation / 执行)
  技术: Agent编排 + 购物合并引擎
  技能: 多菜谱清单合并/同单位累加/挑拣建议
  特色: 人数参数+DeepSeek智能调整数量

E (Evolving Feedback / 进化)
  技术: 偏好学习 + 反馈闭环
  技能: 评分自动更新偏好标签
  特色: 越用越懂你
```

**右下角：技术栈速览**

```
前端: uni-app (Vue3+Vite5) 微信小程序/H5
后端: FastAPI + MySQL + Redis + Docker
AI:   Qwen-VL-Max + DeepSeek-Chat + Ollama
数据: Ta-da真实数据集 2576道菜谱
```

**配图：** Gemini 生成 B-Y-T-E 四象限架构图

---

## 第3页：软件规模与迭代

**标题：** 从V1.0到V3.0 — 我们真正交付了什么

**V1→V2→V3 迭代路线（来自原始PPT Slide 18，更新为实际完成情况）：**

| 版本 | 原始规划 | 实际完成 |
|------|---------|---------|
| V1.0 | 拍菜识图+基础画像 | ✅ FastAPI骨架+JWT认证+MySQL |
| V2.0 | RAG+结构化推荐 | ✅ 推荐引擎Pipeline+2573道菜谱 |
| V3.0 | Agent全链路闭环 | ✅ VLM真AI识别+Agent编排+5场景演示 |

**软件规模（答辩硬指标）：**

| 指标 | 我们 | 要求 | 倍数 |
|------|------|------|------|
| 接口/用例 | 11 个 | >3 | 3.6x |
| 源文件 | 49 个 | >5 | 9.8x |
| 代码行数 | 14,264 行 | >500 | 28x |
| 菜谱数据 | 2,576 道 | - | 真实数据集 |
| 自动化测试 | 23 个(pytest) | - | 12 passed |

**可行性分析（来自原始PPT Slide 19）：**
- 不盲目自研大模型，做"算法系统集成商"
- 利用 Qwen-VL Zero-shot 能力，绕过海量数据标注
- 定位于 Lightweight Agent，"即用即走、高频决策"

---

## 第4页：五大演示场景

**标题：** 现场演示 — 5个完整场景

| # | 场景 | 演示内容 | 对应接口 |
|---|------|---------|---------|
| 1 | 拍照推荐 | 拍食材→VLM识别→个性化推荐→评分反馈 | Sense→Decision→Feedback |
| 2 | 清单导出 | 3道菜合并16项清单+挑拣建议+人数调整 | Task/merge-list |
| 3 | 品质鉴定 | 拍水果→品质优/中/差+挑选标准+购买建议 | Quality/assess |
| 4 | 营养分析 | 拍一顿饭→热量计算+一拳/一掌参照+日标对比 | Nutrition/analyze-meal |
| 5 | 探店向导 | 拍菜品→菜系/历史故事/最佳吃法(8道经典菜) | Guide/explore |

**演示亮点：**
- VLM 真 AI 识别（非 Mock！）
- 个性化推荐引擎实时打分
- DeepSeek 智能意图解析
- 一键导出购物清单+食材挑拣建议
- 反馈学习：评分后偏好自动更新

---

## 第5页：总结与未来

**标题：** 我们做了什么 & 接下来去哪

**已完成：**
- ✅ B-Y-T-E 全链路闭环（感知→决策→执行→反馈）
- ✅ 真实 VLM + LLM 接入（非 mock 演示）
- ✅ 个性化推荐引擎（偏好学习+反馈闭环+可解释性）
- ✅ 2576 道菜谱真实数据集
- ✅ 5 个可演示完整场景
- ✅ Docker 一键部署 + pytest 自动化测试

**未来方向（来自原始PPT Slide 21）：**
- GraphRAG 知识图谱推理（Neo4j 已预留接口）
- LangGraph Agent 状态机（代码已预留适配层）
- ByteSavor 5.0：从饮食 Agent 到智慧生活伴侣
  - 接入智能手表/冰箱传感器 → 全场景健康管理
  - 老人独居监测 → 子女周报推送

**致谢**

---

## Gemini 生图 Prompt

### 图1：竞品Baseline对比图（第1页用）
```
A clean comparison table or radar chart showing 6 food apps compared across 6 dimensions: 
"Food Recognition", "Personalized Recommendation", "Shopping List Merge", 
"Nutrition Analysis", "Cultural Guide", "End-to-End Pipeline".
ByteSavor scores highest on all 6. 
Other apps score partial.
Clean white background, green (#059669) for ByteSavor bars, gray for others.
Flat design, suitable for presentation slide. English labels.
```

### 图2：B-Y-T-E 四象限图（第2页用）
```
A 4-quadrant circular diagram representing an AI pipeline.
Top-left "B": magnifying glass over food photo, label "Perception (VLM)".
Top-right "Y": brain with lightbulb, label "Decision (DeepSeek)".
Bottom-right "T": shopping cart with checkmark, label "Task (Agent)".  
Bottom-left "E": star with arrow looping back, label "Feedback (Learning)".
Arrows connecting B→Y→T→E in a circle.
Color scheme: green (#059669) gradient for each quadrant.
Clean flat design, white background. Minimal text.
```
