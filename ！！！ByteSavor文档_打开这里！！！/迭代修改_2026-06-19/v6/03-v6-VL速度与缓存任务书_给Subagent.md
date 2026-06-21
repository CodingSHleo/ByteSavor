# ByteSavor v6-03：VL 速度与缓存任务书（给 Subagent）

日期：2026-06-21  
执行对象：subagent  
审查人：主 agent / 项目负责人  
前置依赖：建议先完成 v6-01 Skill 工业化底座  

---

## 0. 本任务目标

优化千问 VL 感知链路的真实速度和用户感知速度，但不引入本地 CNN/ONNX 降级。

完成后必须能准确答辩：

> ByteSavor 的感知层通过前端压缩、后端指纹缓存、模型/prompt 版本化 cache key 和阶段化事件，把 VLM 这个慢外部依赖包进可观测、可复用、可解释的工程链路里。

---

## 1. 当前问题

当前代码证据：

| 文件 | 当前状态 | 问题 |
|---|---|---|
| `app/services/vlm/__init__.py` | `cache_key = make_key("vlm", _image_hash(image_url))` | cache key 没有模型和 prompt 版本，prompt 改了仍可能命中旧结果 |
| `app/services/vlm/__init__.py` | 返回 `cache_hit` | 缺少 `latency_ms/model/cache_key/image_fingerprint/prompt_version` |
| `bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue` | H5 压缩 maxW=800 quality=0.7 | 可进一步压到 720/0.68，且缺少压缩前后状态 |
| `app/routers/sense.py` | 返回 VLM 结果 | 缺少统一可观测字段透出测试 |

---

## 2. 严禁事项

1. 不允许新增本地 CNN/ONNX 降级模型。
2. 不允许把 VLM 未配置伪装成成功识别。
3. 不允许缓存包含用户隐私的原始图片内容。
4. 不允许把完整 base64 写入日志。
5. 不允许只做前端假进度，不做后端 cache key 修正。

---

## 3. 必改文件

| 文件 | 操作 | 要求 |
|---|---|---|
| `app/services/vlm/__init__.py` | 修改 | cache key 加模型/prompt_version，结果加观测字段 |
| `app/services/vlm/prompts.py` | 修改 | 增加 `FOOD_ANALYSIS_PROMPT_VERSION` |
| `app/routers/sense.py` | 修改或确认 | 透出观测字段 |
| `bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue` | 修改 | 压缩参数与阶段状态 |
| `tests/test_sense.py` | 新增或修改 | VLM cache 和观测字段测试 |
| `tests/test_vlm_cache.py` | 可新增 | 纯 service cache 测试 |

---

## 4. 后端实现要求

### 4.1 prompt version

在 `app/services/vlm/prompts.py` 增加：

```python
FOOD_ANALYSIS_PROMPT_VERSION = "food-analysis-v1"
```

后续 prompt 改动时只改这个 version，即可避免旧缓存污染新 prompt。

### 4.2 cache key

当前：

```python
cache_key = make_key("vlm", _image_hash(image_url))
```

改为：

```python
fingerprint = _image_hash(image_url)
cache_key = make_key("vlm", settings.vlm_model, FOOD_ANALYSIS_PROMPT_VERSION, fingerprint)
```

要求：

1. `image_fingerprint` 只能是 hash，不允许返回原图。
2. `cache_key` 可以返回给前端用于调试，但不能包含 base64。
3. cache 命中时也必须返回完整观测字段。

### 4.3 result 观测字段

`analyze_food()` 返回必须包含：

```python
{
  "cache_hit": False,
  "cache_key": "...",
  "latency_ms": 1234,
  "model": settings.vlm_model,
  "prompt_version": FOOD_ANALYSIS_PROMPT_VERSION,
  "image_fingerprint": "..."
}
```

缓存命中时：

```python
"cache_hit": True
"latency_ms": 本次 cache 读取耗时
```

注意：缓存中可以保存模型首次调用的结果，但每次返回的 `latency_ms/cache_hit` 要反映本次请求。

### 4.4 日志要求

日志只允许：

```text
vlm_cache_hit key=... model=... prompt_version=...
vlm_analyze_done cache_hit=false latency_ms=...
```

不允许打印图片 base64。

---

## 5. 前端实现要求

文件：`bsapp/src/pages/ingredient-recognition/ingredient-recognition.vue`

### 5.1 压缩参数

H5 `compressImage`：

```javascript
const maxW = 720
callback(canvas.toDataURL('image/jpeg', 0.68))
```

如果图片小于 720，不要放大。

### 5.2 阶段状态

识别过程至少展示这些状态：

1. `正在压缩图片...`
2. `图片已压缩，准备调用视觉模型...`
3. `VLM 多模态模型推理中...`
4. cache 命中时显示：`命中缓存，已快速识别`
5. 完成时显示：`识别完成，请确认 X 种食材`

如果 API 返回了 `latency_ms`，完成状态或调试字段中保留。

---

## 6. 必须新增测试

### 6.1 VLM cache 测试

可以通过 monkeypatch provider 实现：

1. 第一次调用 `cache_hit=False`。
2. 第二次同图同模型同 prompt_version `cache_hit=True`。
3. 换 `settings.vlm_model` 或 prompt_version 后 cache key 不同。
4. 返回包含 `latency_ms/model/prompt_version/image_fingerprint/cache_key`。

### 6.2 Sense API 测试

1. `/v1/sense/analyze` 成功返回观测字段。
2. 图片过大仍返回 `IMAGE_TOO_LARGE`。
3. VLM 返回 None 仍返回 `VLM_UNAVAILABLE`。

---

## 7. 验证命令

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_sense.py \
  tests/test_vlm_cache.py
```

Agent 感知路径回归：

```bash
JWT_SECRET=test-review-secret venv/bin/python -m pytest -q \
  tests/test_agent.py \
  tests/test_agent_runtime.py \
  tests/test_agent_loop_engineering.py
```

前端：

```bash
node scripts/verify_frontend_regressions.mjs
cd bsapp
npm run build:h5
```

---

## 8. 修复记录要求

完成后新增：

- `docs/迭代修改/44-v6-VL速度与缓存修复记录.md`
- `！！！ByteSavor文档_打开这里！！！/迭代修改_2026-06-19/44-v6-VL速度与缓存修复记录.md`

必须写清：

1. cache key 组成。
2. 为什么不做本地 CNN 降级。
3. 前端压缩参数。
4. cache hit/miss 测试结果。
5. 剩余风险：真实 VLM 网络耗时仍取决于外部 API。

