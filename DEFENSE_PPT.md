# ByteSavor 期末展演 PPT 内容

## 第1页：软件功能概览（按角色展示）

**标题：** ByteSavor — AI 饮食全链路助手

**三行定位：**
- 拍一张照片 → AI 识别食材 → 推荐菜谱 → 生成清单 → 学习偏好
- 基于 B-Y-T-E 智能闭环（感知→决策→执行→反馈）
- 2573 道菜谱 + Qwen-VL 视觉识别 + DeepSeek 推理引擎

**四个用户场景：**

| 角色 | 场景 | 亮点 |
|------|------|------|
| 家庭主厨 | 拍冰箱→识别食材→推荐菜谱→导出清单 | 食材自动合并+挑拣建议 |
| 健身人群 | 拍一顿饭→热量分析→份量参照→日标对比 | 一拳/一掌参照体系 |
| 探店美食家 | 拍菜品→识别菜名→文化故事→最佳吃法 | 8道经典菜知识库 |
| 水果采购 | 拍水果→品质鉴定→挑选标准→购买建议 | 优/中/差分级 |

**本页配图：** 用 Gemini 生成一张 BYTE 全链路流程示意图

---

## 第2页：技术栈与难点

**标题：** 技术架构与亮点

**技术栈（分层展示）：**
```
前端: uni-app (Vue3 + Vite5) 微信小程序/H5双端
后端: FastAPI + MySQL 8.0 + Redis + Docker
AI:   Qwen-VL-Max(视觉) + DeepSeek-Chat(推理) + Ollama(本地)
数据: Ta-da 数据集 2573道菜谱
```

**技术难点与解决方案：**

| 难点 | 解决方案 |
|------|---------|
| VLM 识别不稳定 | 三级降级：DashScope → Ollama 本地 → 提示重试 |
| 推荐不个性化 | 用户画像加权：食材匹配50%+标签30%+偏好20% |
| 图片上传慢 | 前端压缩到800px+60s超时 |
| Agent 编排复杂 | Provider 抽象模式，每阶段独立追踪 |
| JWT 安全 | 空密钥启动拦截，生产必须配置 |

**本页配图：** 用 Gemini 生成一张技术架构分层图

---

## 第3页：软件规模

**标题：** 软件规模一览

| 指标 | 数值 | 要求 | 状态 |
|------|------|------|------|
| 接口/用例 | 11 个 | >3 | ✅ 超标 3.6 倍 |
| 源文件 | 49 个 | >5 | ✅ 超标 9.8 倍 |
| 代码总行数 | 14,264 行 | >500 | ✅ 超标 28 倍 |
| 菜谱数据 | 2,576 道 | - | Ta-da 真实数据集 |
| 测试用例 | 23 个 | - | pytest 自动化 |
| 特色功能 | 5 个场景 | - | VLM+Agent+品质鉴定+营养分析+探店向导 |

**五个演示场景即五个用例：**
1. 拍照识别 → 个性化推荐 → 反馈学习
2. 多菜谱 → 购物清单合并+挑拣建议
3. 水果拍照 → 品质鉴定+挑选标准
4. 拍一顿饭 → 热量分析+份量参照
5. 拍菜品 → 菜系识别+文化故事

---

## 第4页：演示场景（备用/过渡页）

**标题：** 现场演示 — 5 个场景

1. **拍照推荐** — B-Y-T-E 全闭环
2. **清单导出** — 3 道菜合并 16 项+挑拣建议
3. **品质鉴定** — 西瓜/榴莲品质分级
4. **营养分析** — 一拳米饭=150g=175kcal
5. **探店向导** — 8 道经典菜文化知识库

---

## 第5页：总结与展望

**标题：** 我们做了什么

- ✅ 完成了从"拍照"到"执行"的全链路闭环
- ✅ 接入了真实 VLM 和 LLM（非 mock 演示）
- ✅ 建立了个性化推荐引擎（偏好学习+反馈闭环）
- ✅ 构建了 2573 道菜谱的真实数据集
- ✅ 实现了 5 个可演示的完整场景

**未来方向：**
- GraphRAG 知识图谱推理（Neo4j 已预留接口）
- LangGraph Agent 状态机（代码已预留适配层）
- 微信小程序正式上线

---

## Gemini 生图 Prompt

### 图1：BYTE 全链路流程图（放第1页）

```
A clean, modern tech diagram showing a 4-step circular pipeline for an AI food assistant app. 
Step B "Perception": a phone camera icon pointing to food ingredients. 
Step Y "Decision": a brain icon with recipe cards. 
Step T "Task": a shopping cart icon with a merged list. 
Step E "Feedback": a star rating icon with an updating profile. 
Arrows connect B→Y→T→E in a circle. 
Color scheme: green (#059669) and white. 
Minimalist, flat design, suitable for a presentation slide. 
No text other than B, Y, T, E labels. 
White background.
```

### 图2：技术架构分层图（放第2页）

```
A clean 3-layer architecture diagram for a food AI app.
Top layer "uni-app": phone icons showing WeChat mini program and H5.
Middle layer "FastAPI Backend": boxes for VLM Vision, DeepSeek Reasoning, Recommendation Engine, Agent Pipeline.
Bottom layer "Data": icons for MySQL, Redis, Ollama, DashScope API.
Arrow flowing from top to bottom.
Color scheme: green (#059669) and gray (#374151).
Minimalist flat design, white background. No detailed text, just layer labels.
```
