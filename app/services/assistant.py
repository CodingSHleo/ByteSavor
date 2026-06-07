"""AI 美食助手 — 做饭建议、食材搭配、营养咨询"""
import json
import logging
import httpx

logger = logging.getLogger("assistant")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """你是 ByteSavor 的 AI 美食助手，专注饮食领域。你的能力：
1. 根据用户有的食材，给出烹饪建议和菜谱灵感
2. 回答食材搭配、营养知识、烹饪技巧问题
3. 根据用户的健康目标（减脂/增肌/均衡）给出饮食建议
4. 推荐适合的菜谱

回答风格：简洁实用，像一位经验丰富的厨师朋友。用中文回答，不超过 300 字。"""


async def chat(user_message: str, api_key: str = "", history: list = None) -> dict:
    """AI 助手对话"""
    if not api_key or "sk-" not in api_key:
        return {"reply": "AI 助手暂未配置 API key，请在 .env 中设置 LLM_API_KEY=sk-your-deepseek-key", "source": "fallback"}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])  # 最近 6 轮对话
    messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            )
            if r.status_code != 200:
                logger.warning("assistant_http_error status=%s", r.status_code)
                return {"reply": "AI 助手暂时不可用，请稍后重试", "source": "error"}
            content = r.json()["choices"][0]["message"]["content"]
            return {"reply": content, "source": "deepseek"}
    except Exception as e:
        logger.warning("assistant_exception %s", e)
        return {"reply": "网络异常，AI 助手响应超时", "source": "error"}
