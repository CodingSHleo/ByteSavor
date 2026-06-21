from __future__ import annotations

import json
import logging
from dataclasses import replace

import httpx

from app.agent.planner import AgentAction, build_candidate_actions, plan_next_action
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger("agent_llm_planner")


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


async def choose_action_with_llm(
    state: AgentState,
    candidates: list[dict],
) -> dict | None:
    if not settings.agent_llm_planner_enabled:
        return None
    if not settings.llm_api_key or not settings.llm_api_url:
        return None
    if not candidates:
        return None

    allowed_tools = {str(candidate.get("tool")) for candidate in candidates if candidate.get("tool")}
    prompt = f"""你是 ByteSavor Agent 的受控 Planner。

硬规则：
1. 只能从候选动作中选择 selected_tool，禁止发明工具。
2. 禁止生成 recipe_id，菜谱必须由 decision 工具通过数据库召回。
3. 只返回 JSON：{{"selected_tool":"候选工具名","reason":"选择理由"}}。

用户输入：{state["user_input"]}
已完成工具：{state["completed_tools"]}
候选动作：{json.dumps(candidates, ensure_ascii=False)}
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
                    "max_tokens": 200,
                },
            )
        if response.status_code != 200:
            logger.warning("agent_llm_planner_http status=%s body=%s", response.status_code, response.text[:200])
            return None
        content = response.json()["choices"][0]["message"]["content"]
        data = _extract_json(str(content))
        if not data:
            return None
        selected = str(data.get("selected_tool") or "")
        if selected not in allowed_tools:
            logger.warning("agent_llm_planner_unauthorized_tool selected=%s allowed=%s", selected, sorted(allowed_tools))
            return None
        return {
            "kind": "tool",
            "tool": selected,
            "reason": str(data.get("reason") or ""),
        }
    except Exception as exc:
        logger.warning("agent_llm_planner_failed %s", exc)
        return None


async def select_next_action(state: AgentState, skill_descriptors: list[dict]) -> AgentAction:
    candidates = build_candidate_actions(state, skill_descriptors)
    candidate_tools = [str(candidate["tool"]) for candidate in candidates if candidate.get("tool")]
    base_rule_action = plan_next_action(state)
    rule_action = replace(base_rule_action, candidate_tools=candidate_tools)

    if not candidates:
        return replace(rule_action, planner_source="rule")

    llm_action = await choose_action_with_llm(state, candidates)
    if not llm_action:
        source = "rule_fallback" if settings.agent_llm_planner_enabled else "rule"
        return replace(rule_action, planner_source=source)
    selected_tool = str(llm_action.get("tool") or "")
    if selected_tool not in set(candidate_tools):
        logger.warning("agent_llm_planner_unauthorized_tool selected=%s allowed=%s", selected_tool, candidate_tools)
        return replace(rule_action, planner_source="rule_fallback")

    return AgentAction(
        kind="tool",
        tool=selected_tool,
        reason=str(llm_action.get("reason") or "LLM selected candidate tool"),
        planner_source="llm",
        candidate_tools=candidate_tools,
        llm_reason=str(llm_action.get("reason") or ""),
    )
