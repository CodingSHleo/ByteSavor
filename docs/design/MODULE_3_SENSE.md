# 模块三：感知层 (B-Sense) 实现思路

## 一、现状

| 方法 | 路径 | 当前行为 |
|------|------|---------|
| POST | `/v1/sense/analyze` | Mock 返回西兰花+牛肉 |

```python
# 现在的代码
return SuccessResponse(data={
    "ingredients": [
        {"name": "西兰花", "confidence": 0.98, "freshness": "high", "state": "新鲜"},
        {"name": "牛肉", "confidence": 0.95, "freshness": "normal", "state": "冷藏"}
    ],
    "portion_estimation": {"total_weight": 320}
})
```

## 二、目标

接收图片 URL → 调 VLM 识别食材 → 解析 VLM 返回 → 返回结构化食材列表。

如果 VLM 不可用（没配 API key 或网络不通），降级返回 Mock 数据，保证接口不炸。

## 三、调用链

```
POST /v1/sense/analyze { task_id, image_url, context }
  │
  ├─ 1. 校验 image_url 非空
  ├─ 2. 调 VLM service: vlm.analyze_food(image_url)
  │     │
  │     ├─ VLM 可用 → 发 HTTP 请求 → 拿回 JSON
  │     └─ VLM 不可用 → 返回 None → 降级 Mock
  ├─ 3. 解析 VLM 返回的食材列表
  └─ 4. 返回 Ingredient[] + portion_estimation
```

## 四、新增文件

```
app/services/vlm.py      # VLM 调用封装（发 HTTP → 解析 → 返回）
```

## 五、修改文件

```
app/routers/sense.py     # Mock → 调 vlm service
```

## 六、vlm.py 设计

```python
# app/services/vlm.py

import httpx
from app.core.config import settings

async def analyze_food(image_url: str) -> dict | None:
    """
    调 VLM 识别图片中的食材。
    成功返回: {"ingredients": [...], "portion_estimation": {...}}
    VLM 不可用返回 None，上层降级 Mock。
    """
    if not settings.vlm_api_url:
        return None  # 没配 VLM，降级

    prompt = """请识别图片中的所有食材。返回 JSON 格式：
{
  "ingredients": [
    {"name": "食材名", "confidence": 0.95, "freshness": "high/medium/low", "state": "新鲜/冷藏/冷冻"}
  ],
  "portion_estimation": {"total_weight": 估计总克数}
}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                settings.vlm_api_url,
                headers={"Authorization": f"Bearer {settings.vlm_api_key}"},
                json={
                    "model": "qwen-vl",
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt}
                    ]}]
                }
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            # 从 VLM 返回中提取 JSON
            return _parse_vlm_response(data)
    except Exception:
        return None


def _parse_vlm_response(data: dict) -> dict:
    """从 VLM 的返回体中提取食材 JSON"""
    try:
        content = data["choices"][0]["message"]["content"]
        # VLM 返回可能是纯 JSON 或含 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        import json
        return json.loads(content)
    except Exception:
        # 解析失败，返回空结果让上层降级
        return {"ingredients": [], "portion_estimation": {"total_weight": 0}}
```

## 七、routers/sense.py 改造

```python
# 原来
return SuccessResponse(data={...mock...})

# 改成
@router.post("/v1/sense/analyze")
async def analyze_ingredients(req: SenseRequest):
    if not req.image_url:
        return ErrorResponse(error={"code":"NO_IMAGE","message":"缺少图片URL"})

    # 调 VLM
    result = await vlm.analyze_food(req.image_url)

    if result is None:
        # VLM 不可用，降级 Mock
        result = {mock 数据}

    return SuccessResponse(data=result)
```

## 八、降级策略

VLM 不可用的情况：
- `.env` 里没配 `VLM_API_URL`
- VLM 服务返回非 200
- 网络超时
- VLM 返回的内容解析失败

以上任一情况 → 返回 Mock 数据 + 打印 warning 日志。这样：
- 开发阶段没配 VLM 也能跑通全链路
- 真实环境 VLM 恢复后自动生效
- 不会因为 VLM 挂了让整个接口 500

## 九、依赖

- 模块一（config 里有 vlm_api_url / vlm_api_key）
- 不需要用户登录（Sense 是公开接口）

## 十、不在本模块做的

- 图片上传到 OSS（前端直传 OSS，后端只收 URL）
- 视觉校验二次确认（后续模块）
- 食材识别结果持久化

---

## 十一、实现状态（2026-05-25）✅ 已完成

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/services/vlm.py` | VLM 调用封装。`analyze_food(url)` 发 HTTP 请求给 VLM，解析返回的 JSON。VLM 不可用时返回 None，上层降级 Mock |

### 修改文件

| 文件 | 说明 |
|------|------|
| `app/routers/sense.py` | Mock → 调 vlm service。VLM 不可用自动降级 Mock |

### 同时修复的问题

- 所有 router 的 `response_model=SuccessResponse` 移除
- **VLM provider 抽象化**：审查意见指出 provider 被写死为 OpenAI 格式，已重构为：
  ```
  app/services/vlm/
  ├── __init__.py   # 对外接口，创建默认 provider
  ├── base.py       # BaseVLMProvider 抽象类
  ├── openai.py     # OpenAICompatProvider（Qwen-VL/GPT-4V/InternVL 通用）
  └── prompts.py    # 不同场景的 prompt 模板
  ```
  换模型只需新增一个 provider 子类，router 一行不用改
- **Prompt 解耦**：prompt 抽到 `prompts.py`，不同场景（食材识别/菜品理解/场景分析）各有独立模板

### 验证结果

```
Sense（有 image_url, VLM未配） → success, 降级 Mock: [西兰花, 牛肉] ✅
Sense（缺 image_url）          → error, code: NO_IMAGE ✅
```

### 如何接入真实 VLM

修改 `.env`：
```
VLM_API_URL=https://your-vlm-endpoint/v1/chat/completions
VLM_API_KEY=sk-xxx
```
重启服务，`/v1/sense/analyze` 自动走真实 VLM 推理。
