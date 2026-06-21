from __future__ import annotations

import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("llm_rerank")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


async def rerank_recipe_candidates(
    *,
    user_ingredients: list[str],
    constraints: dict,
    candidates: list[dict],
) -> list[str]:
    """Use LLM only to rerank existing DB recipes; never allow new recipe IDs."""
    if not settings.llm_api_key or "sk-" not in str(settings.llm_api_key):
        return []
    if not candidates or not user_ingredients:
        return []

    candidate_payload = [
        {
            "recipe_id": c.get("recipe_id"),
            "title": c.get("title"),
            "ingredients": [i.get("name", "") for i in (c.get("ingredients") or []) if isinstance(i, dict)],
            "matched": c.get("_meta", {}).get("matched_ingredients", []),
            "missing_user_ingredients": c.get("_meta", {}).get("missing_ingredients", []),
            "purchase_suggestions": c.get("_meta", {}).get("purchase_suggestions", []),
        }
        for c in candidates[:12]
    ]
    allowed_ids = {str(c["recipe_id"]) for c in candidate_payload if c.get("recipe_id")}
    prompt = f"""你是 ByteSavor 菜谱重排裁判。只能从候选菜谱中选择和排序，禁止编造新菜。

硬规则：
1. 用户现有食材必须优先使用：{user_ingredients}
2. 首位菜谱应尽量覆盖更多现有食材；如果不能全部覆盖，优先覆盖更具体的食材。
3. 不要把只命中泛主料、却忽略关键食材的菜排在前面。
4. 缺少的配料只能作为 purchase_suggestions，不要当成用户已有食材。

约束：{constraints}
候选：{json.dumps(candidate_payload, ensure_ascii=False)}

只返回 JSON：
{{"recipe_ids":["候选ID1","候选ID2"]}}"""
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
            response = await client.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 300,
                },
            )
        if response.status_code != 200:
            logger.warning("llm_rerank_http status=%s body=%s", response.status_code, response.text[:200])
            return []
        content = response.json()["choices"][0]["message"]["content"].strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        ranked_ids = [str(x) for x in data.get("recipe_ids", []) if str(x) in allowed_ids]
        return ranked_ids
    except Exception as exc:
        logger.warning("llm_rerank_failed %s", exc)
        return []
