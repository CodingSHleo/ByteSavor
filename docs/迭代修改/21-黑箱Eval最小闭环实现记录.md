# 修改文档 21：离线黑箱 Eval 最小闭环

## 日期
2026-06-20

## 修改目标
对应 v3 复审文档 Section 6.2：先跑通最小 Eval 闭环，不接 LLM Judge。

## 新增文件

### `evals/cases/quick.jsonl` — 10 条黄金用例
| ID | 场景 | 检查项 |
|----|------|--------|
| Q01 | 牛肉南瓜减脂 | 有推荐、reply 非空、evaluation、termination_reason、覆盖 ≥1 个核心食材 |
| Q02 | 无约束探索 | 同上（无食材覆盖率要求） |
| Q03 | 多食材 3 个 | 覆盖 ≥2 个核心食材、四个 phase 齐全 |
| Q04 | 缺图片澄清 | status=needs_input、ask_user event、NEEDS_INPUT |
| Q05 | 购物清单 | 有 evaluation、termination_reason、events 非空 |
| Q06 | 清淡口味 | 基本推荐检查 |
| Q07 | 时间约束 15min | 基本推荐检查 |
| Q08 | 增肌目标 | 基本推荐检查 |
| Q09 | 空输入 | 有 evaluation、termination_reason |
| Q10 | 多轮对话 | 有 evaluation、termination_reason |

### `evals/scorer.py` — 确定性规则 scorer
- 不调用 LLM
- 支持 15 种检查类型：has_recipes、recipes_non_empty、reply_not_empty、has_evaluation、has_termination_reason、core_ingredient_coverage_min_1/2、status、has_ask_user_event、has_phase_*、events_non_empty
- 输出：{case_id, total_score, max_score, passed_checks, failed_checks, details}

### `evals/runner.py` — Eval runner
用法：`python evals/runner.py --quick`
- 加载 JSONL 用例
- 用 LangGraphAgent + mock 工具执行
- 调用 scorer 打分
- 输出 `evals/reports/latest.json` + `evals/reports/latest.md`

## 验收
```bash
JWT_SECRET=test-review-secret venv/bin/python evals/runner.py --quick
```
结果：10/10 用例完成，42/42 checks 通过（100%），耗时 0.05s。

## 后续扩展
- 替换 mock 工具为真实服务
- 增加 30-50 条完整用例
- 接入 LLM Judge 做软评估
- 接入 CI 自动运行
