import json
import logging
import httpx
from app.core.config import settings
from app.services.vlm.base import BaseVLMProvider

logger = logging.getLogger("vlm")


class VLMProviderError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class OpenAICompatProvider(BaseVLMProvider):
    def __init__(self, model: str = "qwen-vl"):
        self.model = model

    async def analyze_food(self, image_url: str, prompt: str) -> dict | None:
        if not settings.vlm_api_url:
            logger.warning("vlm_skip: no API URL configured")
            return None

        # 图片格式：HTTP URL 直接传，base64 data URL 直接传
        img_src = image_url
        is_data = image_url.startswith("data:")
        is_http = image_url.startswith("http://") or image_url.startswith("https://")
        logger.info("vlm_request model=%s host=%s img_type=%s img_len=%d",
                    self.model, settings.vlm_api_url.split("/")[2],
                    "data_url" if is_data else "http_url" if is_http else "other",
                    len(image_url))

        try:
            async with httpx.AsyncClient(timeout=settings.vlm_timeout_sec) as client:
                resp = await client.post(
                    settings.vlm_api_url,
                    headers={"Authorization": f"Bearer {settings.vlm_api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": img_src}},
                                {"type": "text", "text": prompt},
                            ],
                        }],
                        "max_tokens": 700,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("vlm_http status=%d body=%s", resp.status_code, resp.text[:300])
                    raise VLMProviderError("VLM_HTTP_ERROR", f"视觉模型接口返回异常：{resp.status_code}")
                result = _parse(resp.json())
                n = len(result.get("ingredients", []))
                logger.info("vlm_ok ingredients=%d", n)
                return result
        except httpx.ReadTimeout as e:
            logger.warning("vlm_timeout timeout_sec=%s", settings.vlm_timeout_sec)
            raise VLMProviderError("VLM_TIMEOUT", "视觉模型响应超时，请稍后重试或换一张更清晰的图片") from e
        except VLMProviderError:
            raise
        except Exception as e:
            logger.warning("vlm_exception %s: %s", type(e).__name__, str(e)[:200])
            raise VLMProviderError("VLM_UNAVAILABLE", "视觉模型暂时不可用，请稍后重试") from e


def _parse(data: dict) -> dict:
    choice = data["choices"][0]
    finish = choice.get("finish_reason", "unknown")
    content = choice["message"]["content"].strip()
    content_len = len(content)

    try:
        # 1. Markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        # 2. 文本中嵌 JSON
        elif "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]

        parsed = json.loads(content)
        if "ingredients" not in parsed:
            parsed["ingredients"] = []
        if "portion_estimation" not in parsed:
            parsed["portion_estimation"] = {"total_weight": 0}

        if finish == "length":
            logger.warning("vlm_truncated finish_reason=length content_len=%d", content_len)
        return parsed
    except Exception:
        logger.warning("vlm_parse_failed finish_reason=%s content_len=%d content_head=%s",
                       finish, content_len, content[:150])
        return {"ingredients": [], "portion_estimation": {"total_weight": 0}}
