# ByteSavor 项目总流程与答辩说明

更新时间：2026-06-15

## 1. 项目定位

ByteSavor 是一个基于多模态 Agent 的全场景饮食全链路解析系统。它不是单纯调用一个识别 API，而是围绕用户“看见食物、理解约束、执行饮食决策、形成长期记忆”的完整流程设计。

系统主线是 B-Y-T-E：

```text
B 感知：图片/文本输入 -> 食材、菜品、分量、品质、餐盘识别
Y 推理：结合目标、偏好、库存、营养缺口 -> 推荐下一餐或分析结果
T 执行：生成今日三餐计划、购物清单、探店讲解、文本导入
E 反馈：确认已吃、评分、删除错误记录 -> 更新长期营养与偏好记忆
```

关键边界：

- 识别、推荐、分析不等于已经摄入。
- 只有用户点击“完成这一餐”或“确认已吃并计入今日”后，营养才写入长期记录。
- 已计入的数据如果发现错误，可以在健康看板删除，删除后不再进入营养汇总。
- Agent 是统一入口；角色页面是独立演示入口，便于答辩按场景讲清楚。

## 2. 文件夹结构

```text
bytesavor-backend/
├── app/                         后端 FastAPI 应用
│   ├── routers/                 API 路由层
│   ├── services/                业务服务层：VLM、推荐、Agent、营养、品质、向导
│   ├── agent/                   Agent 状态、规划器、运行时、工具注册
│   ├── models/                  SQLAlchemy ORM 模型
│   ├── core/                    配置、数据库、Redis、安全
│   └── seed/                    菜谱数据与导入脚本
├── bsapp/                       主 uni-app 前端工程
│   └── src/pages/               首页、识别、探索、健康看板、独立角色页面
├── frontend/.../bytesavor-uniapp/嵌套前端副本，已同步主要代码
├── tests/                       后端自动化测试
├── demo_tests/                  分角色演示测试说明
├── docs/                        技术文档、答辩资料、测试文档
├── ByteSavor.pptx / docs/*.pptx 原始与答辩参考 PPT
└── README.md                    后端快速启动说明
```

建议保留：

- `app/`、`bsapp/`、`tests/`、`demo_tests/`、`docs/`、`README.md`、`.env.example`、`requirements.txt`。
- `.pytest_cache/`、`__pycache__/`、`dist/build/` 属于生成产物，可不作为答辩交付重点。
- `.claude/` 是开发过程记录，不影响运行；若交付压缩包，可移到“开发记录”或不展示给老师。

## 3. 软件功能概述：按角色展示

| 角色 | 典型问题 | 前端入口 | 后端接口 | 展示重点 |
|---|---|---|---|---|
| 家庭做饭用户 | 家里有什么，下一餐怎么做 | 首页、拍照识别、探索菜谱 | `/v1/sense/analyze`、`/v1/decision/meal-plan` | 识别食材、校正、推荐多道菜 |
| 健康管理用户 | 今天营养摄入够不够 | 健康看板、一餐营养分析 | `/v1/nutrition/analyze-meal`、`/v1/nutrition/summary` | 热量、蛋白、碳水、脂肪、微量营养素 |
| 买菜用户 | 这个水果/食材值不值得买 | 品质鉴定 | `/v1/quality/assess` | 优中差、外观依据、挑选建议 |
| 探店用户 | 这道菜有什么故事，怎么吃 | 探店向导 | `/v1/guide/explore` | 菜系、历史、口味技法、最佳吃法 |
| 备餐/采购用户 | 多道菜需要买什么 | 购物清单、文本导入 | `/v1/task/merge-list`、`/v1/inventory/import` | 同名食材合并、数量保留、导入库存 |
| 高级用户/答辩演示 | 一句话完成多个步骤 | AI Agent | `/v1/agent/execute` | 规划、工具调用、推荐、清单、对话过程 |

## 4. 当前前端主流程

### 4.1 首页

首页承担“总控台”角色：

- 顶部显示今日营养分、宏量营养状态。
- “功能中枢”集中展示角色入口：
  - 状态看板
  - 拍照识别
  - 营养分析
  - 品质鉴定
  - 探店向导
  - 文本导入
  - 探索菜谱
  - 购物清单
  - 历史记录
  - 美食知识
  - 系统设置
  - 我的档案
- “今日三餐计划”显示早餐/午餐/晚餐。
- “推荐下一餐”横向展示多道菜谱。
- “AI 助手”显示对话过程和 Agent 工具执行过程。

### 4.2 食材识别到推荐

```text
拍照识别 -> VLM 返回候选食材 -> 用户删除/修订/添加 -> 导入当前库存
-> 首页读取库存 -> 推荐下一餐 -> 加入今日计划 -> 完成这一餐
-> 写入长期营养记录并扣减库存 -> 清空当前食材，推荐下一餐
```

这里修正了一个重要逻辑：导出清单或生成推荐都不代表用户已经吃了；只有完成用餐才计入。

### 4.3 一餐营养分析到长期记录

```text
一餐营养分析 -> 拍餐盘 -> 估算热量/宏量营养
-> 用户确认已吃并计入今日 -> 后端创建并完成一条 MealRecord
-> 健康看板统计 completed 记录
-> 如果发现错误，在健康看板删除该记录
```

## 5. 后端接口分层

| 层级 | 主要文件 | 职责 |
|---|---|---|
| API 路由 | `app/routers/*.py` | 参数接收、鉴权、返回统一响应 |
| 服务层 | `app/services/*.py` | 推荐、清单、营养、品质、向导、长期记忆 |
| Agent 层 | `app/agent/*.py`、`app/routers/agent.py` | 解析用户意图，规划工具调用，返回事件轨迹 |
| 数据层 | `app/models/` | User、Profile、Recipe、Inventory、MealRecord 等 |
| 基础设施 | `app/core/` | MySQL、Redis、JWT、配置 |

核心接口：

| 模块 | 接口 | 说明 |
|---|---|---|
| 认证 | `POST /v1/auth/register`、`POST /v1/auth/login` | 注册/登录，返回 JWT |
| 感知 | `POST /v1/sense/analyze` | 食材识别 |
| 推荐 | `POST /v1/decision/meal-plan` | 根据食材、目标、偏好推荐菜谱 |
| 清单 | `POST /v1/task/merge-list` | 多菜谱购物清单合并 |
| 品质 | `POST /v1/quality/assess` | 食材/水果品质鉴定 |
| 营养 | `POST /v1/nutrition/analyze-meal` | 一餐营养分析 |
| 向导 | `POST /v1/guide/explore` | 菜品文化与吃法讲解 |
| 库存 | `POST /v1/inventory/import`、`GET /v1/inventory/current` | 当前食材库存 |
| 用餐 | `POST /v1/meals/plan`、`POST /v1/meals/{id}/complete`、`POST /v1/meals/{id}/cancel` | 三餐计划、完成、删除/撤销 |
| 统计 | `GET /v1/nutrition/summary?range=day/week/weeks` | 长期营养汇总 |
| Agent | `POST /v1/agent/execute` | 多工具统一入口 |

## 6. Agent 的真实定位

项目里 Agent 不应被解释为“一个聊天框调用推荐接口”。更准确的说法：

- Agent 是“多工具编排器”。
- 它根据用户输入和图片判断需要调用哪些工具。
- 它能调用 nutrition、quality、guide、sense、decision、task 等能力。
- 前端展示 Agent 的事件轨迹，让老师看到它经历了规划、工具调用、结果汇总。

答辩时可以这样讲：

> 独立页面保证每个能力可测试、可解释；Agent 保证真实使用时用户可以一句话跨能力完成任务。我们没有把所有能力硬塞进一个接口，而是先做可独立验证的工具，再由 Agent 编排。

## 7. 分角色测试流程

### 场景一：拍照识别 -> 推荐 -> 用餐闭环

1. 登录账号。
2. 首页点“拍照识别”。
3. 上传冰箱/菜板图片。
4. 检查识别结果是否可以删除、修订、添加。
5. 确认导入当前食材。
6. 回首页看“推荐下一餐”是否出现多道菜。
7. 选择一道菜“加入今日计划”。
8. 点击“完成”。
9. 到健康看板确认今日 kcal、蛋白等发生变化。

### 场景二：文本导入 -> 推荐

1. 首页点“文本导入”。
2. 输入：`猪肉 300g，青椒 3个，西瓜 1个`。
3. 点击解析文本。
4. 删除错误项或确认导入。
5. 回首页生成推荐。

### 场景三：水果品质鉴定

1. 首页点“品质鉴定”。
2. 上传西瓜/番茄/榴莲图片。
3. 检查返回：等级、外观特征、判断依据、挑选建议。
4. 注意该流程不写入摄入。

### 场景四：一餐营养分析

1. 首页点“营养分析”。
2. 上传一顿饭图片。
3. 检查总热量、蛋白质、碳水、脂肪和目标差距。
4. 如果这顿已经吃了，点“确认已吃并计入今日”。
5. 到健康看板检查记录。
6. 如果发现错误，删除该条已计入用餐。

### 场景五：探店向导

1. 首页点“探店向导”。
2. 上传经典菜图片。
3. 检查菜品名、菜系、历史故事、口味特点、最佳吃法。
4. 如果命中内置知识库，会显示知识库标签。

### 场景六：Agent 统一入口

1. 首页 AI 助手输入：`家里有牛肉和南瓜，30分钟做个减脂餐`。
2. 查看对话过程、工具调用事件和推荐菜谱。
3. 从 Agent 推荐中记录菜谱或导出清单。

## 8. 答辩评分点对应

| 评分要求 | 项目对应内容 |
|---|---|
| 软件功能设计合理，有逻辑性，符合功能场景 | B-Y-T-E 全链路；按家庭做饭、健康管理、买菜、探店、采购、Agent 六类角色组织 |
| 功能点实现完整，符合预期需求 | 识别、推荐、清单、品质、营养、探店、文本导入、三餐计划、长期营养记录 |
| 现场演示顺畅、数据处理正确、无 Bug | 推荐按库存变化更新；完成才计入；错误可删除；识别结果可校正 |
| 软件规模符合要求 | 后端 FastAPI + 前端 uni-app + 多模块测试，源文件、接口、代码量均明显超过要求 |
| 特色功能、设计亮点、技术难点 | 多模态 VLM、Agent 工具编排、长期营养记忆、三餐执行闭环、角色化独立页面 |

## 9. 运行方式

后端：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
JWT_SECRET=test-review-secret venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

前端 H5：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run dev:h5 -- --host 0.0.0.0 --port 5174
```

手机访问时，确保手机和电脑在同一局域网，并把前端 API 地址设为电脑局域网 IP 的 `:8000`。

## 10. 验证命令

后端测试：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q
```

前端构建：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

嵌套前端构建：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/frontend/bytesavorapptest5_31/bytesavorapptest5_31/bytesavor-uniapp
npm run build:h5
```

## 11. 仍需注意的问题

1. VLM 识别质量取决于外部模型和图片质量。答辩时建议准备稳定测试图片。
2. `cancel` 当前承担“删除/撤销计入”的语义，后续可新增更明确的 `DELETE /v1/meals/{id}`。
3. 一餐营养分析按 VLM 食物识别和内置热量表估算，适合作为健康建议，不应表述为医学级精确计算。
4. 推荐算法已能跑通闭环，但权重仍属于工程启发式，后续可用标注集做 NDCG/Hit Rate 离线评估。
5. OpenID 登录仍是课程项目简化版本；生产级微信登录需要后端 code2session 校验。

