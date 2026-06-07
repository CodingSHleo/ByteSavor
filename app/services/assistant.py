"""AI 美食助手 — DeepSeek 驱动的做饭建议/食材搭配/营养咨询"""

import logging
import httpx

logger = logging.getLogger("assistant")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """你是 ByteSavor 的 AI 美食顾问，叫「小味」。像一位经验丰富的家庭厨师。

## 核心规则
- 消息里带了「用户现有食材」时，立刻根据这些食材给出 2-3 道菜谱建议+简要做法。不要自我介绍，直接说菜。
- 消息里没有食材时，正常回答饮食相关问题。
- 每条约 150 字，短小实用。用中文。

## 你能做的
- 根据手头食材推荐菜谱+做法
- 分析食材搭配（"牛肉配南瓜秋冬温补"）
- 营养知识（热量/蛋白质/碳水）
- 根据减脂/增肌/均衡目标调整建议
- 烹饪技巧（火候/调味/刀工）

## 不能做的
- 别推荐用户没有的食材做主料
- 别编造精确营养数据
- 别回答和饮食无关的问题"""


def goal_text(goal: str) -> str:
    m = {"fat_loss": "我在减脂", "muscle_gain": "我在增肌", "balanced": ""}
    return m.get(goal, "")


def build_context(ingredients: list[str] = None, goal: str = "", preferences: list[str] = None) -> str:
    """根据用户画像构建上下文"""
    parts = []
    if ingredients:
        parts.append(f"用户现有食材：{'、'.join(ingredients)}")
    if goal:
        goal_map = {"fat_loss": "减脂", "muscle_gain": "增肌", "balanced": "均衡饮食"}
        parts.append(f"健康目标：{goal_map.get(goal, goal)}")
    if preferences:
        parts.append(f"口味偏好：{'、'.join(preferences)}")
    return "。".join(parts) + "。" if parts else ""


async def chat(
    user_message: str,
    api_key: str = "",
    history: list = None,
    ingredients: list[str] = None,
    goal: str = "",
    preferences: list[str] = None,
) -> dict:
    if not api_key or "sk-" not in api_key:
        return {"reply": "AI 助手暂未配置 API key，请在 .env 中设置 LLM_API_KEY=sk-your-deepseek-key", "source": "fallback"}

    context = build_context(ingredients, goal, preferences)
    if ingredients:
        g = f"，目标是{goal_text(goal)}" if goal else ""
        user_msg = f"【重要】直接推荐菜谱，不要自我介绍。我有：{'、'.join(ingredients)}{g}。用户问：{user_message}\n请给我具体的菜名和做法。"
    elif context:
        user_msg = f"{context}\n用户问：{user_message}"
    else:
        user_msg = user_message

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
            )
            if r.status_code != 200:
                logger.warning("assistant_http status=%s body=%s", r.status_code, r.text[:200])
                return {"reply": "AI 助手暂时不可用，请稍后重试", "source": "error"}
            reply = r.json()["choices"][0]["message"]["content"]
            logger.info("assistant_ok len=%d", len(reply))
            return {"reply": reply, "source": "deepseek"}
    except Exception as e:
        logger.warning("assistant_err %s", e)
        return {"reply": "网络异常，AI 助手响应超时", "source": "error"}
