# ByteSavor v5 继续复核：Eval API 与社区冒烟

日期：2026-06-21  
复核对象：`31-v5复审修复记录.md` 中剩余事项  
结论：Eval API 已在当前后端进程上验证通过；社区账号/发帖/点赞/评论/删除已通过真实 API 冒烟。浏览器插件本轮不可用，未完成浏览器级截图验收。

---

## 1. 服务状态

后端：

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

结果：

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

前端：

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run dev:h5
```

结果：

```text
Local: http://localhost:5175/
```

说明：`5173/5174` 已被占用，Vite 自动切到 `5175`。

---

## 2. Eval API 验证

普通沙箱直接访问 `127.0.0.1:8000` 时失败，原因是本机网络访问被沙箱限制：

```text
curl exit 7
```

使用允许访问 localhost 的环境重跑：

```bash
API_BASE=http://127.0.0.1:8000 ./scripts/verify_eval_api.sh
```

结果：

```text
API probe passed
Loaded 10 cases from evals/cases/quick.jsonl (mode=api)
Score: 72/72 (100%)
Eval API verification passed
```

结论：

- 当前 8000 后端是新代码。
- `/v1/agent/execute` 返回了 `events.phase` 和 `termination_reason`。
- quick Eval API 模式通过。

边界：

- 仍是 10 条 quick 用例，不等于 30-50 条完整黄金 Eval 集。

---

## 3. 前端服务可达性

命令：

```bash
curl -s http://127.0.0.1:5175/ | head -20
```

结果包含：

```html
<title>ByteSavor</title>
<div id="app"></div>
<script type="module" src="/src/main.js"></script>
```

结论：

- H5 dev server 正常响应。
- 前端入口页可达。

---

## 4. 社区真实 API 冒烟

由于本轮 Browser 插件返回：

```text
Browser is not available: iab
```

且本地 Playwright CLI 尝试未在合理时间内返回，本轮改用真实 API 冒烟验证业务闭环，不把它冒充为浏览器截图验收。

冒烟流程：

1. 密码注册新用户。
2. 密码登录获取 token。
3. 创建 recipe 社区帖。
4. 分页查询社区 recipe 列表。
5. 校验新帖子出现在列表且带结构化食材。
6. 点赞帖子。
7. 详情查询校验 `liked_by_me=true` 且 `like_count>=1`。
8. 发表评论。
9. 详情查询校验评论存在。
10. 取消点赞。
11. 详情查询校验 `liked_by_me=false` 且 `like_count=0`。
12. 作者删除帖子。

命令摘要：

```bash
node - <<'NODE'
# fetch http://127.0.0.1:8000
# register -> login -> create post -> list -> like -> detail -> comment -> unlike -> delete
NODE
```

结果：

```json
{
  "username": "smoke_mqmlc5fa",
  "postId": 42,
  "list_has_more": true,
  "ok": true
}
```

结论：

- 账号密码链路可用。
- 社区 recipe 发帖可用。
- 分页列表可用。
- `liked_by_me` 可用。
- 评论可用。
- 取消点赞可用。
- 作者删除可用。

---

## 5. 本轮未完成的浏览器级检查

未完成项：

- 没有浏览器截图。
- 没有真实点击 `.vue` 页面控件。
- 没有控制台 error/warn 采集。
- 没有移动视口截图。

原因：

- Browser 插件不可用：`Browser is not available: iab`。
- 本地 Playwright CLI 通过 skill wrapper 启动后长时间无输出，未继续依赖该路径。

后续如果要做 UI 终验，建议单独执行：

1. 打开 `http://localhost:5175/`。
2. 注册一个密码账号。
3. 进入社区页。
4. 发布 recipe 帖。
5. 检查列表是否显示食材摘要。
6. 进入详情。
7. 点赞、取消赞、评论。
8. 作者删除。
9. 同时观察浏览器 console。

---

## 6. 当前最新验证基线

| 项目 | 结果 |
|---|---:|
| 核心非 DB 测试 | `84 passed, 1 skipped` |
| 完整 DB 验证 | `39 passed` |
| Eval mock quick | `72/72 (100%)` |
| Eval API quick | `72/72 (100%)` |
| H5 build | `DONE Build complete` |
| H5 dev server | `http://localhost:5175/` 可达 |
| 社区 API 冒烟 | `ok: true` |

---

## 7. 下一步建议

1. 不再让 subagent 修改 v5 基础工程和账号社区，除非出现新 bug。
2. 下一轮如果继续推进，优先做浏览器级 UI 终验，而不是继续堆后端测试。
3. 完整黑箱 Eval 仍需要扩展到 30-50 条黄金用例。
4. Alembic 正式迁移仍未接入，当前 `ensure_*` 只能作为课程/演示期折中。
