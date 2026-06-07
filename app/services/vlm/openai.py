import json
import logging
import httpx
from app.core.config import settings
from app.services.vlm.base import BaseVLMProvider

logger = logging.getLogger("vlm")


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
            async with httpx.AsyncClient(timeout=120) as client:
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
                        "max_tokens": 300,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("vlm_http status=%d body=%s", resp.status_code, resp.text[:300])
                    return None
                result = _parse(resp.json())
                n = len(result.get("ingredients", []))
                logger.info("vlm_ok ingredients=%d", n)
                return result
        except Exception as e:
            logger.warning("vlm_exception %s: %s", type(e).__name__, str(e)[:200])
            return None


def _parse(data: dict) -> dict:
    try:
        content = data["choices"][0]["message"]["content"].strip()
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
        # 校验
        if "ingredients" not in parsed:
            parsed["ingredients"] = []
        if "portion_estimation" not in parsed:
            parsed["portion_estimation"] = {"total_weight": 0}
        return parsed
    except Exception:
        logger.info("vlm_parse_failed raw=%s", str(data.get("choices", [{}])[0].get("message", {}).get("content", ""))[:200])
        return {"ingredients": [], "portion_estimation": {"total_weight": 0}}
