"""
DeepSeek LLM 推理层 — Agent 的"大脑"
负责意图解析、规划、推理。VLM 只管看图，DeepSeek 管思考。
"""
import json, httpx
from app.core.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


async def parse_intent(user_input: str) -> dict | None:
    """用 DeepSeek 解析自然语言意图"""
    if not settings.llm_api_key or "sk-" not in str(settings.llm_api_key):
        return None

    prompt = f"""分析用户饮食需求，返回JSON（不要markdown）：
{{"goal":"fat_loss/muscle_gain/balanced","time_limit":分钟,"taste":"spicy/light/''","ingredients":["食材"]}}

用户: {user_input}"""

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150, "temperature": 0
                }
            )
            if r.status_code != 200:
                return None
            content = r.json()["choices"][0]["message"]["content"].strip()
            if "```" in content:
                content = content.split("```")[1].split("```")[0]
                if content.startswith("json"): content = content[4:]
            return json.loads(content)
    except Exception:
        return None
