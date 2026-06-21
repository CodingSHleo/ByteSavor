# 修改文档 06：图片识别 hash 缓存

## 修改日期

2026-06-19

## 修改目标

对应方案文档 Section 3.8（图片 hash 缓存）。对 image_url 或 base64 内容进行 md5 hash 缓存，避免重复图片多次调用 VLM。

## 文件变更

### 修改 `app/services/vlm/__init__.py`

**修改前**（原始版本）：
```python
async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    return await _provider.analyze_food(image_url, prompt)
```

**修改后**：新增缓存层

```python
import hashlib
from app.core.cache import get as cache_get, set as cache_set, make_key

IMAGE_CACHE_TTL = 1800  # 30 分钟

def _image_hash(image_url: str) -> str:
    return hashlib.md5(image_url.encode("utf-8")).hexdigest()[:16]

async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    # 1. 检查缓存
    cache_key = make_key("vlm", _image_hash(image_url))
    cached = await cache_get(cache_key)
    if cached:
        cached["cache_hit"] = True
        return cached

    # 2. 调用 VLM
    raw = await _provider.analyze_food(image_url, prompt)
    if raw is None:
        return None

    # 3. 后处理（同义词标准化 + 置信度分级）
    ...

    # 4. 写入缓存
    result = {"ingredients": ..., "cache_hit": False}
    await cache_set(cache_key, result, ttl=IMAGE_CACHE_TTL)
    return result
```

**效果**：
- 同一张图片在 30 分钟内重复识别直接返回缓存结果
- cache_key 格式：`bs:<md5(vlm|image_hash)>`
- 命中时 `cache_hit: true`，前端可展示"命中缓存"
- 依赖已有 Redis，不需要新增依赖
