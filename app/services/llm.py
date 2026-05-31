import json
import httpx
from app.core.config import settings


async def parse_intent(user_input: str) -> dict:
    """用 LLM 解析自然语言意图 → 结构化 JSON"""
    if not settings.llm_api_url:
        return None

    prompt = f"""分析用户饮食需求，返回 JSON（不要多余文字）：
{{
  "goal": "fat_loss/muscle_gain/balanced",
  "time_limit": 整数分钟,
  "taste": "spicy/light/空字符串",
  "ingredients": ["食材1", "食材2"]
}}

用户输入: {user_input}"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                settings.llm_api_url,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0,
                },
            )
            if resp.status_code != 200:
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1].split("```")[0]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
    except Exception:
        return None
