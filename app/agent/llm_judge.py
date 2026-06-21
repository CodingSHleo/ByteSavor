from __future__ import annotations

import json
import logging

import httpx

from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger("agent_llm_judge")


def _extract_json(content: str) -> dict | None:
    text = content.strip()
    if "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


async def judge_agent_result(state: AgentState) -> dict | None:
    if not settings.agent_llm_judge_enabled:
        return None
    if not settings.llm_api_key or not settings.llm_api_url:
        return None

    payload = {
        "user_input": state["user_input"],
        "ingredients": state["ingredients"],
        "preferences": state["preferences"],
        "recipes": [
            {
                "recipe_id": recipe.get("recipe_id"),
                "title": recipe.get("title"),
                "match_score": recipe.get("match_score"),
            }
            for recipe in state["recipes"][:8]
        ],
        "shopping_list": state["shopping_list"][:20],
        "errors": state["errors"],
    }
    prompt = f"""你是 ByteSavor Agent 的软性 Judge，只评价现有结果。

硬规则：
1. 只能评审 payload 中已经存在的结果，禁止新增菜谱、禁止新增 recipe_id。
2. 你的输出不阻断主流程，不改变 status 或 termination_reason。
3. 只返回 JSON：{{"verdict":"PASS或WARN","scores":{{"instruction_following":4.0,"ingredient_relevance":4.0,"preference_alignment":4.0,"actionability":4.0}},"issues":[],"suggestions":[]}}。

payload：{json.dumps(payload, ensure_ascii=False)}
"""
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
            response = await client.post(
                settings.llm_api_url,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model or "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 500,
                },
            )
        if response.status_code != 200:
            logger.warning("agent_llm_judge_http status=%s body=%s", response.status_code, response.text[:200])
            return None
        content = response.json()["choices"][0]["message"]["content"]
        data = _extract_json(str(content))
        if not data:
            return None
        verdict = data.get("verdict")
        if verdict not in {"PASS", "WARN"}:
            data["verdict"] = "WARN"
        return {
            "verdict": data["verdict"],
            "scores": data.get("scores") or {},
            "issues": data.get("issues") or [],
            "suggestions": data.get("suggestions") or [],
        }
    except Exception as exc:
        logger.warning("agent_llm_judge_failed %s", exc)
        return None
