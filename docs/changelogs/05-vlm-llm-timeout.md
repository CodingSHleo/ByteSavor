# 修改文档 05：VLM/LLM 超时收紧

## 修改日期

2026-06-19

## 修改目标

对应方案文档 Section 4 P1.6（VLM/LLM 超时收紧）。防止演示时因外部模型响应慢导致长时间白屏。

## 文件变更

### 1. 修改 `app/core/config.py`

**修改位置**：第 23-32 行

**修改前**：
```python
# VLM
vlm_api_url: str = ""
vlm_api_key: str = ""
vlm_model: str = "qwen3.5-27b-mlx"

# LLM
llm_api_url: str = ""
llm_api_key: str = ""
llm_model: str = "qwen3.5-27b-mlx"
```

**修改后**：新增超时配置字段
```python
# VLM
vlm_api_url: str = ""
vlm_api_key: str = ""
vlm_model: str = "qwen3.5-27b-mlx"
vlm_timeout_sec: int = 20  # 演示用 20s，失败走降级

# LLM
llm_api_url: str = ""
llm_api_key: str = ""
llm_model: str = "qwen3.5-27b-mlx"
llm_timeout_sec: int = 15  # LLM 推理超时
```

### 2. 修改 `app/services/vlm/openai.py`

**修改位置**：第 29 行

**修改前**：
```python
async with httpx.AsyncClient(timeout=120) as client:
```

**修改后**：
```python
async with httpx.AsyncClient(timeout=settings.vlm_timeout_sec) as client:
```

**效果**：VLM 超时从 120 秒降至 20 秒（可通过 `.env` 中的 `VLM_TIMEOUT_SEC` 覆盖）。

### 3. 修改 `app/services/feedback.py`

**修改位置**：第 145 行

**修改前**：
```python
async with httpx.AsyncClient(timeout=60) as client:
```

**修改后**：
```python
async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
```

**效果**：LLM 偏好解析超时从 60 秒降至 15 秒。

### 降级行为

| 组件 | 超时 | 降级策略 |
|------|------|---------|
| VLM (sense) | 20s | 抛 RuntimeError("VLM_UNAVAILABLE")，Agent 记录 error 事件，Evaluator 标记 PARTIAL |
| VLM (nutrition/quality/guide) | 20s | 同 VLM，返回 None |
| LLM (feedback parse) | 15s | 静默返回 {}，fallback 到 `_local_parse_preference` |
