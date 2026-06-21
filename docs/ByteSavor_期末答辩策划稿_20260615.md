# ByteSavor 期末答辩策划稿

更新时间：2026-06-15

## 1. 展演要求对齐

期末展演限制是：PPT 不超过 5 页，PPT + 软件演示共 10 分钟，提问约 4 分钟。评分重点里，现场演示顺畅和数据处理正确占 40 分，所以 PPT 不要讲太散，要把时间留给可跑通的流程。

建议时间分配：

| 环节 | 时间 | 目标 |
|---|---:|---|
| PPT 第 1-5 页 | 3 分钟 | 讲清楚它是什么、谁用、怎么实现、规模够不够 |
| 手机/网页演示 | 6 分钟 | 跑一条主线，再快速展示 2 个角色页面 |
| 兜底 API/测试结果 | 1 分钟 | 如果现场网络/模型慢，用测试和接口兜底 |

## 2. PPT 五页结构

### 第 1 页：项目一句话与全场景定位

标题：

> 基于多模态 Agent 的全场景饮食全链路解析系统

副标题：

> 从“看见食物”到“决定吃什么、怎么买、吃完如何记住”的饮食 Agent

页面内容建议：

- 左侧放一张高级 UI 风格手机界面图，展示首页、识别、营养看板三个小屏。
- 右侧用四个角色讲功能，不要只列模块名：
  - 家庭做饭：拍照识别冰箱食材，推荐下一餐。
  - 健康管理：按用户目标计算每日摄入和缺口。
  - 买菜/备餐：合并购物清单，判断食材品质。
  - 探店/学习：识别菜品，讲菜系故事、吃法和技法。

讲稿：

> 我们做的不是一个单点菜谱工具，而是一个饮食场景里的多模态 Agent。用户可以拍食材、拍菜、输入文字，也可以直接和 AI 助手对话。系统会把识别、推荐、清单、营养记录和偏好学习串起来，最后形成一个可持续更新的个人饮食记忆。

配图 prompt：

```text
Design a premium presentation hero image for "ByteSavor", a multimodal food agent app.
Show three editable mobile UI screens floating slightly: ingredient recognition, recipe recommendation, nutrition dashboard.
Use refined green, mint, warm amber and soft off-white palette, with subtle glass layers and clean food icons.
Add a thin circular flow line around the screens with four labels: Sense, Decide, Execute, Learn.
Professional Chinese university software engineering defense style, elegant but not overly decorative, high contrast, dark readable text area, 16:9.
```

### 第 2 页：按角色展示功能完整性

这一页可以和你喜欢的 baseline 图结合：用“现有饮食软件通常只覆盖一个点”做对比，然后给出 ByteSavor 的全链路。

页面结构：

| 角色 | 用户任务 | ByteSavor 已实现 |
|---|---|---|
| 做饭用户 | 家里有什么，怎么做 | 食材识别、校正、菜谱推荐、多菜谱清单 |
| 健康用户 | 今天还缺什么营养 | 个性化目标、宏量/微量营养素、日/周统计 |
| 买菜用户 | 这个食材好不好 | 水果/食材品质判断、挑选建议 |
| 探店用户 | 这道菜是什么，怎么吃 | 菜品识别、历史故事、口味技法、最佳吃法 |
| 长期用户 | 系统能不能越来越懂我 | 摄入确认、评分反馈、偏好数据库、推荐加权 |

讲稿：

> 这一页重点是功能不是堆按钮，而是按角色组织。比如做饭用户关心“我现在能做什么”，健康用户关心“今天还缺什么”，探店用户关心“这道菜怎么理解”。所以我们把同一个多模态能力拆成五条可演示的角色路径，同时保留 Agent 作为统一入口。

配图 prompt：

```text
Create a clean benchmark comparison diagram for a food AI app.
Left side: "Traditional apps" as isolated cards: calorie counter, recipe search, shopping list, food scanner, each disconnected.
Right side: "ByteSavor" as one connected full-chain flow: photo/text input -> food understanding -> personalized recommendation -> shopping/meal execution -> nutrition memory and preference learning.
Use elegant green and amber accents, rounded but sharp professional cards, Chinese labels, 16:9 presentation, editable-looking diagram style, no cartoon characters.
```

### 第 3 页：技术架构与 Agent 闭环

页面内容：

```text
uni-app / Vue3 前端
        |
FastAPI API 层
        |
B 感知：VLM 食材/餐盘/菜品/品质识别
Y 决策：推荐引擎 + 用户画像 + 营养目标
T 执行：三餐计划、库存扣减、购物清单
E 反馈：确认摄入、评分文本、LLM 解析偏好、写入长期记忆
        |
MySQL + Redis + Recipe Dataset + VLM/LLM Provider
```

技术亮点要讲人话：

- VLM 负责“看懂图片”，不是用 mock 结果。
- LLM 负责“理解用户反馈和菜品故事”，不是只做聊天。
- 推荐系统不是只返回数据库前几条，而是结合食材、目标、偏好、忌口和时间限制排序。
- 识别/导出不等于摄入，只有用户确认摄入才写入营养长期记录。
- 偏好学习不是静态标签，用户评分和文字原因会进入 `preference_memories`。

讲稿：

> 我们把 Agent 拆成 B-Y-T-E 四个阶段。B 是感知，负责把图片或文字转成结构化食材、菜品和分量；Y 是决策，结合用户目标和偏好做推荐；T 是执行，生成清单、三餐计划和库存扣减；E 是反馈，用户确认吃完之后，营养进入长期记录，评分文字会被 LLM 解析成偏好记忆，下次推荐会读取这些记忆。

配图 prompt：

```text
Draw a polished technical architecture diagram for a multimodal food agent.
Top: uni-app mobile frontend.
Middle: FastAPI backend with four connected modules labeled B Sense, Y Decision, T Execution, E Feedback.
Sense connects to VLM; Decision connects to recommendation engine; Execution connects to meal plan/inventory/shopping list; Feedback connects to preference memory.
Bottom: MySQL, Redis, recipe dataset, VLM provider, LLM provider.
Use a circular arrow to show feedback returns to future recommendation.
Professional, high-end UI colors: deep green, mint, amber, off-white, dark readable text, 16:9.
```

### 第 4 页：角色化测试与工程质量

这一页不要只讲“跑了哪些测试”，而是把测试和功能角色一一对应。这样老师看到的不是孤立测试报告，而是“每个用户场景都有对应验证”。

建议页面标题：

> 五类角色场景，一套可验证流程

角色化测试矩阵：

| 角色 | 功能路径 | 测试材料 | 验证点 |
|---|---|---|---|
| 家庭做饭用户 | 拍照识别 -> 校正 -> 推荐菜谱 -> 导出清单 | `demo_tests/场景一_拍照推荐` | 食材可删改、推荐多道菜、清单不自动计入摄入 |
| 健康管理用户 | 餐盘识别 -> 营养估算 -> 确认摄入 -> 健康看板 | `demo_tests/场景四_营养分析` | 只有确认摄入才写入今日；删除后不再统计 |
| 买菜用户 | 拍水果/食材 -> 品质鉴定 -> 挑选建议 | `demo_tests/场景三_品质鉴定` | 等级、依据、购买建议完整返回 |
| 探店用户 | 拍菜品 -> 识别菜名 -> 故事/口味/吃法 | `demo_tests/场景五_探店向导` | VLM 识别后，LLM 补全讲解内容 |
| 备餐采购用户 | 多菜谱/文本输入 -> 合并购物清单 | `demo_tests/场景二_清单导出` | 同名食材合并、数量保留、可复制导出 |
| 长期个性化用户 | 确认摄入 -> 评分原因 -> 偏好记忆 -> 下次推荐 | `tests/test_feedback_memory.py` | `preference_memories` 写入 liked/avoid 信号 |

讲稿：

> 我们的测试是按角色设计的。比如家庭做饭用户测的是识别、校正和推荐；健康管理用户测的是“确认摄入才计入今日”；探店用户测的是菜品识别后能不能补全故事和吃法。这样每一个功能点都能回到真实使用场景，而不是为了测试而测试。

页面下半部分再放工程规模，用三个小数字卡片即可：

规模数据（当前工程统计）：

| 指标 | 当前项目 | 要求 |
|---|---:|---:|
| 自动化测试文件 | 11 个 | 用例超过 3 个 |
| 主要源文件 | 105 个 | 源文件超过 5 个 |
| 代码行数 | 149,823 行 | 代码超过 500 行 |

可讲的测试：

- `tests/test_auth.py`：登录、用户画像、个性化目标。
- `tests/test_decision.py`：家庭做饭/推荐路径，菜谱详情和微量营养素。
- `tests/test_meals_inventory.py`：健康用户路径，三餐计划、确认摄入、删除记录、营养汇总。
- `tests/test_feedback_memory.py`：长期个性化路径，评分文本写入偏好记忆，推荐读取 liked/avoid 信号。
- `tests/test_food_guide.py`：探店用户路径，识别后补全故事、口味、吃法。

讲稿：

> 软件工程课不只看能不能点开，还看结构和验证。我们把测试和角色功能绑定：每个角色都有测试图片、测试输入、接口链路和验证点。尤其是几个容易出错的边界，我们都写进测试：识别不等于摄入、确认摄入才写营养、删除后不再统计、反馈文字要进入偏好库。

配图 prompt：

```text
Create a premium software engineering validation slide visual.
Show three large metrics cards: 105 source files, 149,823 lines, 11 pytest files.
Below, show a checklist timeline: Auth, Sense, Decision, Meal Memory, Preference Memory, Food Guide.
Use ByteSavor green and amber palette, clean dashboard style, Chinese labels, 16:9, high contrast black text.
```

### 第 5 页：现场演示路线与收束

主线演示：

1. 登录测试账号，设置目标：减脂/均衡/增肌，填写身高体重、运动频次。
2. 拍照识别食材，展示可删除、可修订，避免西瓜被多个候选重复计入。
3. 生成清单页，展示本次食材营养、占每日目标比例、今日缺口。
4. 点击“确认摄入并更新今日”，展示健康看板今日摄入更新。
5. 给这餐评分并写原因，例如“喜欢清淡少油，高蛋白，牛肉口感好”。
6. 回到推荐/Agent，说明推荐会读取偏好记忆。

快速展示：

- 品质鉴定：展示水果品质和挑选建议。
- 探店向导：展示菜名、历史故事、口味技法、最佳吃法。
- 文本导入：展示不用图片也可以输入食材。

结尾话术：

> 最后总结一下，ByteSavor 的重点不是“我接了几个 AI 接口”，而是我们把饮食场景拆成可验证的工程流程：识别之后能校正，推荐之后能执行，吃完之后能进入营养记录，评分之后能形成偏好记忆。这个闭环让系统下一次推荐时真的更贴近用户，而不是每次都从零开始。

## 3. 答辩提问准备

### 问：这和普通菜谱推荐有什么区别？

答：

> 普通推荐通常只看关键词或菜谱分类。我们的推荐会读取当前食材、用户目标、每日营养缺口、历史偏好和忌口，并且和三餐执行、营养记录连接。也就是说它不是一次性推荐，而是在用户长期使用中持续更新。

### 问：你们的 Agent 具体体现在哪里？

答：

> Agent 不只是聊天框。我们的设计是先把识别、推荐、清单、营养、品质、探店做成独立工具，再由 Agent 根据用户输入规划调用。这样每个工具可以单独测试，Agent 又能完成跨场景任务，比如“家里有牛肉和南瓜，30 分钟做个减脂餐”。

### 问：营养数据是否准确？

答：

> 我们把它定位为饮食建议级估算，不宣称医学级精确。系统会根据识别分量、常见食材营养表和用户目标计算，并且允许用户确认、修订和删除错误记录。这个边界在软件里是明确的。

### 问：为什么要用户确认摄入？

答：

> 因为识别一张图不代表用户真的吃了。我们把“识别、推荐、导出清单”和“确认摄入”分开，只有用户确认已经吃了才写入长期数据库，这样营养统计才可信。

### 问：偏好数据库有什么用？

答：

> 用户吃完后可以评分并写原因，LLM 会把“喜欢清淡少油、高蛋白”“不喜欢油腻”等反馈解析成结构化记忆，写入 `preference_memories`。下一次推荐时，推荐引擎会读取 liked 和 avoid 信号，对菜谱加权或降权。

## 4. 画图资产清单

建议准备 4 类图，放进可编辑 PPT：

1. 首页 UI 英雄图：体现产品质感。
2. baseline 对比图：孤立工具 vs ByteSavor 全链路。
3. B-Y-T-E 架构闭环图：最重要，答辩时重点讲。
4. 测试与规模仪表盘图：回应软件工程评分标准。

图片风格统一要求：

```text
Use refined ByteSavor visual identity: deep green, fresh mint, warm amber, off-white background, subtle glassmorphism, high contrast readable black Chinese text, clean dashboard UI, professional university defense presentation, 16:9, no childish cartoon style, no over-bright white empty background.
```

## 5. 演示兜底

如果 VLM/LLM 现场慢：

- 先展示 `demo_tests/` 中准备好的图片。
- 切到已经跑通的页面截图或本地 H5。
- 用 Swagger 或 curl 展示核心接口返回。
- 强调后端测试已覆盖核心流程，现场模型延迟属于外部模型服务波动。

本次最新验证：

```text
pytest: tests/test_auth.py tests/test_meals_inventory.py tests/test_feedback_memory.py tests/test_food_guide.py tests/test_decision.py
结果: 15 passed

前端构建:
bsapp npm run build:h5: DONE Build complete
嵌套 uniapp npm run build:h5: DONE Build complete
```
