import base64
import json
import httpx
from app.core.config import settings
from app.services.vlm.base import BaseVLMProvider


class OpenAICompatProvider(BaseVLMProvider):
    def __init__(self, model: str = "qwen-vl"):
        self.model = model

    async def analyze_food(self, image_url: str, prompt: str) -> dict | None:
        if not settings.vlm_api_url:
            return None

        img_src = image_url
        if image_url.startswith("http://") or image_url.startswith("https://"):
            b64 = await _download_as_base64(image_url)
            if b64:
                img_src = b64

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    settings.vlm_api_url,
                    headers={"Authorization": f"Bearer {settings.vlm_api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": img_src}},
                                    {"type": "text", "text": prompt},
                                ],
                            }
                        ],
                    },
                )
                if resp.status_code != 200:
                    return None
                return _parse(resp.json())
        except Exception:
            return None


def _parse(data: dict) -> dict:
    try:
        content = data["choices"][0]["message"]["content"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception:
        return {"ingredients": [], "portion_estimation": {"total_weight": 0}}


async def _download_as_base64(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            ct = resp.headers.get("content-type", "image/jpeg")
            b64 = base64.b64encode(resp.content).decode()
            return f"data:{ct};base64,{b64}"
    except Exception:
        return None
